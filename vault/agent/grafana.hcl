pid_file = "/tmp/vault-agent-grafana.pid"

vault {
  address = "http://vault:8201"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/vault/creds/grafana/role_id"
      secret_id_file_path = "/vault/creds/grafana/secret_id"
    }
  }

  sink "file" {
    config = {
      path = "/vault/creds/grafana/token"
    }
  }
}

template {
  destination = "/vault/secrets/grafana.env"
  command     = "pkill -HUP grafana || true"
  contents    = <<EOT
# Ce fichier est généré par Vault Agent pour Grafana.
GRAFANA_USER={{ with secret "secret/data/grafana" }}{{ .Data.data.GRAFANA_USER }}{{ end }}
GRAFANA_PASS={{ with secret "secret/data/grafana" }}{{ .Data.data.GRAFANA_PASS }}{{ end }}
EOT
}
