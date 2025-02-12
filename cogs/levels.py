import discord
from discord import app_commands
from discord.ext import commands
import json
import math
import os
from datetime import datetime

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels_file = "data/levels.json"
        self.xp_per_message = 15
        self.xp_cooldown = 60  # Secondes entre chaque gain d'XP
        self.user_cooldowns = {}
        self.load_levels()
        
        # Créer le dossier data s'il n'existe pas
        if not os.path.exists('data'):
            os.makedirs('data')
        
    def load_levels(self):
        """Charger les données des niveaux depuis le fichier JSON"""
        try:
            with open(self.levels_file, 'r') as f:
                self.levels = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.levels = {}
            self.save_levels()

    def save_levels(self):
        """Sauvegarder les données des niveaux dans le fichier JSON"""
        with open(self.levels_file, 'w') as f:
            json.dump(self.levels, f, indent=4)

    def get_level_xp(self, level):
        """Calculer l'XP nécessaire pour le niveau suivant"""
        return 5 * (level ** 2) + 50 * level + 100

    def get_level_from_xp(self, xp):
        """Calculer le niveau en fonction de l'XP totale"""
        level = 0
        while xp >= self.get_level_xp(level):
            xp -= self.get_level_xp(level)
            level += 1
        return level

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Vérifier le cooldown
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        current_time = datetime.now().timestamp()
        
        if guild_id not in self.levels:
            self.levels[guild_id] = {}
            
        if user_id not in self.levels[guild_id]:
            self.levels[guild_id][user_id] = {"xp": 0, "level": 0, "last_message": 0}

        last_message = self.levels[guild_id][user_id]["last_message"]
        
        if current_time - last_message < self.xp_cooldown:
            return

        # Ajouter XP
        old_level = self.levels[guild_id][user_id]["level"]
        self.levels[guild_id][user_id]["xp"] += self.xp_per_message
        self.levels[guild_id][user_id]["last_message"] = current_time
        
        # Calculer nouveau niveau
        new_level = self.get_level_from_xp(self.levels[guild_id][user_id]["xp"])
        self.levels[guild_id][user_id]["level"] = new_level
        
        # Envoyer message de niveau up
        if new_level > old_level:
            embed = discord.Embed(
                title="🎉 Niveau supérieur !",
                description=f"Bravo {message.author.mention} ! Tu as atteint le niveau {new_level} !",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
        
        self.save_levels()

    @app_commands.command(name="rank", description="Afficher votre niveau ou celui d'un autre membre")
    async def rank(self, interaction: discord.Interaction, membre: discord.Member = None):
        member = membre or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.levels or user_id not in self.levels[guild_id]:
            return await interaction.response.send_message(
                f"{member.display_name} n'a pas encore de niveau sur ce serveur.",
                ephemeral=True
            )
            
        user_data = self.levels[guild_id][user_id]
        current_xp = user_data["xp"]
        level = user_data["level"]
        xp_for_next = self.get_level_xp(level)
        
        progress = (current_xp / xp_for_next) * 100
        progress_bar = "▰" * int(progress/10) + "▱" * (10-int(progress/10))
        
        embed = discord.Embed(
            title=f"Niveau de {member.display_name}",
            color=member.color
        )
        embed.add_field(name="Niveau", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{current_xp}/{xp_for_next}", inline=True)
        embed.add_field(name="Progression", value=f"{progress_bar} ({progress:.1f}%)", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Afficher le classement des membres")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.levels:
            return await interaction.response.send_message(
                "Aucun classement disponible pour le moment.",
                ephemeral=True
            )
            
        # Trier les membres par XP
        sorted_users = sorted(
            self.levels[guild_id].items(),
            key=lambda x: (x[1]["level"], x[1]["xp"]),
            reverse=True
        )[:10]  # Top 10
        
        embed = discord.Embed(
            title=f"🏆 Classement de {interaction.guild.name}",
            color=discord.Color.gold()
        )
        
        for index, (user_id, data) in enumerate(sorted_users, 1):
            member = interaction.guild.get_member(int(user_id))
            if member:
                embed.add_field(
                    name=f"{index}. {member.display_name}",
                    value=f"Niveau {data['level']} • {data['xp']} XP",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
