pid_file = "/tmp/alertmanager-agent.pid"

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/vault/agent/role_id"
      secret_id_file_path = "/vault/agent/secret_id"
    }
  }

  sink "file" {
    config = {
      path = "/vault/agent/token"
    }
  }
}

template {
  destination = "/vault/secrets/web_app.env"
  contents = <<EOT
SMTP_USER="{{ with secret "secret/web_app/config" }}{{ .Data.data.SMTP_USER }}{{ end }}"
SMTP_PASS="{{ with secret "secret/web_app/config" }}{{ .Data.data.SMTP_PASS }}{{ end }}"
FREE_USER="{{ with secret "secret/web_app/config" }}{{ .Data.data.FREE_USER }}{{ end }}"
FREE_PASS="{{ with secret "secret/web_app/config" }}{{ .Data.data.FREE_PASS }}{{ end }}"
EOT
}
