#!/usr/bin/env python3
import os
import re
import json
import time
from collections import defaultdict, Counter
from datetime import datetime

ACCESS_LOG = "/logs/access.log"
BANLIST_FILE = "/data/banlist.json"
PROM_FILE = "/data/ip_threat.prom"
BAN_THRESHOLD = 15.0
WHITELIST = {"192.168.1.254", "45.155.41.95", "37.167.128.28"}

SENSITIVE_PATHS = [
    "wp-admin", "phpmyadmin", "backup", "admin", "config", "env", ".git", "passwd", "root",
    "token", "setup", "shell", "debug", "sql", ".bak", ".old", ".zip", "login", "secret",
    "vscode", "password", "auth", "rotate", "/api/user/auth-tokens/rotate"
]

CRITICAL_PATHS = [
    ".env", "id_rsa", "user_secrets", "shadow", "passwd",
    "config.yml", "docker-compose.yml", "credentials", "access_token",
    "api_token", "auth-token", "vault", "key.pem", "private.pem"
]

SUSPECT_UAS = ['curl', 'python', '-', 'go-http-client']

LOG_PATTERN = re.compile(
    r'(?P<ip>(?:\d{1,3}\.){3}\d{1,3}).*?"(?P<method>[A-Z]+) (?P<path>[^ ]+)[^"]*" (?P<status>\d{3})'
)

def parse_access_log():
    scores = {}
    if not os.path.exists(ACCESS_LOG):
        print(f"[!] Fichier log introuvable : {ACCESS_LOG}")
        return scores

    ip_data = defaultdict(lambda: {
        'count': 0,
        'statuses': Counter(),
        'paths': Counter(),
        'user_agents': Counter(),
    })

    with open(ACCESS_LOG, "r") as f:
        for line in f:
            match = LOG_PATTERN.search(line)
            if not match:
                continue
            ip = match.group("ip")
            if ip in WHITELIST:
                continue

            path = match.group("path").lower()
            status = int(match.group("status"))

            quoted_fields = re.findall(r'"(.*?)"', line)
            ua = quoted_fields[2].lower() if len(quoted_fields) >= 3 else "unknown"

            data = ip_data[ip]
            data['count'] += 1
            data['statuses'][status] += 1
            data['paths'][path] += 1
            data['user_agents'][ua] += 1

    for ip, data in ip_data.items():
        score = 0

        if data['count'] > 100:
            score += 2
        if any(code in data['statuses'] for code in (401, 404, 403)):
            score += 6
        if any(s in p for p in data['paths'] for s in SENSITIVE_PATHS):
            score += 5
        if any(s in p for p in data['paths'] for s in CRITICAL_PATHS):
            score += 10
        if any(re.search(r'\.(zip|bak|gz|tar|rar|js)$', p) for p in data['paths']):
            score += 5
        if any(re.search(r'/js/[a-z0-9_]{6,}\.js', p) for p in data['paths']):
            score += 6
        if len(data['paths']) > 15:
            score += 2
        if any(s in ua for ua in data['user_agents'] for s in SUSPECT_UAS):
            score += 4
        if any(count > 5 for count in data['paths'].values()):
            score += 3

        scores[ip] = score

    return scores

def write_banlist(scores):
    try:
        banned = [ip for ip, score in scores.items() if score >= BAN_THRESHOLD]
        with open(BANLIST_FILE, "w") as f:
            json.dump({
                "banned_ips": banned,
                "updated": datetime.utcnow().isoformat()
            }, f, indent=2)
        print(f"[+] Banlist mise à jour ({len(banned)} IPs)")
    except Exception as e:
        print(f"[ERROR] Écriture banlist: {e}")

def write_prometheus(scores):
    try:
        with open(PROM_FILE, "w") as f:
            for ip, score in scores.items():
                f.write(f'ip_threat_score{{ip="{ip}"}} {score:.2f}\n')
        print(f"[+] Export Prometheus écrit ({len(scores)} IPs)")
    except Exception as e:
        print(f"[ERROR] Écriture Prometheus: {e}")

def main_loop():
    print("[+] IP Defender en boucle active. Intervalle : 3600")
    while True:
        try:
            print("[*] Scan des logs & génération banlist/prometheus...")
            scores = parse_access_log()
            write_banlist(scores)
            write_prometheus(scores)
        except Exception as e:
            print(f"[CRASH LOOP] Exception: {e}")
        time.sleep(3600)

if __name__ == "__main__":
    try:
        print("[+] Démarrage de IP Defender...")
        main_loop()
    except Exception as e:
        print(f"[CRITICAL] Impossible de lancer le service: {e}")
