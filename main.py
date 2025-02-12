import os
import discord
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime

# Configuration du bot
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Chargement des cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Cog chargé : {filename[:-3]}')
                except Exception as e:
                    print(f'Erreur lors du chargement du cog {filename}: {str(e)}')

        await self.tree.sync()
        print(f'Commandes synchronisées')

bot = Bot()

# Événement: Bot prêt
@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="/help pour les commandes"
        )
    )

# Commande de base pour vérifier que le bot fonctionne
@bot.tree.command(name="ping", description="Vérifier la latence du bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! Latence: {round(bot.latency * 1000)}ms")

# Lancement du bot
if __name__ == "__main__":
    TOKEN = os.getenv('TOKEN')
    if not TOKEN:
        raise ValueError("Le token du bot n'est pas défini dans les variables d'environnement")

    # Création du dossier cogs s'il n'existe pas
    if not os.path.exists('cogs'):
        os.makedirs('cogs')

    bot.run(TOKEN)