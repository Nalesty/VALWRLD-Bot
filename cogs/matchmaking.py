import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class Matchmaking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.matchmaking_file = "data/matchmaking.json"
        self.lobbies = {}
        # Créer le dossier data s'il n'existe pas
        if not os.path.exists('data'):
            os.makedirs('data')
        self.load_matchmaking()

    def load_matchmaking(self):
        """Charger les données de matchmaking"""
        try:
            # Créer le dossier data s'il n'existe pas
            if not os.path.exists('data'):
                os.makedirs('data')
                print(f"✅ Dossier data créé avec succès")

            if os.path.exists(self.matchmaking_file):
                with open(self.matchmaking_file, 'r', encoding='utf-8') as f:
                    self.lobbies = json.load(f)
                    print(f"✅ Données de matchmaking chargées : {len(self.lobbies)} lobbies")
            else:
                # Créer le fichier s'il n'existe pas
                self.lobbies = {}
                self.save_matchmaking()
                print(f"✅ Nouveau fichier de matchmaking créé")

        except Exception as e:
            print(f"❌ Erreur lors du chargement du matchmaking : {str(e)}")
            self.lobbies = {}

    def save_matchmaking(self):
        """Sauvegarder les données de matchmaking"""
        try:
            with open(self.matchmaking_file, 'w', encoding='utf-8') as f:
                json.dump(self.lobbies, f, indent=4, ensure_ascii=False)
                print(f"✅ Données de matchmaking sauvegardées")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du matchmaking : {str(e)}")

    @app_commands.command(name="lfg", description="Créer ou rejoindre un groupe de jeu")
    @app_commands.describe(
        jeu="Nom du jeu",
        joueurs="Nombre de joueurs recherchés",
        description="Description de votre groupe",
        rank="Votre rang/niveau (optionnel)"
    )
    async def looking_for_group(
        self,
        interaction: discord.Interaction,
        jeu: str,
        joueurs: int,
        description: str,
        rank: str = None
    ):
        """Créer une recherche de groupe"""
        lobby_id = str(interaction.id)
        
        self.lobbies[lobby_id] = {
            "game": jeu,
            "host": str(interaction.user.id),
            "players_needed": joueurs,
            "description": description,
            "rank": rank,
            "participants": [str(interaction.user.id)],
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        self.save_matchmaking()

        embed = discord.Embed(
            title=f"🎮 Groupe recherché pour {jeu}",
            description=description,
            color=discord.Color.green()
        )
        embed.add_field(
            name="Places",
            value=f"1/{joueurs + 1}",
            inline=True
        )
        if rank:
            embed.add_field(name="Rang", value=rank, inline=True)
        embed.add_field(
            name="Host",
            value=interaction.user.mention,
            inline=True
        )
        embed.set_footer(text=f"ID: {lobby_id}")

        view = discord.ui.View()
        join_button = discord.ui.Button(
            custom_id=f"lfg_join_{lobby_id}",
            label="Rejoindre",
            style=discord.ButtonStyle.success
        )
        close_button = discord.ui.Button(
            custom_id=f"lfg_close_{lobby_id}",
            label="Fermer",
            style=discord.ButtonStyle.danger
        )
        view.add_item(join_button)
        view.add_item(close_button)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="lobbies", description="Voir les groupes de jeu actifs")
    @app_commands.describe(
        jeu="Filtrer par jeu (optionnel)"
    )
    async def list_lobbies(self, interaction: discord.Interaction, jeu: str = None):
        """Lister les groupes de jeu actifs"""
        active_lobbies = {
            id: lobby for id, lobby in self.lobbies.items()
            if lobby["status"] == "open"
            and (not jeu or lobby["game"].lower() == jeu.lower())
        }

        if not active_lobbies:
            return await interaction.response.send_message(
                "Aucun groupe actif trouvé." +
                (f" pour {jeu}" if jeu else ""),
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎮 Groupes de jeu actifs",
            color=discord.Color.blue()
        )

        for lobby_id, lobby in active_lobbies.items():
            host = interaction.guild.get_member(int(lobby["host"]))
            if not host:
                continue

            value = (
                f"👥 {len(lobby['participants'])}/{lobby['players_needed'] + 1}\n"
                f"👑 {host.display_name}\n"
                f"{lobby['description']}\n"
                f"{'🏅 ' + lobby['rank'] if lobby['rank'] else ''}"
            )
            embed.add_field(
                name=f"{lobby['game']} (ID: {lobby_id})",
                value=value,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Gérer les interactions des boutons"""
        if not interaction.data or "custom_id" not in interaction.data:
            return

        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith("lfg_"):
            return

        action, lobby_id = custom_id.split("_")[1:]
        
        if action == "join":
            await self.handle_lobby_join(interaction, lobby_id)
        elif action == "close":
            await self.handle_lobby_close(interaction, lobby_id)

    async def handle_lobby_join(self, interaction: discord.Interaction, lobby_id: str):
        """Gérer la demande de rejoindre un groupe"""
        if lobby_id not in self.lobbies:
            return await interaction.response.send_message(
                "❌ Ce groupe n'existe plus.",
                ephemeral=True
            )

        lobby = self.lobbies[lobby_id]
        user_id = str(interaction.user.id)

        if user_id in lobby["participants"]:
            return await interaction.response.send_message(
                "❌ Vous êtes déjà dans ce groupe !",
                ephemeral=True
            )

        if len(lobby["participants"]) > lobby["players_needed"]:
            return await interaction.response.send_message(
                "❌ Le groupe est complet !",
                ephemeral=True
            )

        if lobby["status"] != "open":
            return await interaction.response.send_message(
                "❌ Ce groupe est fermé !",
                ephemeral=True
            )

        # Ajouter le participant
        lobby["participants"].append(user_id)
        self.save_matchmaking()

        # Notifier le host
        host = interaction.guild.get_member(int(lobby["host"]))
        if host:
            try:
                await host.send(
                    f"👋 {interaction.user.mention} a rejoint votre groupe pour {lobby['game']} !"
                )
            except discord.Forbidden:
                pass

        # Mettre à jour l'affichage
        embed = interaction.message.embeds[0]
        for field in embed.fields:
            if field.name == "Places":
                field.value = f"{len(lobby['participants'])}/{lobby['players_needed'] + 1}"
                break

        view = discord.ui.View()
        join_button = discord.ui.Button(
            custom_id=f"lfg_join_{lobby_id}",
            label="Rejoindre",
            style=discord.ButtonStyle.success,
            disabled=len(lobby["participants"]) > lobby["players_needed"]
        )
        close_button = discord.ui.Button(
            custom_id=f"lfg_close_{lobby_id}",
            label="Fermer",
            style=discord.ButtonStyle.danger
        )
        view.add_item(join_button)
        view.add_item(close_button)

        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.send_message(
            "✅ Vous avez rejoint le groupe !",
            ephemeral=True
        )

        # Si le groupe est complet, créer un salon temporaire
        if len(lobby["participants"]) == lobby["players_needed"] + 1:
            await self.create_team_channel(interaction, lobby)

    async def handle_lobby_close(self, interaction: discord.Interaction, lobby_id: str):
        """Gérer la fermeture d'un groupe"""
        if lobby_id not in self.lobbies:
            return await interaction.response.send_message(
                "❌ Ce groupe n'existe plus.",
                ephemeral=True
            )

        lobby = self.lobbies[lobby_id]
        if str(interaction.user.id) != lobby["host"]:
            return await interaction.response.send_message(
                "❌ Seul l'hôte peut fermer le groupe !",
                ephemeral=True
            )

        lobby["status"] = "closed"
        self.save_matchmaking()

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = f"🔒 {embed.title} (Fermé)"

        view = discord.ui.View()
        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.send_message(
            "✅ Le groupe a été fermé !",
            ephemeral=True
        )

    async def create_team_channel(self, interaction: discord.Interaction, lobby):
        """Créer un salon temporaire pour l'équipe"""
        try:
            # Créer la catégorie si elle n'existe pas
            category = discord.utils.get(interaction.guild.categories, name="🎮 Équipes")
            if not category:
                category = await interaction.guild.create_category("🎮 Équipes")

            # Créer le salon
            channel_name = f"équipe-{lobby['game'].lower()}"
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            for user_id in lobby["participants"]:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    overwrites[member] = discord.PermissionOverwrite(read_messages=True)

            channel = await interaction.guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites
            )

            # Envoyer le message de bienvenue
            embed = discord.Embed(
                title="👥 Équipe formée !",
                description=f"Bienvenue dans votre salon d'équipe pour {lobby['game']} !",
                color=discord.Color.green()
            )

            participants_text = ""
            for user_id in lobby["participants"]:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    participants_text += f"• {member.mention}\n"

            embed.add_field(name="Membres", value=participants_text)
            
            if lobby["rank"]:
                embed.add_field(name="Rang", value=lobby["rank"], inline=False)

            await channel.send(embed=embed)

        except discord.Forbidden:
            await interaction.followup.send(
                "⚠️ Je n'ai pas pu créer le salon d'équipe. Vérifiez mes permissions.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Matchmaking(bot))