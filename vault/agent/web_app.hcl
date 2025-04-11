pid_file = "/tmp/vault-agent-web_app.pid"

vault {
  address = "http://vault:8201"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/vault/creds/web_app/role_id"
      secret_id_file_path = "/vault/creds/web_app/secret_id"
    }
  }

  sink "file" {
    config = {
      path = "/vault/creds/web_app/token"
    }
  }
}

template {
  destination = "/vault/secrets/web_app.env"
  command     = "pkill -HUP web_app || true"
  contents    = <<EOT
# Ce fichier est généré par Vault Agent pour la Web App.
FLASK_SECRET_KEY={{ with secret "secret/data/web_app" }}{{ .Data.data.FLASK_SECRET_KEY }}{{ end }}
API_SECRET_TOKEN={{ with secret "secret/data/web_app" }}{{ .Data.data.API_SECRET_TOKEN }}{{ end }}
API_SECRET_KEY={{ with secret "secret/data/web_app" }}{{ .Data.data.API_SECRET_KEY }}{{ end }}
FREE_USER={{ with secret "secret/data/web_app" }}{{ .Data.data.FREE_USER }}{{ end }}
FREE_PASS={{ with secret "secret/data/web_app" }}{{ .Data.data.FREE_PASS }}{{ end }}
SMTP_SMARTHOST={{ with secret "secret/data/web_app" }}{{ .Data.data.SMTP_SMARTHOST }}{{ end }}
SMTP_FROM={{ with secret "secret/data/web_app" }}{{ .Data.data.SMTP_FROM }}{{ end }}
SMTP_AUTH_USERNAME={{ with secret "secret/data/web_app" }}{{ .Data.data. SMTP_AUTH_USERNAME }}{{ end }}
SMTP_AUTH_PASSWORD={{ with secret "secret/data/web_app" }}{{ .Data.data.SMTP_AUTH_PASSWORD }}{{ end }}
TRAEFIK_USER={{ with secret "secret/data/web_app" }}{{ .Data.data.TRAEFIK_USER }}{{ end }}
TRAEFIK_PASSWORD={{ with secret "secret/data/web_app" }}{{ .Data.data.TRAEFIK_PASSWORD }}{{ end }}
EOT
}
