import os
import discord
from discord.ext import commands
from modules import commands_status, commands_ipthreats, commands_grafana, scheduler_daily

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} prêt.")
    scheduler_daily.init_scheduler(bot)

@bot.command(name="help")
async def custom_help(ctx):
    msg = (
        "📖 **Commandes disponibles :**\n\n"
        "🟢 `!status`\n→ Affiche le statut détaillé du cluster\n\n"
        "🔥 `!ipthreats`\n→ Affiche les IPs suspectes : top 5, 5 plus récentes, pays actifs\n\n"
        "🔥 `!ipinfo`\n→ Info sur une IP ciblée avec full détails\n\n"
        "📊 `!dashboard`\n→ Lien vers Grafana\n\n"
        "📖 `!ipdump`\n→ Exporte toutes les IPs suspectes en CSV\n\n"
        "📅 `!daily`\n→ Affiche manuellement le rapport complet du cluster\n"
    )
    await ctx.send(msg)

# Charger les modules de commandes
commands_status.register(bot)
commands_ipthreats.register(bot)
commands_grafana.register(bot)

bot.run(TOKEN)