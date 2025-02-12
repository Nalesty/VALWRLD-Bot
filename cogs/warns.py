import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "data/warnings.json"
        self.warnings = {}
        self.load_warnings()
        
    def load_warnings(self):
        """Charger les avertissements depuis le fichier JSON"""
        try:
            with open(self.warnings_file, 'r') as f:
                self.warnings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.warnings = {}
            self.save_warnings()

    def save_warnings(self):
        """Sauvegarder les avertissements dans le fichier JSON"""
        with open(self.warnings_file, 'w') as f:
            json.dump(self.warnings, f, indent=4)

    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str):
        """Donner un avertissement à un membre"""
        if membre.bot:
            return await interaction.response.send_message("❌ Impossible d'avertir un bot.", ephemeral=True)
            
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ Vous ne pouvez pas avertir ce membre car son rôle est supérieur ou égal au vôtre.",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)
        user_id = str(membre.id)
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
            
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []
            
        warning = {
            "reason": raison,
            "moderator": str(interaction.user.id),
            "timestamp": datetime.now().isoformat()
        }
        
        self.warnings[guild_id][user_id].append(warning)
        self.save_warnings()
        
        # Créer l'embed
        embed = discord.Embed(
            title="⚠️ Avertissement",
            description=f"{membre.mention} a reçu un avertissement",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Raison", value=raison)
        embed.add_field(
            name="Avertissements totaux",
            value=str(len(self.warnings[guild_id][user_id])),
            inline=False
        )
        
        # Vérifier le nombre d'avertissements pour les sanctions automatiques
        warn_count = len(self.warnings[guild_id][user_id])
        
        if warn_count >= 5:  # Ban après 5 avertissements
            try:
                await membre.ban(reason=f"5 avertissements accumulés - Dernier: {raison}")
                embed.add_field(
                    name="Sanction automatique",
                    value="Le membre a été banni pour avoir accumulé 5 avertissements.",
                    inline=False
                )
            except discord.Forbidden:
                embed.add_field(
                    name="⚠️ Erreur",
                    value="Impossible de bannir le membre automatiquement.",
                    inline=False
                )
        elif warn_count >= 3:  # Kick après 3 avertissements
            try:
                await membre.kick(reason=f"3 avertissements accumulés - Dernier: {raison}")
                embed.add_field(
                    name="Sanction automatique",
                    value="Le membre a été expulsé pour avoir accumulé 3 avertissements.",
                    inline=False
                )
            except discord.Forbidden:
                embed.add_field(
                    name="⚠️ Erreur",
                    value="Impossible d'expulser le membre automatiquement.",
                    inline=False
                )
                
        await interaction.response.send_message(embed=embed)
        
        # DM au membre
        try:
            await membre.send(
                f"⚠️ Vous avez reçu un avertissement sur {interaction.guild.name}\n"
                f"Raison: {raison}\n"
                f"C'est votre {warn_count}e avertissement."
            )
        except discord.Forbidden:
            pass

    @app_commands.command(name="warnings", description="Voir les avertissements d'un membre")
    @app_commands.default_permissions(moderate_members=True)
    async def view_warnings(self, interaction: discord.Interaction, membre: discord.Member):
        """Voir les avertissements d'un membre"""
        guild_id = str(interaction.guild.id)
        user_id = str(membre.id)
        
        if guild_id not in self.warnings or user_id not in self.warnings[guild_id]:
            return await interaction.response.send_message(
                f"✅ {membre.display_name} n'a aucun avertissement.",
                ephemeral=True
            )
            
        warnings = self.warnings[guild_id][user_id]
        
        embed = discord.Embed(
            title=f"Avertissements de {membre.display_name}",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        
        for i, warning in enumerate(warnings, 1):
            moderator = interaction.guild.get_member(int(warning["moderator"]))
            mod_name = moderator.display_name if moderator else "Modérateur inconnu"
            timestamp = datetime.fromisoformat(warning["timestamp"])
            
            embed.add_field(
                name=f"Avertissement #{i}",
                value=f"**Raison:** {warning['reason']}\n"
                      f"**Modérateur:** {mod_name}\n"
                      f"**Date:** <t:{int(timestamp.timestamp())}:F>",
                inline=False
            )
            
        embed.set_thumbnail(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removewarn", description="Retirer un avertissement")
    @app_commands.default_permissions(moderate_members=True)
    async def remove_warning(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        numero: int
    ):
        """Retirer un avertissement spécifique"""
        guild_id = str(interaction.guild.id)
        user_id = str(membre.id)
        
        if (guild_id not in self.warnings or
            user_id not in self.warnings[guild_id] or
            not self.warnings[guild_id][user_id]):
            return await interaction.response.send_message(
                f"❌ {membre.display_name} n'a aucun avertissement.",
                ephemeral=True
            )
            
        if numero < 1 or numero > len(self.warnings[guild_id][user_id]):
            return await interaction.response.send_message(
                "❌ Numéro d'avertissement invalide.",
                ephemeral=True
            )
            
        removed_warning = self.warnings[guild_id][user_id].pop(numero - 1)
        self.save_warnings()
        
        embed = discord.Embed(
            title="✅ Avertissement retiré",
            description=f"Un avertissement a été retiré de {membre.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="Raison originale",
            value=removed_warning["reason"],
            inline=False
        )
        embed.add_field(
            name="Avertissements restants",
            value=str(len(self.warnings[guild_id][user_id])),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Warnings(bot))
