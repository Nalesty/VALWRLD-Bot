import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp
from datetime import datetime
import asyncio

class StreamNotifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.streams_file = "data/streams.json"
        self.check_interval = 300  # 5 minutes
        self.load_streams()
        self.bg_task = self.bot.loop.create_task(self.check_streams())
        
    def load_streams(self):
        """Charger les configurations des streams depuis le fichier JSON"""
        try:
            with open(self.streams_file, 'r') as f:
                self.streams = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.streams = {}
            self.save_streams()

    def save_streams(self):
        """Sauvegarder les configurations des streams"""
        with open(self.streams_file, 'w') as f:
            json.dump(self.streams, f, indent=4)

    @app_commands.command(name="addstream", description="Ajouter une chaîne de streaming")
    @app_commands.describe(
        plateforme="La plateforme de streaming (twitch/youtube/facebook/tiktok)",
        channel_id="L'identifiant de votre chaîne"
    )
    async def add_stream(self, interaction: discord.Interaction, plateforme: str, channel_id: str):
        # Vérifier si l'utilisateur a le rôle requis
        guild_id = str(interaction.guild.id)
        if guild_id not in self.streams:
            self.streams[guild_id] = {
                "notification_channel": None,
                "allowed_role": None,
                "streamers": {}
            }

        if self.streams[guild_id]["allowed_role"]:
            role = interaction.guild.get_role(int(self.streams[guild_id]["allowed_role"]))
            if role not in interaction.user.roles:
                return await interaction.response.send_message(
                    "❌ Vous n'avez pas la permission d'ajouter une chaîne de streaming.",
                    ephemeral=True
                )

        # Ajouter la chaîne
        user_id = str(interaction.user.id)
        self.streams[guild_id]["streamers"][user_id] = {
            "platform": plateforme.lower(),
            "channel_id": channel_id,
            "last_stream": None
        }
        
        self.save_streams()
        await interaction.response.send_message(
            f"✅ Votre chaîne {plateforme} a été ajoutée avec succès !",
            ephemeral=True
        )

    @app_commands.command(name="setupstream", description="Configurer les notifications de stream")
    @app_commands.default_permissions(administrator=True)
    async def setup_stream(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        role: discord.Role
    ):
        """Configurer le salon de notification et le rôle autorisé"""
        guild_id = str(interaction.guild.id)
        
        self.streams[guild_id] = {
            "notification_channel": str(salon.id),
            "allowed_role": str(role.id),
            "streamers": {}
        }
        
        self.save_streams()
        await interaction.response.send_message(
            f"✅ Configuration sauvegardée !\n"
            f"Salon de notification : {salon.mention}\n"
            f"Rôle autorisé : {role.mention}",
            ephemeral=True
        )

    async def check_twitch_stream(self, channel_id):
        # Implémentation de la vérification Twitch
        # Nécessite une clé API Twitch
        pass

    async def check_youtube_stream(self, channel_id):
        # Implémentation de la vérification YouTube
        # Nécessite une clé API YouTube
        pass

    async def check_streams(self):
        """Tâche en arrière-plan pour vérifier les streams"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for guild_id, guild_data in self.streams.items():
                    if not guild_data["notification_channel"]:
                        continue

                    channel = self.bot.get_channel(int(guild_data["notification_channel"]))
                    if not channel:
                        continue

                    for user_id, streamer_data in guild_data["streamers"].items():
                        # Vérification en fonction de la plateforme
                        is_live = False
                        stream_title = ""
                        
                        if streamer_data["platform"] == "twitch":
                            is_live, stream_title = await self.check_twitch_stream(streamer_data["channel_id"])
                        elif streamer_data["platform"] == "youtube":
                            is_live, stream_title = await self.check_youtube_stream(streamer_data["channel_id"])
                        
                        # Si en stream et pas de notification récente
                        if is_live and streamer_data["last_stream"] != stream_title:
                            guild = self.bot.get_guild(int(guild_id))
                            member = guild.get_member(int(user_id))
                            
                            if member:
                                embed = discord.Embed(
                                    title="🎥 Stream en cours !",
                                    description=f"{member.mention} est en live !",
                                    color=discord.Color.purple(),
                                    timestamp=datetime.now()
                                )
                                embed.add_field(name="Titre", value=stream_title)
                                embed.add_field(name="Plateforme", value=streamer_data["platform"].capitalize())
                                
                                await channel.send(embed=embed)
                                self.streams[guild_id]["streamers"][user_id]["last_stream"] = stream_title
                                self.save_streams()

            except Exception as e:
                print(f"Erreur lors de la vérification des streams : {e}")
            
            await asyncio.sleep(self.check_interval)

    def cog_unload(self):
        """Nettoyer la tâche en arrière-plan lors du déchargement du cog"""
        self.bg_task.cancel()

async def setup(bot):
    await bot.add_cog(StreamNotifications(bot))
