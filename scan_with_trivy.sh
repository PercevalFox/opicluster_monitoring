#!/bin/bash
set -e

REPORT_DIR="./data"
TIMESTAMP=$(date +'%Y%m%d-%H%M%S')
REPORT_FILE="$REPORT_DIR/trivy_report_$TIMESTAMP.txt"

echo "[INFO] Scan Trivy démarré..."
mkdir -p "$REPORT_DIR"

for d in discord_bot web_app ip_defender; do
    echo "[*] Analyse de $d" >> "$REPORT_FILE"
    trivy fs "./$d" --scanners vuln --severity HIGH,CRITICAL --exit-code 0 >> "$REPORT_FILE"
    echo -e "\n" >> "$REPORT_FILE"
done

echo "[✓] Rapport généré : $REPORT_FILE"
