import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_file = "data/welcome.json"
        self.load_config()
        
    def load_config(self):
        """Charger la configuration des messages de bienvenue"""
        try:
            with open(self.welcome_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}
            self.save_config()

    def save_config(self):
        """Sauvegarder la configuration des messages de bienvenue"""
        with open(self.welcome_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gérer l'arrivée d'un nouveau membre"""
        guild_id = str(member.guild.id)
        if guild_id not in self.config or not self.config[guild_id].get("welcome_channel"):
            return

        channel = self.bot.get_channel(int(self.config[guild_id]["welcome_channel"]))
        if not channel:
            return

        message = self.config[guild_id].get("welcome_message", "Bienvenue {user} sur {server} !")
        message = message.format(
            user=member.mention,
            server=member.guild.name,
            membercount=member.guild.member_count
        )

        embed = discord.Embed(
            title="👋 Nouveau membre !",
            description=message,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Gérer les boosts du serveur"""
        # Vérifier si le membre vient de boost
        if not before.premium_since and after.premium_since:
            guild_id = str(after.guild.id)
            if guild_id not in self.config or not self.config[guild_id].get("boost_channel"):
                return

            channel = self.bot.get_channel(int(self.config[guild_id]["boost_channel"]))
            if not channel:
                return

            message = self.config[guild_id].get("boost_message", "Merci {user} d'avoir boosté {server} !")
            message = message.format(
                user=after.mention,
                server=after.guild.name,
                boostcount=after.guild.premium_subscription_count
            )

            embed = discord.Embed(
                title="🚀 Nouveau boost !",
                description=message,
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(embed=embed)

    @app_commands.command(name="setupwelcome", description="Configurer les messages de bienvenue")
    @app_commands.default_permissions(administrator=True)
    async def setup_welcome(
        self,
        interaction: discord.Interaction,
        salon_bienvenue: discord.TextChannel,
        salon_boost: discord.TextChannel,
        message_bienvenue: str = None,
        message_boost: str = None
    ):
        """Configurer les messages de bienvenue et de boost"""
        guild_id = str(interaction.guild.id)
        
        self.config[guild_id] = {
            "welcome_channel": str(salon_bienvenue.id),
            "boost_channel": str(salon_boost.id),
            "welcome_message": message_bienvenue,
            "boost_message": message_boost
        }
        
        self.save_config()
        
        embed = discord.Embed(
            title="✅ Configuration sauvegardée",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="Salon de bienvenue",
            value=salon_bienvenue.mention,
            inline=True
        )
        embed.add_field(
            name="Salon de boost",
            value=salon_boost.mention,
            inline=True
        )
        if message_bienvenue:
            embed.add_field(
                name="Message de bienvenue",
                value=message_bienvenue,
                inline=False
            )
        if message_boost:
            embed.add_field(
                name="Message de boost",
                value=message_boost,
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="testwelcome", description="Tester le message de bienvenue")
    @app_commands.default_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        """Tester le message de bienvenue"""
        await self.on_member_join(interaction.user)
        await interaction.response.send_message("✅ Message de test envoyé !", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
