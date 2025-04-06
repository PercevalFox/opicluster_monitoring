import os
import requests
import csv
from io import StringIO
from collections import Counter
from discord import File

def register(bot):
    @bot.command()
    async def ipthreats(ctx):
        """Analyse enrichie des IPs suspectes"""
        try:
            url = f"{os.getenv('API_HOST')}/api/bot/ip_threats"
            headers = {"Authorization": f"Bearer {os.getenv('API_SECRET_TOKEN')}"}
            r = requests.get(url, headers=headers)
            data = r.json()

            if not isinstance(data, list) or not data:
                await ctx.send("❌ Aucune donnée IP disponible.")
                return

            top_scores = sorted(data, key=lambda x: x.get("Score", 0), reverse=True)[:5]
            top_str = "\n\n".join(
                f"**{ip['IP']}** (Score: {ip['Score']}, Requêtes: {ip['Requests']})\n"
                f"→ `401:{ip['401']} 403:{ip['403']} 404:{ip['404']}`\n"
                f"→ UA: `{ip['UA_sample'][:40]}`"
                for ip in top_scores
            )

            recent_str = "\n".join(
                f"- `{ip['IP']}` (Score {ip['Score']}, {ip['Requests']} reqs)" for ip in data[-5:]
            )

            countries = [ip.get("CountryCode", "??") for ip in data]
            top_countries = Counter(countries).most_common(5)
            flag = lambda c: chr(127397 + ord(c[0])) + chr(127397 + ord(c[1])) if len(c) == 2 else "🏳️"
            country_str = "\n".join(
                f"- {c} {flag(c)} : {n} tentatives" for c, n in top_countries
            )

            msg = (
                "🛡️ **Analyse enrichie des IPs suspectes**\n\n"
                "🔥 **Top 5 par score :**\n" +
                top_str +
                "\n\n🕓 **Dernières IPs détectées :**\n" +
                recent_str +
                "\n\n🌍 **Pays les plus actifs :**\n" +
                country_str
            )
            await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Erreur : {e}")

    @bot.command()
    async def ipinfo(ctx, ip_query: str):
        """Détails complets pour une IP spécifique"""
        try:
            url = f"{os.getenv('API_HOST')}/api/bot/ip_threats"
            headers = {"Authorization": f"Bearer {os.getenv('API_SECRET_TOKEN')}"}
            r = requests.get(url, headers=headers)
            data = r.json()

            target = next((ip for ip in data if ip["IP"] == ip_query), None)

            if not target:
                await ctx.send(f"❌ Aucune donnée trouvée pour {ip_query}")
                return

            flag = lambda c: chr(127397 + ord(c[0])) + chr(127397 + ord(c[1])) if len(c) == 2 else "🏳️"
            country = target.get("Country", "Inconnu")
            cc = target.get("CountryCode", "??")

            msg = (
                f"🕵️ **Détails pour `{ip_query}`**\n\n"
                f"🌍 Pays : {country} {flag(cc)}\n"
                f"🔢 Score : {target['Score']} / Requêtes : {target['Requests']}\n"
                f"🧾 UA : `{target['UA_sample'][:100]}`\n"
                f"🚫 401:{target['401']} 403:{target['403']} 404:{target['404']}\n"
                f"📂 Chemins critiques :\n```{target['Critical_paths'][:400]}...```"
            )
            await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Erreur : {e}")

    @bot.command()
    async def ipdump(ctx):
        """Exporte uniquement les IPs suspectes en CSV"""
        try:
            url = f"{os.getenv('API_HOST')}/api/bot/ip_threats"
            headers = {"Authorization": f"Bearer {os.getenv('API_SECRET_TOKEN')}"}
            r = requests.get(url, headers=headers)
            data = r.json()

            if not isinstance(data, list) or not data:
                await ctx.send("❌ Aucune IP à exporter.")
                return

            # Génère un CSV contenant uniquement la colonne IP
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["IP"])
            for row in data:
                writer.writerow([row["IP"]])

            output.seek(0)
            await ctx.send("📎 Liste des IPs suspectes :", file=File(fp=output, filename="ip_list.csv"))

        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'export : {e}")
