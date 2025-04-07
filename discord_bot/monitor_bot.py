import os
import requests
import subprocess
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env.bot
load_dotenv(dotenv_path='/home/foxink/opicluster_monitoring/.env.bot')

# Récupérer le webhook à partir des variables d'environnement
WEBHOOK_URL = os.getenv("WEBHOOK_GENERAL")

# ID de l'utilisateur Discord (remplace par l'ID réel, pas le nom)
DISCORD_USER_ID = "1215791728993370293"  # Remplace par l'ID numérique réel de ton utilisateur

# Nom du container Docker
CONTAINER_NAME = "discord_bot"  # Remplace par le nom de ton container Docker

def check_container_status():
    """Vérifie si le container est en marche"""
    try:
        # Utilise docker inspect pour vérifier si le container est "running"
        result = subprocess.run(
            ["sudo", "docker", "inspect", "--format", "{{.State.Status}}", CONTAINER_NAME], 
            capture_output=True, text=True
        )
        
        container_status = result.stdout.strip()  # Récupère le statut du container
        
        if container_status == "running":
            print(f"Container {CONTAINER_NAME} is running.")
            return True  # Le container est en marche
        else:
            print(f"Container {CONTAINER_NAME} is not running. Status: {container_status}")
            return False  # Le container est down
        
    except Exception as e:
        print(f"Erreur lors de la vérification du container: {e}")
        return False  # En cas d'erreur, on considère que le bot est down

def send_discord_notification(message):
    """Envoie une notification à Discord via le Webhook"""
    payload = {
        "content": f"<@{DISCORD_USER_ID}> {message}",  # Mentionne l'utilisateur en utilisant son ID
        "username": "Bot Monitoring",
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)  # Utiliser l'URL sans l'encodage
        response.raise_for_status()  # Vérifie si la requête a réussi
        print("Notification envoyée à Discord")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi de la notification: {e}")

def monitor():
    """Surveille l'état du container et envoie une notification si nécessaire"""
    if not check_container_status():
        send_discord_notification("🚨 Le bot est **DOWN** ! Veuillez vérifier.")
    else:
        print("Le bot est UP. Aucun message envoyé.")  # Pas de message envoyé si le bot est UP

if __name__ == "__main__":
    monitor()
