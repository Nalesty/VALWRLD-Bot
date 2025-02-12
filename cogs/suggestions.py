import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import json
import os

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestions_file = "data/suggestions.json"
        self.load_suggestions()

    def load_suggestions(self):
        """Charger les configurations des suggestions"""
        try:
            with open(self.suggestions_file, 'r') as f:
                self.suggestions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.suggestions = {}
            self.save_suggestions()

    def save_suggestions(self):
        """Sauvegarder les configurations des suggestions"""
        with open(self.suggestions_file, 'w') as f:
            json.dump(self.suggestions, f, indent=4)

    @app_commands.command(name="suggestion", description="Soumettre une suggestion")
    async def submit_suggestion(self, interaction: discord.Interaction, suggestion: str):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.suggestions or not self.suggestions[guild_id].get("channel"):
            return await interaction.response.send_message(
                "❌ Le système de suggestions n'est pas configuré sur ce serveur.",
                ephemeral=True
            )

        channel = self.bot.get_channel(int(self.suggestions[guild_id]["channel"]))
        if not channel:
            return await interaction.response.send_message(
                "❌ Le salon de suggestions est introuvable.",
                ephemeral=True
            )

        # Créer l'embed de suggestion
        embed = discord.Embed(
            title="💡 Nouvelle Suggestion",
            description=suggestion,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )
        embed.set_footer(text=f"ID: {interaction.user.id}")

        # Envoyer la suggestion et ajouter les réactions
        message = await channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")

        # Si les fils de discussion sont activés
        if self.suggestions[guild_id].get("use_threads", False):
            await message.create_thread(name=f"Discussion: {suggestion[:50]}...")

        await interaction.response.send_message(
            "✅ Votre suggestion a été soumise avec succès !",
            ephemeral=True
        )

    @app_commands.command(name="setupsuggestions", description="Configurer le système de suggestions")
    @app_commands.default_permissions(administrator=True)
    async def setup_suggestions(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        utiliser_fils: bool = True,
        notifications_dm: bool = True
    ):
        """Configurer le système de suggestions"""
        guild_id = str(interaction.guild.id)
        
        self.suggestions[guild_id] = {
            "channel": str(salon.id),
            "use_threads": utiliser_fils,
            "dm_notifications": notifications_dm,
            "suggestions": {}
        }
        
        self.save_suggestions()
        
        await interaction.response.send_message(
            f"✅ Configuration sauvegardée !\n"
            f"Salon des suggestions : {salon.mention}\n"
            f"Fils de discussion : {'Activés' if utiliser_fils else 'Désactivés'}\n"
            f"Notifications DM : {'Activées' if notifications_dm else 'Désactivées'}",
            ephemeral=True
        )

    @app_commands.command(name="approve", description="Approuver une suggestion")
    @app_commands.default_permissions(administrator=True)
    async def approve_suggestion(
        self,
        interaction: discord.Interaction,
        message_id: str,
        commentaire: str = None
    ):
        """Approuver une suggestion"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.suggestions:
            return await interaction.response.send_message(
                "❌ Le système de suggestions n'est pas configuré sur ce serveur.",
                ephemeral=True
            )

        channel = self.bot.get_channel(int(self.suggestions[guild_id]["channel"]))
        if not channel:
            return await interaction.response.send_message(
                "❌ Le salon de suggestions est introuvable.",
                ephemeral=True
            )

        try:
            message = await channel.fetch_message(int(message_id))
            if not message.embeds:
                return await interaction.response.send_message(
                    "❌ Message invalide.",
                    ephemeral=True
                )

            embed = message.embeds[0]
            embed.color = discord.Color.green()
            
            if commentaire:
                embed.add_field(
                    name="✅ Approuvée par un administrateur",
                    value=commentaire
                )
            else:
                embed.add_field(
                    name="✅ Statut",
                    value="Approuvée par un administrateur"
                )

            await message.edit(embed=embed)
            
            # Notification DM si activée
            if self.suggestions[guild_id].get("dm_notifications"):
                user_id = int(embed.footer.text.split("ID: ")[1])
                user = interaction.guild.get_member(user_id)
                if user:
                    try:
                        dm_embed = discord.Embed(
                            title="✅ Suggestion Approuvée !",
                            description=f"Votre suggestion a été approuvée sur {interaction.guild.name}",
                            color=discord.Color.green()
                        )
                        dm_embed.add_field(name="Suggestion", value=embed.description)
                        if commentaire:
                            dm_embed.add_field(name="Commentaire", value=commentaire)
                        await user.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass

            await interaction.response.send_message(
                "✅ Suggestion approuvée avec succès !",
                ephemeral=True
            )

        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Message introuvable.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue : {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="deny", description="Refuser une suggestion")
    @app_commands.default_permissions(administrator=True)
    async def deny_suggestion(
        self,
        interaction: discord.Interaction,
        message_id: str,
        raison: str = None
    ):
        """Refuser une suggestion"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.suggestions:
            return await interaction.response.send_message(
                "❌ Le système de suggestions n'est pas configuré sur ce serveur.",
                ephemeral=True
            )

        channel = self.bot.get_channel(int(self.suggestions[guild_id]["channel"]))
        if not channel:
            return await interaction.response.send_message(
                "❌ Le salon de suggestions est introuvable.",
                ephemeral=True
            )

        try:
            message = await channel.fetch_message(int(message_id))
            if not message.embeds:
                return await interaction.response.send_message(
                    "❌ Message invalide.",
                    ephemeral=True
                )

            embed = message.embeds[0]
            embed.color = discord.Color.red()
            
            if raison:
                embed.add_field(
                    name="❌ Refusée par un administrateur",
                    value=raison
                )
            else:
                embed.add_field(
                    name="❌ Statut",
                    value="Refusée par un administrateur"
                )

            await message.edit(embed=embed)
            
            # Notification DM si activée
            if self.suggestions[guild_id].get("dm_notifications"):
                user_id = int(embed.footer.text.split("ID: ")[1])
                user = interaction.guild.get_member(user_id)
                if user:
                    try:
                        dm_embed = discord.Embed(
                            title="❌ Suggestion Refusée",
                            description=f"Votre suggestion a été refusée sur {interaction.guild.name}",
                            color=discord.Color.red()
                        )
                        dm_embed.add_field(name="Suggestion", value=embed.description)
                        if raison:
                            dm_embed.add_field(name="Raison", value=raison)
                        await user.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass

            await interaction.response.send_message(
                "✅ Suggestion refusée avec succès !",
                ephemeral=True
            )

        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Message introuvable.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue : {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
