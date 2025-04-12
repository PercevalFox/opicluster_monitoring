# ✨ opicluster-monitoring

> Full-stack Raspberry Pi + Orange Pi monitoring infrastructure with alerting, dashboards, Discord/SMS integrations, threat detection & hardened security.

---

## ✨ Overview

This project is a fully self-hosted, production-grade monitoring stack built on:

- 🍊 **12x Orange Pi 3 LTS** running `node_exporter`
- 🍓 **1x Raspberry Pi 4** acting as central monitoring node
- ☁️ **K3S cluster** with shared storage mounted at `/mnt/shared`

It includes **Prometheus**, **Grafana**, **Alertmanager**, a custom **Discord bot**, **SMS alerts**, **threat detection**, **web dashboard**, **Vault** and **infrastructure hardening at every level**.

---

## 🌐 Architecture

```text
                          +------------------------+
                          |  https://monitoring.   |
                          | Restricted Access Only |
                          +-----------+------------+
                                      |
                                  [Traefik] 🔐
                                      |
   +-----------+-----------+----------+----------+-----------+---------+
   |           |           |          |          |           |         |
[Web App] [Grafana] [Prometheus][Alertmanager][Vault] [Discord Bot][IP Defender]
                                      |
                        [OrangePi x12 via node_exporter]
```

---

## ⚙️ Features

### 📊 Monitoring & Alerting
- Prometheus scraping 12 Orange Pi nodes via `node_exporter`
- Custom alert rules (🧠 CPU, 🌡️ temperature, 🧮 memory, 💾 disk, 🔌 network, 🌀 swap)
- Grafana dashboards secured with TLS + htpasswd + GeoBlock France-only
- Alertmanager: advanced routing to Discord, SMS (Free Mobile), fallback tiers
- `generate-config.sh`: regenerate alertmanager config from Vault `.env`

### 🌐 Web Dashboard (Flask)
- Served behind Traefik with TLS & security headers
- Views:
  - `/alerts` – Live Prometheus alerts
  - `/ip_threats` – IP scoring & details
  - `/settings`, `/static/`, `/api/bot/status`, `/api/bot/ip_threats`, `/sms_alert`
- Vault Agent injects env securely into container
- Traefik middlewares bypass static to optimize load

### 🤖 Discord Bot
- Modular command set:
  - `status`, `grafana`, `ipthreats`, `games`
- Auto-reply + metrics exposed
- `scheduler_daily.py` → Daily reporting task
- Grafana dashboard screenshot every 1h 
- `.last_message_id` tracking to avoid Discord spam
- Vault-injected secrets, `read_only`, `tmpfs`, `seccomp`

### 🛡️ IP Threat Detection
- `ip_defender` scores requests from Traefik logs hourly
- `generate_suspicious_ips.py` exports:
  - `/data/ip_threat.prom` (Prometheus format)
  - `/data/banlist.json` (banned IPs)
- Detection logic includes:
  - path matching (e.g. `.env`, `admin`, etc.)
  - UA fuzzing, repetition, error ratio, obfuscated JS, uncommon extensions
  - geoIP via `ip-api.com` + whitelist

### 🔐 Traefik & GeoBlock Security
- `traefik-auth`: htpasswd middleware
- `geoblock-france@file`, `geoblock-only@file`: France-only or API-only rules
- Full HSTS, TLS 1.3, strict CSP, X-Robots-Tag, PermissionsPolicy
- Custom `GeoBlock` plugin via PascalMinder

### 🔒 Container & Network Hardening
- Docker:
  - `read_only`, `seccomp`, `cap_drop: ALL`, `tmpfs`, `no-new-privileges`
- Network:
  - iptables DROP, SSH rate limit (3/min), ICMP limited
- Fail2ban enabled on boot
- Healthchecks on every service

### 🧪 Security Audits & Scanners
- `scan_with_bandit.sh`: Python SAST report (stored in `/data/bandit_report_*.txt`)
- `scan_with_trivy.sh`: container vulnerability scan (CRITICAL/HIGH only)
- `lynishard.sh`, `aide_scan_test.sh`: local system audit reports
- `.gitignore`: secrets, reports, state, cache, backups all excluded

### 🔐 Secrets Management via Vault
- HashiCorp Vault container auto-started
- Agents:
  - `vault-agent-web_app`
  - `vault-agent-grafana`
  - `vault-agent-discord_bot`
- Configs under `vault/agent/*.hcl`
- Secret mounts: `/vault/secrets/*.env`
- Bootstrap scripts per service

### 🆘 Boot Control & Alerting
- `startup_checker.py`:
  - Waits for boot, launches containers
  - Inspects health of core stack (`CRITICAL_CONTAINERS`)
  - Sends SMS alert via Free API if any container fails

---

## 🚀 Deployment

```bash
# Launch stack
sudo docker-compose up -d

# Static analysis
./scan_with_bandit.sh

# Image vulnerability scan
./scan_with_trivy.sh

# Regenerate Alertmanager config from Vault secrets
./generate-config.sh
```

---

## 📊 Dashboards & Access

- 🌍 Web App: https://monitoring.opicluster.online (auth required)
- 📈 Grafana: https://grafana.monitoring.opicluster.online 
- 🧠 Prometheus: https://prometheus.monitoring.opicluster.online (auth required)
- 🚨 Alertmanager: https://alertmanager.monitoring.opicluster.online (auth required)
- 🧾 Public Grafana Dashboard: [Main Dashboard](https://grafana.monitoring.opicluster.online/public-dashboards/666de8ff490c443896ce76e43fd3375a)
- ⚙️ Traefik: https://traefik.monitoring.opicluster.online (auth required)

---

## 🔐 Admin Zone
<details>
<summary>⚖️ Internals & Maintenance Scripts</summary>

### 💡 Services
- All 12 Orange Pis monitored with `node_exporter:9100`
- Shared mountpoint: `/mnt/shared`
- Centralized scripts and logs stored under `data/` or `tools/`

### 🧰 Tools
- `generate_suspicious_ips.py`: extract, enrich and rank suspicious requests
- `ip_defender`: ban scoring engine, Prometheus export
- `startup_checker.py`: auto-checks boot & SMS fallback
- `scan_with_bandit.sh`, `scan_with_trivy.sh`: security scans
- `lynishard.sh`, `aide_scan_test.sh`: system hardening scan

### 🧹 Admin Scripts
- `choose_and_run.sh`: interactive maintenance tool
- `clean_docker.sh`: garbage collector for Docker volumes/images/networks

### 🔐 External Config Files
- `/etc/security/*.conf`: faillock, pam_env, access, time, sepermit
- `vault/*.hcl`, `vault/*.env`, `vault/creds`, `vault/secrets`

</details>

---

## 🚧 Roadmap / TODO

- [ ] Autoload Grafana dashboards (`provisioning/`)
- [ ] Add **Loki + Promtail** for log aggregation
- [ ] Webhook support (Telegram, Mattermost, etc.)
- [ ] GitHub Actions CI/CD: build, scan, deploy
- [ ] Ansible: bootstrap OPI nodes + Vault init + AIDE/Lynis
- [ ] Self-healing: container restarts, fallback IP failover

---

## 👨‍💻 Author

**PercevalFox** — _DevSecOps @ opicluster_

