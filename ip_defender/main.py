import re
import json
import time
from collections import defaultdict
from datetime import datetime

ACCESS_LOG = "/logs/access.log"
BANLIST_FILE = "/data/banlist.json"
PROM_FILE = "/data/ip_threat.prom"
BAN_THRESHOLD = 15
SLEEP_INTERVAL = 3600  # secondes
WHITELIST = {"192.168.1.254", "45.155.41.95", "37.167.128.28"}

def parse_access_log():
    scores = defaultdict(int)
    try:
        with open(ACCESS_LOG, "r") as f:
            for line in f:
                match = re.search(r'(?P<ip>\d+\.\d+\.\d+\.\d+).*"(GET|POST|HEAD) (?P<url>.*?) HTTP/', line)
                if match:
                    ip = match.group("ip")
                    if ip in WHITELIST:
                        continue
                    url = match.group("url")
                    if "wp-login" in url or "admin" in url:
                        scores[ip] += 5
                    elif "/sms_alert" in url or "/api/" in url:
                        scores[ip] += 1
                    else:
                        scores[ip] += 0.1
    except Exception as e:
        print(f"[!] Error parsing log: {e}")
    return scores

def write_banlist(scores):
    banned = [ip for ip, score in scores.items() if score >= BAN_THRESHOLD]
    with open(BANLIST_FILE, "w") as f:
        json.dump({"banned_ips": banned, "updated": datetime.utcnow().isoformat()}, f, indent=2)

def write_prometheus(scores):
    with open(PROM_FILE, "w") as f:
        for ip, score in scores.items():
            f.write(f'ip_threat_score{{ip="{ip}"}} {score:.2f}\n')

def main_loop():
    while True:
        print("[*] Scanning logs & updating banlist/prometheus export...")
        scores = parse_access_log()
        write_banlist(scores)
        write_prometheus(scores)
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main_loop()
