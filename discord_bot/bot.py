import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import time  # Assurez-vous d'importer 'time'
from modules import scheduler_daily, commands_games, commands_status, commands_ipthreats, commands_grafana

# Charger les variables d'environnement
load_dotenv()

# Récupérer le token de Discord depuis les variables d'environnement
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Définir les intents nécessaires pour interagir avec les messages et autres événements
intents = discord.Intents.default()
intents.message_content = True

# Initialiser le bot avec des paramètres personnalisés
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None  # Désactive la commande d'aide par défaut
)

# Variable pour l'uptime
start_time = time.time()

@bot.command(name="serverinfo")
async def server_info(ctx):
    """Affiche les informations du serveur Discord"""
    
    guild = ctx.guild  # Récupère l'objet Guild (le serveur Discord)
    
    # Crée un message d'information avec des détails sur le serveur
    embed = discord.Embed(
        title=f"Informations sur le serveur {guild.name}",
        description=f"ID: {guild.id}",
        color=discord.Color.blue()
    )
    
    # Ajoute les champs avec des émoticônes
    embed.add_field(name="👑 Propriétaire", value=guild.owner, inline=True)
    embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Créé le", value=guild.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    embed.add_field(name="🚀 Boosts", value=guild.premium_subscription_count, inline=True)
    
    # Affiche l'embed dans le canal où la commande a été exécutée
    await ctx.send(embed=embed)

# Quand le bot est prêt, initialiser le scheduler et envoyer un message dans le canal spécifique
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} prêt.")
    channel = discord.utils.get(bot.get_all_channels(), name="général")
    if channel:
        await channel.send(f"🚀 Le bot {bot.user} est maintenant en ligne et prêt à fonctionner !")

# Initialisation du scheduler et des commandes de jeu
async def setup():
    # Attendre l'initialisation du scheduler
    await scheduler_daily.init_scheduler(bot)
    # Attendre l'enregistrement des commandes de jeu
    await commands_games.register(bot)

# Appel du setup_hook pour s'assurer que le scheduler et les commandes de jeux sont lancés correctement
bot.setup_hook = setup

@bot.command(name="ping", help="Répond avec 'Pong!' et donne la latence du bot")
async def ping(ctx):
    """Répond avec 'Pong!' et donne la latence du bot"""
    latency = round(bot.latency * 1000)  # Convertir la latence en ms
    await ctx.send(f"🏓 **Pong!**\nLa latence du bot est de {latency} ms.")

# Commande personnalisée !uptime
@bot.command(name="uptime", help="Affiche l'uptime du bot")
async def uptime(ctx):
    """Affiche l'uptime du bot"""
    global start_time

    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    await ctx.send(f"⏳ Bot uptime: {hours}h {minutes}m {seconds}s")

# Commande personnalisée !help
@bot.command(name="help")
async def custom_help(ctx):
    """Affiche toutes les commandes disponibles"""
    msg = (
        "📖 **Commandes disponibles :**\n\n"
        
        "🟢 **Commandes système :**\n"
        "🟢 `!status` → Statut détaillé du cluster\n"
        "🎮 `!guess` → Jeu de devinette sur les stats du cluster\n\n"
        
        "💻 **Commandes de sécurité :**\n"
        "🔥 `!ipthreats` → IPs suspectes : top 5, récentes, pays actifs\n"
        "📖 `!ipinfo` → Info détaillée sur une IP ciblée\n\n"
        
        "📊 **Commandes de monitoring :**\n"
        "📊 `!dashboard` → Lien vers Grafana\n"
        "📅 `!daily` → Rapport complet du cluster\n\n"
        
        "⏳ **Commandes utilitaires :**\n"
        "⏳ `!uptime` → Affiche l'uptime du bot\n"
        "🕰 `!time` → Affiche l'heure actuelle\n"
        "🏓 `!ping` → Répond avec 'Pong!' et donne la latence du bot\n"
        "🖥 `!serverinfo` → Informations sur le serveur Discord\n"
    )
    
    await ctx.send(msg)

# Charger les modules de commandes externes (grafana, ipthreats, status, scheduler, games)
from modules import commands_status, commands_ipthreats, commands_grafana

# Enregistrer les commandes des modules externes
commands_status.register(bot)  # Commandes de statut du cluster
commands_ipthreats.register(bot)  # Commandes pour les IPs suspectes
commands_grafana.register(bot)  # Commandes pour Grafana

# Lancer le bot avec le token
bot.run(TOKEN)
