from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import requests
import datetime

def init_scheduler(bot):
    scheduler = AsyncIOScheduler()

    @scheduler.scheduled_job("cron", hour=8, minute=0)
    async def daily_report():
        await send_report(bot)

    @bot.command()
    async def daily(ctx):
        """Affiche manuellement le rapport du cluster"""
        await send_report(bot, ctx.channel)

    scheduler.start()

async def send_report(bot, channel=None):
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    if not channel:
        channel = bot.get_channel(channel_id)
    if not channel:
        return

    try:
        headers = {"Authorization": f"Bearer {os.getenv('API_SECRET_TOKEN')}"}
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
        temps_high = [f"{name} : {d.get('temperature')}°C" for name, d in data.items() if d.get("temperature", 0) >= 40]

        msg = f"""📅 Rapport Cluster – {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
🟢 Nœuds UP : {up} / {total}
🌡️ Températures : max {temp_max:.1f}°C, min {temp_min:.1f}°C
🔥 Temp > 40°C :\n- """ + "\n- ".join(temps_high) + f"""
⚡ Charge moyenne : {avg_load}
📊 Charge max : {load_peak[0]} ({load_peak[1]})
💾 Disques critiques :\n- """ + ("\n- ".join(disk_low) if disk_low else "Aucun")

        await channel.send(msg)
    except Exception as e:
        await channel.send(f"⚠️ Erreur dans le rapport : {e}")