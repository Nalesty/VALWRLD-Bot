import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Affiche les informations du serveur")
    async def info(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Récupération des statistiques
        total_members = len(guild.members)
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        # Création de l'embed
        embed = discord.Embed(
            title=f"📊 Informations sur {guild.name}",
            color=discord.Color.blue()
        )
        
        # Ajout des champs
        embed.add_field(
            name="👥 Membres",
            value=f"Total: {total_members}\nEn ligne: {online_members}\nBots: {bot_count}",
            inline=True
        )
        embed.add_field(
            name="📝 Canaux",
            value=f"Total: {len(guild.channels)}\nTextuels: {text_channels}\nVocaux: {voice_channels}",
            inline=True
        )
        embed.add_field(
            name="🎭 Rôles",
            value=str(len(guild.roles)),
            inline=True
        )
        embed.add_field(
            name="📅 Créé le",
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=True
        )
        embed.add_field(
            name="👑 Propriétaire",
            value=guild.owner.mention,
            inline=True
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(InfoCog(bot))
