# ✨ opicluster-monitoring

> Full-stack Raspberry Pi monitoring infrastructure with alerting, dashboards, bot integration and threat detection.

---

## ✨ Overview

This project is a self-hosted, production-grade monitoring stack built on:

- **12x Orange Pi 3 LTS** running `node_exporter`
- **1x Raspberry Pi 4** acting as central monitoring node
- **K3S cluster** (shared volume: `/mnt/shared`)

It includes Prometheus, Grafana, Alertmanager, Discord bot alerts, SMS fallback, web dashboard, and hardened security.

---

## 🌐 Architecture

```text
                          +-----------------------+
                          | Restricted Access via |
                          |  https://monitoring.  |
                          +-----------+-----------+
                                     |
                                 [Traefik]
                                     |
             +-----------+-----------+----------+----------+
             |           |           |          |          |
         [Web App]  [Grafana]  [Prometheus] [Alertmanager] [Vault]
                                     |
                      [OrangePi x12 via node_exporter]
```

---

## ⚙️ Features

### Monitoring & Alerting
- Prometheus scraping 12 Orange Pi nodes via `node_exporter`
- Custom alert rules (temperature, CPU, memory, disk, etc.)
- Grafana dashboards with TLS + auth + French geoblocking
- Alertmanager routing alerts via email, Discord, and SMS (via Free Mobile)

### Web Dashboard
- Flask-based `web_app`, served through Traefik
- Views:
  - `/alerts` → real-time Prometheus alerts
  - `/ip_threats` → suspicious IPs from Traefik logs
  - `/settings`, `/api/bot/*`, `/sms_alert` endpoints
- Vault agent injects secrets securely

### Discord Bot
- Discord bot container with modular commands:
  - `status`, `grafana`, `ipthreats`, `games`
- Scheduled tasks and real-time status push

### IP Reputation & Threat Detection
- `ip_defender` service scoring Traefik logs and exporting Prometheus metrics
- `generate_suspicious_ips.py` builds a JSON report from logs
- Export to `/data/ip_threat.prom` & `/data/banlist.json`

### Security & Hardening
- Iptables rules (default DROP), SSH rate-limiting, ICMP limited
- Fail2ban enabled at startup
- Docker services with:
  - `read_only`, `tmpfs`, `seccomp`, `cap_drop`, `no-new-privileges`
- Traefik middlewares:
  - GeoBlock (France-only)
  - Basic Auth (htpasswd)
  - Strict TLS 1.3 (ACME, HSTS, CSP, X-Frame)

### Secrets Management
- HashiCorp Vault with sidecar agents
- Injects `.env` securely for:
  - web_app
  - grafana
  - discord_bot
- Config files in `vault/agent/*.hcl`

---

## ⚡ Boot & SMS Alert
- `startup_checker.py`: launches full stack and checks critical containers
- If one fails, sends a **SMS** alert via Free Mobile API

---

## 🚀 Deployment
```bash
# Start all services
sudo docker-compose up -d

# Scan source code with Bandit
./scan_with_bandit.sh

# Scan containers with Trivy
./scan_with_trivy.sh

# Generate Alertmanager config from Vault env
./generate-config.sh
```

---

## 📊 Dashboard
Access:
- https://monitoring.opicluster.online (web)
- https://grafana.monitoring.opicluster.online (Grafana)
- https://prometheus.monitoring.opicluster.online (Prometheus)
- https://alertmanager.monitoring.opicluster.online (Alertmanager)

---

## 🔐 Admin Zone (private)
<details>
<summary>⚖️ Admin Internals & Scripts</summary>

### Services
- 12x Orange Pi are scraped via Prometheus (`node_exporter` on port 9100)
- Shared mountpoint: `/mnt/shared`
- All metrics, logs, threats and tools centralised there

### Internal Tools
- `generate_suspicious_ips.py`: JSON IP scan export
- `ip_defender`: banlist + Prometheus exposition
- `startup_checker.py`: SMS alert with container status
- `scan_with_bandit.sh`, `scan_with_trivy.sh`: local security audits

### Admin Scripts
- `choose_and_run.sh`: interactive ops launcher
- `clean_docker.sh`: Docker GC cleaner
- `lynishard.sh`, `aide_scan_test.sh`: local hardening audits

</details>

---

## 🚧 TODO
- [ ] Add Grafana provisioning with multiple pre-built dashboards
- [ ] Add webhook support for external integrations (Telegram, Mattermost, etc.)

---

## ✨ Author
**PercevalFox** — _DevSecOps @ opicluster_
