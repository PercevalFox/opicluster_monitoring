#!/bin/bash

# Dossier dans lequel se trouve ton code à auditer
CODE_DIR="/home/foxink/opicluster_monitoring"  

# Dossier de sortie des rapports
REPORT_DIR="/home/foxink/opicluster_monitoring/data"
TIMESTAMP=$(date +'%Y%m%d-%H%M%S')
REPORT_FILE="$REPORT_DIR/bandit_report_$TIMESTAMP.txt"

mkdir -p "$REPORT_DIR"

# Activer l'environnement virtuel si nécessaire :
# source /opt/bandit_venv/bin/activate

echo "[INFO] Lancement de l'analyse Bandit sur $CODE_DIR"
bandit -r "$CODE_DIR" -f txt -o "$REPORT_FILE"

echo "[INFO] Rapport généré : $REPORT_FILE"
