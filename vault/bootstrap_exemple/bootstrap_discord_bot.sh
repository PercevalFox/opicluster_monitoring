#!/bin/bash
set -e

APP="discord_bot"
VAULT_CONTAINER="vault"
VAULT_ADDR_INTERNAL="http://127.0.0.1:8201"
VAULT_TOKEN="A_CHANGER"  # VARIABLE D'ENV à retirer pour production

VAULT_CMD="docker exec -e VAULT_ADDR=$VAULT_ADDR_INTERNAL -e VAULT_TOKEN=$VAULT_TOKEN $VAULT_CONTAINER vault"

echo "[*] Insertion des secrets Discord Bot depuis .env.bot"

$VAULT_CMD kv put secret/$APP \
  DISCORD_BOT_TOKEN="SAUCISSE" \
  API_HOST="https://votre_host.saucisse" \
  API_SECRET_TOKEN="TOKEN" \
  API_SECRET_KEY="TOKEN_2" \
  DISCORD_CHANNEL_ID="ID_DISCORD_CHANNEL" \
  GRAFANA_URL="https://grafana.votre_host.saucisse" \
  WEBHOOK_GENERAL="https://discord.com/api/webhooks/votre_webhook"

echo "[*] Création de la policy $APP"

docker exec $VAULT_CONTAINER sh -c "echo '
path \"secret/data/$APP\" {
  capabilities = [\"read\"]
}
' > /tmp/${APP}-policy.hcl"

$VAULT_CMD policy write ${APP}-policy /tmp/${APP}-policy.hcl

echo "[*] Activation AppRole (idempotent)"
$VAULT_CMD auth enable approle || true

echo "[*] Création de l’AppRole $APP"
$VAULT_CMD write auth/approle/role/$APP \
    token_policies="${APP}-policy" \
    secret_id_ttl=0 \
    token_ttl=60m \
    token_max_ttl=120m

ROLE_ID=$($VAULT_CMD read -field=role_id auth/approle/role/$APP/role-id)
SECRET_ID=$($VAULT_CMD write -f -field=secret_id auth/approle/role/$APP/secret-id)

CREDS_DIR="/home/PercevalFox/opicluster_monitoring/vault/creds/$APP"
mkdir -p "$CREDS_DIR"
echo "$ROLE_ID" > "$CREDS_DIR/role_id"
echo "$SECRET_ID" > "$CREDS_DIR/secret_id"

echo ""
echo "📌 Role ID:     $ROLE_ID"
echo "📌 Secret ID:   $SECRET_ID"
