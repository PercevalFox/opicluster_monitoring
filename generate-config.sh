#!/bin/bash
set -euo pipefail

ENV_FILE="./vault/secrets/web_app.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Le fichier $ENV_FILE est introuvable. Vérifie que le Vault Agent web_app fonctionne."
  exit 1
fi

echo "[*] Chargement des variables depuis $ENV_FILE"
set -a
while IFS='=' read -r key value; do
  # Ignore les lignes vides et les commentaires
  [[ -z "$key" ]] && continue
  [[ "$key" =~ ^# ]] && continue

  # On retire d'éventuels guillemets déjà présents pour éviter un double quoting
  value="$(echo "$value" | sed 's/^"\(.*\)"$/\1/')"
  # Exportation en s'assurant de "protéger" la valeur
  export "$key"="$(printf '%s' "$value")"
done < "$ENV_FILE"
set +a

echo "[*] Génération de alertmanager.yml à partir de alertmanager.template.yml"
envsubst < alertmanager/alertmanager.template.yml > alertmanager/alertmanager.yml
echo "[✓] alertmanager.yml généré avec succès."
