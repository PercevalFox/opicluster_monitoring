#!/usr/bin/env python3
import re
import json
import requests
from collections import defaultdict, Counter

LOG_PATH = "/home/foxink/opicluster_monitoring/traefik/logs/access.log"
OUTPUT_PATH = "/home/foxink/opicluster_monitoring/data/suspicious_ips.json"
WHITELIST = {"192.168.1.254"}

SENSITIVE_PATHS = [
    "wp-admin", "phpmyadmin", "backup", "admin", "config", "env", ".git", "passwd", "root",
    "token", "setup", "shell", "debug", "sql", ".bak", ".old", ".zip", "login", "secret",
    "vscode", "password", "auth", "rotate", "/api/user/auth-tokens/rotate"
]
SUSPECT_UAS = ['curl', 'python', '-', 'go-http-client']

LOG_PATTERN = re.compile(
    r'(?P<ip>(?:\d{1,3}\.){3}\d{1,3}).*?"(?P<method>[A-Z]+) (?P<path>[^ ]+)[^"]*" (?P<status>\d{3})'
)

def get_geo(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=country,countryCode", timeout=2)
        if r.status_code == 200:
            j = r.json()
            return j.get("country", "Unknown"), j.get("countryCode", "XX")
    except Exception:
        pass
    return "Unknown", "XX"

with open(LOG_PATH, "r") as f:
    lines = f.readlines()

ip_data = defaultdict(lambda: {
    'count': 0,
    'statuses': Counter(),
    'paths': Counter(),
    'user_agents': Counter(),
    'score': 0,
})

for line in lines:
    match = LOG_PATTERN.search(line)
    if not match:
        continue

    ip = match.group("ip")
    if ip in WHITELIST:
        continue

    path = match.group("path").lower()
    status = int(match.group("status"))

    # Essayons de récupérer les User-Agent dans les champs "..." du log
    quoted_fields = re.findall(r'"(.*?)"', line)
    ua = quoted_fields[2].lower() if len(quoted_fields) >= 3 else "unknown"

    data = ip_data[ip]
    data['count'] += 1
    data['statuses'][status] += 1
    data['paths'][path] += 1
    data['user_agents'][ua] += 1

scored_ips = []

for ip, data in ip_data.items():
    score = 0

    if data['count'] > 100:
        score += 2
    if any(code in data['statuses'] for code in (401, 404, 403)):
        score += 6
    if any(s in p for p in data['paths'] for s in SENSITIVE_PATHS):
        score += 5
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

    if score >= 6:
        country, cc = get_geo(ip)
        ua_sample = next(iter(data['user_agents']), "-")
        scored_ips.append({
            "IP": ip,
            "Country": country,
            "CountryCode": cc,
            "Score": score,
            "Requests": data['count'],
            "401": data['statuses'].get(401, 0),
            "403": data['statuses'].get(403, 0),
            "404": data['statuses'].get(404, 0),
            "UA_sample": ua_sample,
            "Top_paths": ', '.join(list(data['paths'].keys())[:2])
        })

with open(OUTPUT_PATH, "w") as out:
    json.dump(scored_ips, out, indent=2)

print(f"✅ Export terminé vers: {OUTPUT_PATH} ({len(scored_ips)} IPs suspectes)")
