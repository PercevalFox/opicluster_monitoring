import os
import requests

def register(bot):
    @bot.command()
    async def status(ctx):
        """Affiche le statut détaillé du cluster"""
        headers = {
            "Authorization": f"Bearer {os.getenv('API_SECRET_TOKEN')}"
        }
        try:
            r = requests.get(f"{os.getenv('API_HOST')}/api/bot/status", headers=headers)
            data = r.json()

            up = sum(1 for d in data.values() if d.get("status"))
            total = len(data)
            temps = [d.get("temperature", 0) for d in data.values() if "temperature" in d]
            loads = [(name, d.get("load", 0)) for name, d in data.items() if "load" in d]
            disks = [(name, d.get("filesystem", "")) for name, d in data.items() if "filesystem" in d]

            temp_max = max(temps) if temps else "N/A"
            temp_min = min(temps) if temps else "N/A"
            avg_load = round(sum(v for _, v in loads) / len(loads), 2) if loads else 0
            load_peak = max(loads, key=lambda x: x[1], default=("N/A", 0))

            disk_low = [f"{name} ({space})" for name, space in disks if space and space.endswith("Go") and float(space.split()[0]) < 2.0]

            msg = f"""📊 **Statut du Cluster**
                🟢 Nœuds UP : {up}/{total}
                🌡️ Température : max {temp_max}°C | min {temp_min}°C
                ⚡ Charge moyenne : {avg_load} | Max : {load_peak[0]} ({load_peak[1]})
                💾 Disques faibles :\n- """ + ("\n- ".join(disk_low) if disk_low else "Aucun")

            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"❌ Erreur API: {e}")