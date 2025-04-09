from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
import os
import requests
import datetime
import asyncio

LOGFILE = "/data/execute_script.log"
_scheduler_instance = None

def log(msg: str):
    timestamp = datetime.datetime.now(timezone("Europe/Paris")).strftime("[%Y-%m-%d %H:%M:%S]")
    full_msg = f"{timestamp} {msg}"
    print(full_msg)
    try:
        with open(LOGFILE, "a") as f:
            f.write(full_msg + "\n")
    except Exception as e:
        print(f"[LogError] Impossible d’écrire dans {LOGFILE} : {e}")

# Initialisation du scheduler
async def init_scheduler(bot):
    global _scheduler_instance

    if _scheduler_instance is not None:
        log("⚠️ Scheduler déjà initialisé.")
        return

    scheduler = AsyncIOScheduler(timezone=timezone("Europe/Paris"))

    @scheduler.scheduled_job("cron", hour=10, minute=0)
    async def daily_report():
        log("⏰ Lancement du job 'daily_report'")
        await send_report(bot)

    @bot.command()
    async def daily(ctx):
        """Affiche manuellement le rapport du cluster"""
        await send_report(bot, ctx.channel)

    scheduler.start()
    _scheduler_instance = scheduler
    log("✅ Scheduler lancé avec job 'daily_report' à 10h (Europe/Paris)")

# Fonction pour envoyer le rapport
async def send_report(bot, channel=None):
    try:
        channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
        if not channel:
            channel = bot.get_channel(channel_id)
        if not channel:
            log(f"❌ Aucun canal trouvé pour ID {channel_id}")
            return

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

        disk_low = [f"{name} ({space})" for name, space in disks if space.endswith("Go") and float(space.split()[0]) < 2.0]
        temps_high = [f"{name} : {d.get('temperature')}°C" for name, d in data.items() if d.get("temperature", 0) >= 40]

        now = datetime.datetime.now(timezone("Europe/Paris")).strftime('%Y-%m-%d %H:%M')

        msg = (
            f"📅 Rapport Cluster – {now}\n"
            f"🟢 Nœuds UP : {up} / {total}\n"
            f"🌡️ Températures : max {temp_max:.1f}°C, min {temp_min:.1f}°C\n"
            f"🔥 Temp > 40°C :\n- " + ("\n- ".join(temps_high) if temps_high else "RAS") + "\n"
            f"⚡ Charge moyenne : {avg_load}\n"
            f"📊 Charge max : {load_peak[0]} ({load_peak[1]})\n"
            f"💾 Disques critiques :\n- " + ("\n- ".join(disk_low) if disk_low else "Aucun")
        )

        await channel.send(msg)
        log("✅ Rapport Discord envoyé avec succès.")
    except Exception as e:
        err = f"⚠️ Erreur dans le rapport : {e}"
        log(err)
        if channel:
            await channel.send(err)
