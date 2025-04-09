#!/usr/bin/env python3
import subprocess
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/foxink/opicluster_monitoring/.env.secrets")

FREE_USER = os.getenv("FREE_USER")
FREE_PASS = os.getenv("FREE_PASS")

CRITICAL_CONTAINERS = [
    "web_app",
    "grafana",
    "prometheus",
    "alertmanager",
    "discord_bot",
    "ip_defender",
    "traefik"
]

def send_sms(message):
    if not FREE_USER or not FREE_PASS:
        print("❌ FREE_USER or FREE_PASS non définis")
        return
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER}&pass={FREE_PASS}&msg={message}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print("✅ SMS envoyé")
        else:
            print(f"❌ Erreur SMS : {r.status_code}")
    except Exception as e:
        print(f"❌ Exception lors de l’envoi SMS : {e}")

def is_container_running(name):
    try:
        result = subprocess.run(
            ["sudo", "docker", "inspect", "--format", "{{.State.Running}}", name],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip() == "true"
    except subprocess.CalledProcessError:
        return False

def main():
    print("⏳ Lancement du cluster...")
    subprocess.run(["sudo", "docker-compose", "up", "-d"], cwd="/home/foxink/opicluster_monitoring")
    time.sleep(20)

    failed = []

    for container in CRITICAL_CONTAINERS:
        if not is_container_running(container):
            failed.append(f"🛑 Container DOWN: {container}")

    if failed:
        msg = "[🚨 BOOT CHECK FAIL]\n" + "\n".join(failed)
        send_sms(msg)
    else:
        msg = "[✅ BOOT OK] Tous les containers sont UP et fonctionnels."
        send_sms(msg)

if __name__ == "__main__":
    main()
