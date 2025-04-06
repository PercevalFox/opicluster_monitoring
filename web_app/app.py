import os
import time
import requests
from flask import Flask, render_template, request, abort, jsonify
from flask_mail import Mail, Message
from sms_alert import send_sms
import json

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

PROMETHEUS_URL = "http://prometheus:9090/api/v1/query"
ALERTMANAGER_URL = "http://alertmanager:9093/api/v2/alerts"

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

def get_node_metrics():
    query = 'up{job="node"}'
    try:
        r = requests.get(PROMETHEUS_URL, params={'query': query})
        results = r.json()['data']['result']
        metrics = {}
        for result in results:
            instance = result['metric'].get('instance', 'unknown')  # ex: "192.168.1.19:9100"
            custom_name = result['metric'].get('name', '')
            display_name = f"{instance} ({custom_name})" if custom_name else instance
            status = (result['value'][1] == '1')
            # On stocke l'instance brute pour faciliter le mapping
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
            # Stockage par display_name et par instance brute
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
            # Conversion en Go
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
    metrics = get_node_metrics()  # Clés : "192.168.1.19:9100 (OPIMASC1)"
    temps = get_temperatures()      # Stocke à la fois par display_name et instance
    loads = get_load_5m()           # Par instance
    fs = get_filesystem()           # Par instance
    tcp = get_tcp_estab()           # Par instance

    for display_name, data in metrics.items():
        inst = data.get('instance', display_name.split()[0])
        # Priorité à la valeur obtenue via l'instance brute
        data['temperature'] = temps.get(display_name) or temps.get(inst, None)
        data['load'] = loads.get(inst, None)
        data['filesystem'] = fs.get(inst, None)
        data['tcp'] = tcp.get(inst, None)
        # Estimation de la puissance: 7W si UP, 0 sinon
        data['power'] = 7 if data['status'] else 0
        # Coût unitaire (€/h) pour ce node
        data['cost'] = round(data['power'] / 1000.0 * 0.1696, 2)
    return metrics

def get_alerts():
    try:
        r = requests.get(ALERTMANAGER_URL)
        return r.json()
    except Exception as e:
        print("Erreur get_alerts:", e)
        return []

def unify_consumption_calculation(total_power):
    rate = 0.1696  # €/kWh
    kW = total_power / 1000.0
    cost_day = kW * 24 * rate
    return cost_day

def get_cluster_data():
    metrics = get_cluster_metrics()
    # Valeurs statiques pour CPU/RAM (à adapter selon vos besoins réels)
    total_cpu_cores = 48
    ram_total = 8 * 1024 * 1024 * 1024    # 8 Go
    ram_available = 2 * 1024 * 1024 * 1024 # 2 Go disponibles
    ram_used_percentage = (1 - (ram_available / ram_total)) * 100

    # Total power cumulée : somme des puissances de chaque node (extraites via get_cluster_metrics)
    total_power = sum(data.get('power', 0) for data in metrics.values())

    # Calcul de consommation à partir de total_power
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
    cost_month = energy_month * 0.1696 + 14.0359  # abonnement mensuel inclus

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

@app.route('/sms_alert', methods=['POST'])
def sms_alert():
    auth_header = request.headers.get("Authorization", "")
    expected_token = f"Bearer {os.environ.get('API_SECRET_TOKEN')}"

    if auth_header != expected_token:
        return jsonify({"error": "Accès refusé : Token invalide"}), 403

    data = request.json
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

@app.route('/api/status')
def api_status():
    return jsonify(get_cluster_metrics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
