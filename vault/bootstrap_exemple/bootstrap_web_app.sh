#!/bin/bash
set -e

APP="web_app"
VAULT_CONTAINER="vault"
VAULT_ADDR_INTERNAL="http://127.0.0.1:8201"
VAULT_TOKEN="A_CHANGER"  # Remplacer par la valeur adéquate (ou via une variable d'environnement)

VAULT_CMD="docker exec -e VAULT_ADDR=$VAULT_ADDR_INTERNAL -e VAULT_TOKEN=$VAULT_TOKEN $VAULT_CONTAINER vault"

echo "[*] Insertion des secrets pour Web App depuis .env (template)"
$VAULT_CMD kv put secret/$APP \
  FLASK_SECRET_KEY="CHANGE_ME_FLASK_SECRET" \
  API_SECRET_TOKEN="CHANGE_ME_API_SECRET_TOKEN" \
  API_SECRET_KEY="CHANGE_ME_API_SECRET_KEY" \
  DATABASE_URL="CHANGE_ME_DATABASE_URL"

echo "[*] Création de la policy $APP pour Web App"

docker exec $VAULT_CONTAINER sh -c "echo '
path \"secret/data/$APP\" {
  capabilities = [\"read\"]
}
' > /tmp/${APP}-policy.hcl"

$VAULT_CMD policy write ${APP}-policy /tmp/${APP}-policy.hcl

echo "[*] Activation AppRole (idempotent) pour Web App"
$VAULT_CMD auth enable approle || true

echo "[*] Création de l’AppRole $APP pour Web App"
$VAULT_CMD write auth/approle/role/$APP \
    token_policies="${APP}-policy" \
    secret_id_ttl=0 \
    token_ttl=60m \
    token_max_ttl=120m

ROLE_ID=$($VAULT_CMD read -field=role_id auth/approle/role/$APP/role-id)
SECRET_ID=$($VAULT_CMD write -f -field=secret_id auth/approle/role/$APP/secret-id)

CREDS_DIR="/home/foxink/opicluster_monitoring/vault/creds/$APP"
mkdir -p "$CREDS_DIR"
echo "$ROLE_ID" > "$CREDS_DIR/role_id"
echo "$SECRET_ID" > "$CREDS_DIR/secret_id"

echo ""
echo "📌 Web App Role ID:     $ROLE_ID"
echo "📌 Web App Secret ID:   $SECRET_ID"
