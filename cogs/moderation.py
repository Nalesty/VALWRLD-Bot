import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Expulser un membre du serveur")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Vous ne pouvez pas expulser ce membre car son rôle est supérieur ou égal au vôtre.", ephemeral=True)

        await membre.kick(reason=raison)
        embed = discord.Embed(
            title="👢 Membre expulsé",
            description=f"{membre.mention} a été expulsé par {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        if raison:
            embed.add_field(name="Raison", value=raison)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Bannir un membre du serveur")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Vous ne pouvez pas bannir ce membre car son rôle est supérieur ou égal au vôtre.", ephemeral=True)

        await membre.ban(reason=raison, delete_message_days=1)
        embed = discord.Embed(
            title="🔨 Membre banni",
            description=f"{membre.mention} a été banni par {interaction.user.mention}",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        if raison:
            embed.add_field(name="Raison", value=raison)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="temprole", description="Ajouter un rôle temporairement à un membre")
    @app_commands.default_permissions(manage_roles=True)
    async def temprole(self, interaction: discord.Interaction, membre: discord.Member, role: discord.Role, duree: str):
        try:
            # Conversion de la durée (format: 1h, 2d, etc.)
            unit = duree[-1].lower()
            value = int(duree[:-1])

            if unit == 'h':
                delta = timedelta(hours=value)
            elif unit == 'd':
                delta = timedelta(days=value)
            else:
                return await interaction.response.send_message("❌ Format de durée invalide. Utilisez h pour les heures ou d pour les jours (ex: 2h, 1d)", ephemeral=True)

            await membre.add_roles(role)
            embed = discord.Embed(
                title="✨ Rôle temporaire ajouté",
                description=f"Le rôle {role.mention} a été ajouté à {membre.mention} pour {duree}",
                color=role.color,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)

            # Attendre la durée spécifiée puis retirer le rôle
            await asyncio.sleep(delta.total_seconds())
            if role in membre.roles:  # Vérifier si le membre a toujours le rôle
                await membre.remove_roles(role)
                await interaction.channel.send(f"Le rôle {role.mention} a été retiré de {membre.mention} (durée expirée)")

        except ValueError:
            await interaction.response.send_message("❌ Format de durée invalide", ephemeral=True)

    @app_commands.command(name="move", description="Déplacer un salon dans une autre catégorie")
    @app_commands.default_permissions(manage_channels=True)
    async def move_channel(self, interaction: discord.Interaction, salon: discord.TextChannel, categorie: discord.CategoryChannel):
        ancien_nom = salon.name
        ancienne_categorie = salon.category

        await salon.edit(category=categorie)
        embed = discord.Embed(
            title="📦 Salon déplacé",
            description=f"Le salon {salon.mention} a été déplacé",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Ancienne catégorie", value=ancienne_categorie.name if ancienne_categorie else "Aucune")
        embed.add_field(name="Nouvelle catégorie", value=categorie.name)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="copyemoji", description="Copier un emoji d'un autre serveur")
    @app_commands.default_permissions(manage_emojis=True)
    async def copy_emoji(self, interaction: discord.Interaction, emoji: str):
        try:
            # Vérifier si c'est un emoji personnalisé
            if not emoji.startswith('<') or not emoji.endswith('>'):
                return await interaction.response.send_message("❌ Veuillez fournir un emoji personnalisé valide", ephemeral=True)

            # Extraire l'ID et le nom de l'emoji
            emoji_id = int(emoji.split(':')[-1][:-1])
            emoji_name = emoji.split(':')[1]

            # Récupérer l'URL de l'emoji
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"

            # Télécharger et créer l'emoji
            async with self.bot.session.get(emoji_url) as resp:
                if resp.status == 200:
                    emoji_bytes = await resp.read()
                    new_emoji = await interaction.guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)

                    embed = discord.Embed(
                        title="✨ Emoji copié",
                        description=f"L'emoji a été copié avec succès: {new_emoji}",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("❌ Impossible de télécharger l'emoji", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue: {str(e)}", ephemeral=True)

async def setup(bot):
    # Créer une session HTTP pour le bot
    if not hasattr(bot, 'session'):
        bot.session = aiohttp.ClientSession()
    await bot.add_cog(ModerationCog(bot))