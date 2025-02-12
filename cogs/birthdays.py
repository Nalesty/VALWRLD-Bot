import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import asyncio

class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays_file = "data/birthdays.json"
        self.load_birthdays()
        self.birthday_check.start()

    def load_birthdays(self):
        """Charger les données des anniversaires"""
        try:
            with open(self.birthdays_file, 'r') as f:
                self.birthdays = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.birthdays = {}
            self.save_birthdays()

    def save_birthdays(self):
        """Sauvegarder les données des anniversaires"""
        with open(self.birthdays_file, 'w') as f:
            json.dump(self.birthdays, f, indent=4)

    @app_commands.command(name="setbirthday", description="Définir votre date d'anniversaire")
    async def set_birthday(
        self,
        interaction: discord.Interaction,
        jour: app_commands.Range[int, 1, 31],
        mois: app_commands.Range[int, 1, 12]
    ):
        """Définir sa date d'anniversaire"""
        guild_id = str(interaction.guild.id)
        if guild_id not in self.birthdays:
            self.birthdays[guild_id] = {
                "channel": None,
                "users": {}
            }

        self.birthdays[guild_id]["users"][str(interaction.user.id)] = {
            "day": jour,
            "month": mois
        }

        self.save_birthdays()

        # Mettre à jour l'embed des anniversaires
        await self.update_birthday_embed(interaction.guild)

        await interaction.response.send_message(
            f"✅ Votre anniversaire a été enregistré pour le {jour}/{mois} !",
            ephemeral=True
        )

    @app_commands.command(name="setupbirthdays", description="Configurer le système d'anniversaires")
    @app_commands.default_permissions(administrator=True)
    async def setup_birthdays(self, interaction: discord.Interaction, salon: discord.TextChannel):
        """Configurer le salon des anniversaires"""
        guild_id = str(interaction.guild.id)

        if guild_id not in self.birthdays:
            self.birthdays[guild_id] = {"users": {}}

        self.birthdays[guild_id]["channel"] = str(salon.id)
        self.save_birthdays()

        # Créer l'embed initial des anniversaires
        await self.update_birthday_embed(interaction.guild)

        await interaction.response.send_message(
            f"✅ Le salon des anniversaires a été configuré dans {salon.mention} !",
            ephemeral=True
        )

    async def update_birthday_embed(self, guild):
        """Mettre à jour l'embed des anniversaires"""
        guild_id = str(guild.id)
        if guild_id not in self.birthdays or not self.birthdays[guild_id].get("channel"):
            return

        channel = self.bot.get_channel(int(self.birthdays[guild_id]["channel"]))
        if not channel:
            return

        # Trier les anniversaires par mois et jour
        sorted_birthdays = []
        for user_id, data in self.birthdays[guild_id]["users"].items():
            member = guild.get_member(int(user_id))
            if member:
                sorted_birthdays.append((data["month"], data["day"], member))
        sorted_birthdays.sort()

        # Créer l'embed
        embed = discord.Embed(
            title="🎂 Calendrier des anniversaires",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        current_month = 0
        month_text = ""

        for month, day, member in sorted_birthdays:
            if month != current_month:
                if month_text:
                    embed.add_field(
                        name=f"📅 {datetime(2000, current_month, 1).strftime('%B')}",
                        value=month_text,
                        inline=False
                    )
                current_month = month
                month_text = ""

            month_text += f"• {day} - {member.mention}\n"

        if month_text:
            embed.add_field(
                name=f"📅 {datetime(2000, current_month, 1).strftime('%B')}",
                value=month_text,
                inline=False
            )

        # Supprimer l'ancien embed s'il existe
        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds:
                await message.delete()
                break

        await channel.send(embed=embed)

    @tasks.loop(hours=24)
    async def birthday_check(self):
        """Vérifier les anniversaires quotidiennement"""
        now = datetime.now()

        for guild_id, guild_data in self.birthdays.items():
            if not guild_data.get("channel"):
                continue

            channel = self.bot.get_channel(int(guild_data["channel"]))
            if not channel:
                continue

            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            for user_id, birthday in guild_data["users"].items():
                if birthday["day"] == now.day and birthday["month"] == now.month:
                    member = guild.get_member(int(user_id))
                    if member:
                        embed = discord.Embed(
                            title="🎉 Joyeux anniversaire !",
                            description=f"Souhaitez un joyeux anniversaire à {member.mention} !",
                            color=discord.Color.gold(),
                            timestamp=now
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        await channel.send(content=member.mention, embed=embed)

    @birthday_check.before_loop
    async def before_birthday_check(self):
        """Attendre que le bot soit prêt avant de commencer les vérifications"""
        await self.bot.wait_until_ready()

        # Attendre jusqu'à minuit pour commencer
        now = datetime.now()
        if now.hour != 0:
            delta = datetime.combine(now.date() + timedelta(days=1), datetime.min.time()) - now
            await asyncio.sleep(delta.total_seconds())

async def setup(bot):
    await bot.add_cog(Birthdays(bot))