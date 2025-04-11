pid_file = "/tmp/vault-agent-discord.pid"

vault {
  address = "http://vault:8201"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/vault/creds/discord_bot/role_id"
      secret_id_file_path = "/vault/creds/discord_bot/secret_id"
    }
  }

  sink "file" {
    config = {
      path = "/vault/creds/discord_bot/token"
    }
  }
}

template {
  destination = "/vault/secrets/discord_bot.env"
  command     = "pkill -HUP discord_bot || true"
  contents = <<EOT
DISCORD_BOT_TOKEN={{ with secret "secret/data/discord_bot" }}{{ .Data.data.DISCORD_BOT_TOKEN }}{{ end }}
API_HOST={{ with secret "secret/data/discord_bot" }}{{ .Data.data.API_HOST }}{{ end }}
API_SECRET_TOKEN={{ with secret "secret/data/discord_bot" }}{{ .Data.data.API_SECRET_TOKEN }}{{ end }}
API_SECRET_KEY={{ with secret "secret/data/discord_bot" }}{{ .Data.data.API_SECRET_KEY }}{{ end }}
DISCORD_CHANNEL_ID={{ with secret "secret/data/discord_bot" }}{{ .Data.data.DISCORD_CHANNEL_ID }}{{ end }}
GRAFANA_URL={{ with secret "secret/data/discord_bot" }}{{ .Data.data.GRAFANA_URL }}{{ end }}
WEBHOOK_GENERAL={{ with secret "secret/data/discord_bot" }}{{ .Data.data.WEBHOOK_GENERAL }}{{ end }}
EOT
}
