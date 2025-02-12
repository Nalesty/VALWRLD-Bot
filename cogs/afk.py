import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_file = "data/afk.json"
        self.afk_users = {}
        self.max_afk_duration = timedelta(days=7)  # Durée maximale AFK
        self.load_afk()

    def load_afk(self):
        """Charger les données AFK"""
        try:
            # Créer le dossier data s'il n'existe pas
            if not os.path.exists('data'):
                os.makedirs('data')
                print(f"✅ Dossier data créé avec succès")

            if os.path.exists(self.afk_file):
                with open(self.afk_file, 'r', encoding='utf-8') as f:
                    self.afk_users = json.load(f)
                    print(f"✅ Données AFK chargées : {len(self.afk_users)} utilisateurs")
            else:
                # Créer le fichier s'il n'existe pas
                self.afk_users = {}
                self.save_afk()
                print(f"✅ Nouveau fichier AFK créé")

        except Exception as e:
            print(f"❌ Erreur lors du chargement des données AFK : {str(e)}")
            self.afk_users = {}

    def save_afk(self):
        """Sauvegarder les données AFK"""
        try:
            with open(self.afk_file, 'w', encoding='utf-8') as f:
                json.dump(self.afk_users, f, indent=4, ensure_ascii=False)
                print(f"✅ Données AFK sauvegardées")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des données AFK : {str(e)}")

    @app_commands.command(name="afk", description="Signaler votre absence")
    async def set_afk(self, interaction: discord.Interaction, raison: str = "AFK"):
        """Se mettre en mode AFK"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        if guild_id not in self.afk_users:
            self.afk_users[guild_id] = {}

        self.afk_users[guild_id][user_id] = {
            "reason": raison,
            "timestamp": datetime.now().isoformat()
        }
        self.save_afk()

        # Modifier le surnom pour indiquer AFK
        try:
            original_name = interaction.user.display_name
            if not original_name.startswith("[AFK] "):
                await interaction.user.edit(nick=f"[AFK] {original_name}")
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"✅ Vous êtes maintenant AFK - {raison}",
            ephemeral=True
        )

    @app_commands.command(name="removeafk", description="Retirer manuellement votre statut AFK")
    async def remove_afk(self, interaction: discord.Interaction):
        """Retirer manuellement le statut AFK"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        if guild_id in self.afk_users and user_id in self.afk_users[guild_id]:
            del self.afk_users[guild_id][user_id]
            self.save_afk()

            try:
                if interaction.user.display_name.startswith("[AFK] "):
                    await interaction.user.edit(nick=interaction.user.display_name[6:])
            except discord.Forbidden:
                pass

            await interaction.response.send_message(
                "✅ Votre statut AFK a été retiré !",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Vous n'êtes pas AFK !",
                ephemeral=True
            )

    @app_commands.command(name="afklist", description="Voir la liste des membres AFK")
    async def list_afk(self, interaction: discord.Interaction):
        """Afficher la liste des membres AFK"""
        guild_id = str(interaction.guild.id)

        if guild_id not in self.afk_users or not self.afk_users[guild_id]:
            return await interaction.response.send_message(
                "Aucun membre n'est AFK actuellement.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="💤 Membres AFK",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        for user_id, afk_data in self.afk_users[guild_id].items():
            member = interaction.guild.get_member(int(user_id))
            if member:
                timestamp = datetime.fromisoformat(afk_data["timestamp"])
                time_delta = datetime.now() - timestamp

                hours = time_delta.seconds // 3600
                minutes = (time_delta.seconds % 3600) // 60

                time_str = ""
                if time_delta.days > 0:
                    time_str = f"{time_delta.days}j "
                if hours > 0:
                    time_str += f"{hours}h "
                time_str += f"{minutes}min"

                embed.add_field(
                    name=member.display_name,
                    value=f"Raison: {afk_data['reason']}\nDepuis: {time_str}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Gérer les messages des utilisateurs AFK"""
        if message.author.bot:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        # Vérifier si l'auteur était AFK
        if guild_id in self.afk_users and user_id in self.afk_users[guild_id]:
            # Vérifier si la durée maximale est dépassée
            timestamp = datetime.fromisoformat(self.afk_users[guild_id][user_id]["timestamp"])
            if datetime.now() - timestamp > self.max_afk_duration:
                del self.afk_users[guild_id][user_id]
                self.save_afk()
                await message.channel.send(
                    f"⏰ {message.author.mention}, votre statut AFK a été retiré car il a dépassé la durée maximale de 7 jours.",
                    delete_after=10
                )
            else:
                # Retirer le statut AFK normalement
                del self.afk_users[guild_id][user_id]
                self.save_afk()

                try:
                    if message.author.display_name.startswith("[AFK] "):
                        await message.author.edit(nick=message.author.display_name[6:])
                except discord.Forbidden:
                    pass

                await message.channel.send(
                    f"👋 Bon retour {message.author.mention} !",
                    delete_after=5
                )

        # Vérifier les mentions d'utilisateurs AFK
        for mention in message.mentions:
            mentioned_id = str(mention.id)
            if guild_id in self.afk_users and mentioned_id in self.afk_users[guild_id]:
                afk_data = self.afk_users[guild_id][mentioned_id]
                timestamp = datetime.fromisoformat(afk_data["timestamp"])
                time_delta = datetime.now() - timestamp

                time_str = ""
                if time_delta.days > 0:
                    time_str = f"{time_delta.days}j "
                hours = time_delta.seconds // 3600
                minutes = (time_delta.seconds % 3600) // 60

                if hours > 0:
                    time_str += f"{hours}h "
                time_str += f"{minutes}min"

                await message.channel.send(
                    f"💤 {mention.display_name} est AFK depuis {time_str} - {afk_data['reason']}",
                    delete_after=10
                )

async def setup(bot):
    await bot.add_cog(AFK(bot))