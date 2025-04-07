import random
from discord.ext import commands
import asyncio

# Liste des questions du jeu
questions = [
    {"question": "Devinez le nombre de nœuds UP dans le cluster", "answer": 12, "range": (10, 15)},
    {"question": "Devinez la température maximale du cluster (°C)", "answer": 42, "range": (35, 50)},
    {"question": "Devinez la charge moyenne du cluster", "answer": 0.6, "range": (0.4, 0.8)},
]

# Initialiser le jeu
async def register(bot):
    @bot.command(name="guess")
    async def guess(ctx):
        """Démarre un jeu où les utilisateurs doivent deviner des stats du cluster"""
        question = random.choice(questions)  # Choisir une question aléatoire
        await ctx.send(f"🎮 **Jeu du Cluster !**\n\n{question['question']}\nIndice : Le nombre est entre {question['range'][0]} et {question['range'][1]}.")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        # Essais de l'utilisateur
        tries = 3
        while tries > 0:
            try:
                # Attendre la réponse de l'utilisateur
                response = await bot.wait_for("message", check=check, timeout=30)
                user_guess = float(response.content)

                # Vérifier si la réponse est correcte
                if user_guess == question["answer"]:
                    await ctx.send(f"✅ Bravo {ctx.author.mention}, tu as trouvé la bonne réponse ! La réponse était bien {question['answer']}.")
                    break
                elif user_guess < question["answer"]:
                    await ctx.send("❌ Trop bas ! Essaie un nombre plus élevé.")
                elif user_guess > question["answer"]:
                    await ctx.send("❌ Trop élevé ! Essaie un nombre plus bas.")
                tries -= 1
            except ValueError:
                await ctx.send("🚫 Ce n'est pas un nombre valide. Essaye encore avec un nombre.")
            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé, tu as perdu ! La réponse correcte était : {question['answer']}.")
                break

        if tries == 0:
            await ctx.send(f"⏳ Le jeu est terminé, la réponse était {question['answer']}. Essaie encore plus tard !")
