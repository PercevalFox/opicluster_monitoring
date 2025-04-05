#!/bin/bash
set -euo pipefail

if [ ! -f .env.secrets ]; then
  echo "Erreur : fichier .env.secrets introuvable."
  exit 1
fi

echo "[*] Génération de alertmanager.yml à partir de alertmanager.template.yml"
export $(grep -v '^#' .env.secrets | xargs)

envsubst < alertmanager/alertmanager.template.yml > alertmanager/alertmanager.yml
echo "[✓] alertmanager.yml généré avec succès."
