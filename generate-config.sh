#!/bin/bash
set -euo pipefail

ENV_FILE="./vault/secrets/web_app.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Le fichier $ENV_FILE est introuvable. Vérifie que le Vault Agent web_app fonctionne."
  exit 1
fi

echo "[*] Chargement des variables depuis $ENV_FILE"
set -a
source "$ENV_FILE"
set +a

echo "[*] Génération de alertmanager.yml à partir de alertmanager.template.yml"
envsubst < alertmanager/alertmanager.template.yml > alertmanager/alertmanager.yml
echo "[✓] alertmanager.yml généré avec succès."
