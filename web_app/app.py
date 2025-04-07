import os
import json
import time
import hmac
import hashlib
import requests
from ipaddress import ip_address
from flask import Flask, render_template, request, jsonify, make_response
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sms_alert import send_sms
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config["SERVER_NAME"] = "monitoring.opicluster.online"

# Rate limiting global
limiter = Limiter(get_remote_address, app=app, default_limits=["5 per second", "30 per minute"])

PROMETHEUS_URL = "http://prometheus:9090/api/v1/query"
ALERTMANAGER_URL = "http://alertmanager:9093/api/v2/alerts"

@app.after_request
def secure_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.before_request
def block_options():
    if request.method == 'OPTIONS' and not request.path.startswith("/api"):
        return make_response("Method Not Allowed", 405)

def is_internal_request(ip):
    try:
        ip_obj = ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except Exception:
        return False

def country_to_flag(cc):
    if not cc or len(cc) != 2:
        return "❓"
    return chr(127397 + ord(cc[0].upper())) + chr(127397 + ord(cc[1].upper()))

@app.route('/ip_threats')
def ip_threats():
    data_file = "/home/foxink/opicluster_monitoring/data/suspicious_ips.json"
    try:
        with open(data_file, 'r') as f:
            ip_data = json.load(f)
    except Exception as e:
        return f"<pre>Erreur : {str(e)}</pre>", 500

    for ip in ip_data:
        ip["Flag"] = country_to_flag(ip.get("CountryCode", "XX"))

    ip_data.sort(key=lambda x: x.get("Score", 0), reverse=True)
    return render_template("ip_threats.html", ips=ip_data)

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@app.route('/')
def index():
    data = get_cluster_data()
    return render_template('index.html', **data)

@app.route('/alerts')
def alerts():
    alerts_data = get_alerts()
    return render_template('alerts.html', alerts=alerts_data, api_token=os.environ.get("API_SECRET_TOKEN"))

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/status')
def api_status():
    return jsonify(get_cluster_metrics())

@app.route('/sms_alert', methods=['POST'])
@limiter.limit("5 per second;30 per minute")
def sms_alert():
    raw_body = request.get_data()
    remote_ip = request.remote_addr

    # Auth locale fallback
    if is_internal_request(remote_ip):
        bearer = request.headers.get("Authorization", "")
        expected = f"Bearer {os.environ.get('API_SECRET_TOKEN', '')}"
        if bearer != expected:
            app.logger.warning(f"[SECURITY] Token refusé depuis IP interne {remote_ip}")
            return jsonify({"error": "Token invalide"}), 403
    else:
        # HMAC obligatoire
        signature = request.headers.get("X-Signature", "")
        api_key = os.environ.get("API_SECRET_KEY", "")
        expected_hmac = hmac.new(api_key.encode(), raw_body, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_hmac):
            app.logger.warning(f"[SECURITY] Signature HMAC refusée depuis {remote_ip}")
            return jsonify({"error": "Signature invalide"}), 403

    try:
        data = json.loads(raw_body)
        if data and "alerts" in data:
            for alert in data["alerts"]:
                status = alert.get("status", "firing")
                instance = alert['labels'].get('instance', 'unknown')
                summary = alert['annotations'].get('summary', 'Problème détecté')

                if status == "firing":
                    message = f"[ALERTE] {summary} sur {instance} (FIRING)"
                elif status == "resolved":
                    message = f"[RESOLU] {summary} sur {instance} (RESOLVED)"
                else:
                    message = f"[INCONNU] {summary} sur {instance} (status={status})"

                send_sms(message)
            return jsonify({'status': 'SMS envoyé'}), 200

    except Exception as e:
        app.logger.error(f"[ERROR] Erreur /sms_alert : {str(e)}")
        return jsonify({"error": "Erreur interne"}), 500

    return jsonify({"error": "Format invalide"}), 400

# Helpers Prometheus ----------------------------

def get_node_metrics():
    query = 'up{job="node"}'
    try:
        r = requests.get(PROMETHEUS_URL, params={'query': query})
        results = r.json()['data']['result']
        metrics = {}
        for result in results:
            instance = result['metric'].get('instance', 'unknown')
            custom_name = result['metric'].get('name', '')
            display_name = f"{instance} ({custom_name})" if custom_name else instance
            status = (result['value'][1] == '1')
            metrics[display_name] = {'status': status, 'instance': instance}
        return metrics
    except Exception as e:
        print("Erreur get_node_metrics:", e)
        return {}

def get_temperatures():
    query = 'node_thermal_zone_temp{type="cpu-thermal"}'
    temps = {}
    try:
        r = requests.get(PROMETHEUS_URL, params={'query': query})
        results = r.json()['data']['result']
        for result in results:
            instance = result['metric'].get('instance', 'unknown')
            custom_name = result['metric'].get('name', '')
            display_name = f"{instance} ({custom_name})" if custom_name else instance
            temperature = float(result['value'][1])
            if temperature > 100:
                temperature /= 1000.0
            temps[display_name] = temperature
            temps[instance] = temperature
        return temps
    except Exception as e:
        print("Erreur get_temperatures:", e)
        return {}

def get_load_5m():
    query = 'node_load5'
    loads = {}
    try:
        r = requests.get(PROMETHEUS_URL, params={'query': query})
        results = r.json()['data']['result']
        for result in results:
            instance = result['metric'].get('instance', 'unknown')
            loads[instance] = float(result['value'][1])
        return loads
    except Exception as e:
        print("Erreur get_load_5m:", e)
        return {}

def get_filesystem():
    query = 'node_filesystem_avail_bytes{mountpoint="/"}'
    fs = {}
    try:
        r = requests.get(PROMETHEUS_URL, params={'query': query})
        results = r.json()['data']['result']
        for result in results:
            instance = result['metric'].get('instance', 'unknown')
            avail = float(result['value'][1])
            fs[instance] = f"{avail / (1024**3):.1f} Go"
        return fs
    except Exception as e:
        print("Erreur get_filesystem:", e)
        return {}

def get_tcp_estab():
    query = 'node_netstat_Tcp_CurrEstab'
    tcp = {}
    try:
        r = requests.get(PROMETHEUS_URL, params={'query': query})
        results = r.json()['data']['result']
        for result in results:
            instance = result['metric'].get('instance', 'unknown')
            tcp[instance] = int(float(result['value'][1]))
        return tcp
    except Exception as e:
        print("Erreur get_tcp_estab:", e)
        return {}

def get_cluster_metrics():
    metrics = get_node_metrics()
    temps = get_temperatures()
    loads = get_load_5m()
    fs = get_filesystem()
    tcp = get_tcp_estab()

    for display_name, data in metrics.items():
        inst = data.get('instance', display_name.split()[0])
        data['temperature'] = temps.get(display_name) or temps.get(inst, None)
        data['load'] = loads.get(inst, None)
        data['filesystem'] = fs.get(inst, None)
        data['tcp'] = tcp.get(inst, None)
        data['power'] = 7 if data['status'] else 0
        data['cost'] = round(data['power'] / 1000.0 * 0.1696, 2)
    return metrics

def unify_consumption_calculation(total_power):
    rate = 0.1696
    kW = total_power / 1000.0
    cost_day = kW * 24 * rate
    return cost_day

def get_cluster_data():
    metrics = get_cluster_metrics()
    total_cpu_cores = 48
    ram_total = 8 * 1024 * 1024 * 1024
    ram_available = 2 * 1024 * 1024 * 1024
    ram_used_percentage = (1 - (ram_available / ram_total)) * 100
    total_power = sum(data.get('power', 0) for data in metrics.values())

    kW = total_power / 1000.0
    energy_minute = kW / 60.0
    cost_minute = energy_minute * 0.1696
    energy_hour = kW
    cost_hour = energy_hour * 0.1696
    energy_day = kW * 24
    cost_day = energy_day * 0.1696
    energy_week = kW * 24 * 7
    cost_week = energy_week * 0.1696
    energy_month = kW * 24 * 30
    cost_month = energy_month * 0.1696 + 14.0359

    return {
        "total_cpu_cores": total_cpu_cores,
        "ram_used_percentage": ram_used_percentage,
        "total_power": total_power,
        "energy_minute": energy_minute,
        "cost_minute": cost_minute,
        "energy_hour": energy_hour,
        "cost_hour": cost_hour,
        "energy_day": energy_day,
        "cost_day": cost_day,
        "energy_week": energy_week,
        "cost_week": cost_week,
        "energy_month": energy_month,
        "cost_month": cost_month,
        "metrics": metrics
    }

def get_alerts():
    try:
        r = requests.get(ALERTMANAGER_URL)
        return r.json()
    except Exception as e:
        print("Erreur get_alerts:", e)
        return []

@app.route('/api/bot/status')
@limiter.limit("3 per second;10 per minute")
def api_bot_status():
    bearer = request.headers.get("Authorization", "")
    expected = f"Bearer {os.environ.get('API_SECRET_TOKEN', '')}"
    if bearer != expected:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_cluster_metrics())

@app.route('/api/bot/ip_threats')
def api_bot_ip_threats():
    bearer = request.headers.get("Authorization", "")
    expected = f"Bearer {os.environ.get('API_SECRET_TOKEN', '')}"
    if bearer != expected:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        with open("data/suspicious_ips.json", "r") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
