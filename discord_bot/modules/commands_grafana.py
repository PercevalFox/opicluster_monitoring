import os

def register(bot):
    @bot.command()
    async def dashboard(ctx):
        """Affiche le lien vers le dashboard Grafana"""
        try:
            grafana_base = os.getenv("GRAFANA_URL", "https://grafana.monitoring.opicluster.online")

            # Lien complet vers le dashboard
            dashboard_url = (
                f"{grafana_base}/d/opicluster-dash/opicluster-dashboard"
                f"?orgId=1&from=now-24h&to=now&timezone=browser&var-HOST=$__all&refresh=1m"
            )

            # Envoie le lien vers le dashboard complet
            await ctx.send(f"🔗 Voici le [Dashboard Grafana complet]({dashboard_url})")

        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'affichage du dashboard : {e}")
