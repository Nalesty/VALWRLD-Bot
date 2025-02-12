import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import json
import os

class AntiGhostPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cached_messages = {}
        self.ghost_pings_file = "data/ghost_pings.json"
        self.load_ghost_pings()

    def load_ghost_pings(self):
        """Charger l'historique des ghost pings"""
        try:
            # Créer le dossier data s'il n'existe pas
            if not os.path.exists('data'):
                os.makedirs('data')
                print(f"✅ Dossier data créé avec succès")

            if os.path.exists(self.ghost_pings_file):
                with open(self.ghost_pings_file, 'r', encoding='utf-8') as f:
                    self.ghost_pings = json.load(f)
                    print(f"✅ Ghost pings chargés : {len(self.ghost_pings)} enregistrements")
            else:
                # Créer le fichier s'il n'existe pas
                self.ghost_pings = {}
                self.save_ghost_pings()
                print(f"✅ Nouveau fichier de ghost pings créé")

        except Exception as e:
            print(f"❌ Erreur lors du chargement des ghost pings : {str(e)}")
            self.ghost_pings = {}

    def save_ghost_pings(self):
        """Sauvegarder l'historique des ghost pings"""
        try:
            with open(self.ghost_pings_file, 'w', encoding='utf-8') as f:
                json.dump(self.ghost_pings, f, indent=4, ensure_ascii=False)
                print(f"✅ Ghost pings sauvegardés")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des ghost pings : {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Mettre en cache les messages contenant des mentions"""
        if message.mentions or message.role_mentions:
            self.cached_messages[message.id] = {
                "content": message.content,
                "author": str(message.author),
                "author_id": str(message.author.id),
                "mentions": [str(user.id) for user in message.mentions],
                "role_mentions": [str(role.id) for role in message.role_mentions],
                "timestamp": datetime.now().isoformat()
            }

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Détecter les ghost pings"""
        if message.id in self.cached_messages:
            cached = self.cached_messages[message.id]
            guild_id = str(message.guild.id)

            if guild_id not in self.ghost_pings:
                self.ghost_pings[guild_id] = []

            # Enregistrer le ghost ping
            ghost_ping = {
                "author": cached["author"],
                "author_id": cached["author_id"],
                "content": cached["content"],
                "mentions": cached["mentions"],
                "role_mentions": cached["role_mentions"],
                "timestamp": cached["timestamp"],
                "channel_id": str(message.channel.id)
            }

            self.ghost_pings[guild_id].append(ghost_ping)
            self.save_ghost_pings()

            # Envoyer une alerte dans le salon
            embed = discord.Embed(
                title="👻 Ghost Ping Détecté !",
                description=f"Un message avec des mentions a été supprimé par {ghost_ping['author']}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Message", value=ghost_ping["content"])

            # Mentionner les utilisateurs concernés
            mentions = []
            for user_id in ghost_ping["mentions"]:
                mentions.append(f"<@{user_id}>")
            for role_id in ghost_ping["role_mentions"]:
                mentions.append(f"<@&{role_id}>")

            if mentions:
                embed.add_field(name="Mentions", value=", ".join(mentions))

            await message.channel.send(embed=embed)

            # Nettoyer le cache
            del self.cached_messages[message.id]

    @app_commands.command(name="ghostpings", description="Voir l'historique des ghost pings")
    async def view_ghost_pings(self, interaction: discord.Interaction):
        """Afficher l'historique des ghost pings"""
        guild_id = str(interaction.guild.id)

        if guild_id not in self.ghost_pings or not self.ghost_pings[guild_id]:
            return await interaction.response.send_message(
                "Aucun ghost ping n'a été détecté sur ce serveur.",
                ephemeral=True
            )

        # Créer un embed avec les 10 derniers ghost pings
        embed = discord.Embed(
            title="📜 Historique des Ghost Pings",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        for ping in self.ghost_pings[guild_id][-10:]:
            mentions = []
            for user_id in ping["mentions"]:
                mentions.append(f"<@{user_id}>")
            for role_id in ping["role_mentions"]:
                mentions.append(f"<@&{role_id}>")

            embed.add_field(
                name=f"Par {ping['author']} le {ping['timestamp']}",
                value=f"Message: {ping['content']}\nMentions: {', '.join(mentions)}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AntiGhostPing(bot))