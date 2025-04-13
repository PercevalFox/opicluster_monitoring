#!/bin/bash
set -euo pipefail

LOG_FILE="/mnt/shared/logs/watchdog.log"
CRITICAL_CONTAINERS=("web_app" "grafana" "prometheus" "alertmanager" "discord_bot" "ip_defender" "traefik")

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

while true; do
    for container in "${CRITICAL_CONTAINERS[@]}"; do
        status=$(sudo docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || echo "false")
        if [ "$status" != "true" ]; then
            log "🛑 $container is DOWN. Attempting restart..."
            if sudo docker restart "$container" >/dev/null 2>&1; then
                log "✅ $container successfully restarted."
            else
                log "❌ Failed to restart $container. Manual intervention required."
            fi
        fi
    done
    sleep 60
done
