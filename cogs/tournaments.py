import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import random

class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tournaments_file = "data/tournaments.json"
        self.tournaments = {}
        self.load_tournaments()

    def load_tournaments(self):
        """Charger les tournois depuis le fichier JSON"""
        try:
            # Créer le dossier data s'il n'existe pas
            if not os.path.exists('data'):
                os.makedirs('data')
                print(f"✅ Dossier data créé avec succès")

            if os.path.exists(self.tournaments_file):
                with open(self.tournaments_file, 'r', encoding='utf-8') as f:
                    self.tournaments = json.load(f)
                    print(f"✅ Tournois chargés : {len(self.tournaments)} tournois")
            else:
                # Créer le fichier s'il n'existe pas
                self.tournaments = {}
                self.save_tournaments()
                print(f"✅ Nouveau fichier de tournois créé")

        except Exception as e:
            print(f"❌ Erreur lors du chargement des tournois : {str(e)}")
            self.tournaments = {}

    def save_tournaments(self):
        """Sauvegarder les tournois dans le fichier JSON"""
        try:
            with open(self.tournaments_file, 'w', encoding='utf-8') as f:
                json.dump(self.tournaments, f, indent=4, ensure_ascii=False)
                print(f"✅ Tournois sauvegardés")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des tournois : {str(e)}")

    @app_commands.command(name="createtournament", description="Créer un nouveau tournoi")
    @app_commands.describe(
        nom="Nom du tournoi",
        jeu="Nom du jeu",
        max_participants="Nombre maximum de participants",
        date_debut="Date de début (format: JJ/MM/YYYY HH:MM)",
        description="Description du tournoi"
    )
    async def create_tournament(
        self,
        interaction: discord.Interaction,
        nom: str,
        jeu: str,
        max_participants: int,
        date_debut: str,
        description: str = "Pas de description"
    ):
        """Créer un nouveau tournoi"""
        try:
            # Vérifier le format de la date
            date_debut = datetime.strptime(date_debut, "%d/%m/%Y %H:%M")
            if date_debut < datetime.now():
                return await interaction.response.send_message(
                    "❌ La date de début doit être dans le futur !",
                    ephemeral=True
                )

            # Créer le tournoi
            tournament_id = str(interaction.id)
            self.tournaments[tournament_id] = {
                "name": nom,
                "game": jeu,
                "description": description,
                "max_participants": max_participants,
                "start_date": date_debut.isoformat(),
                "organizer": str(interaction.user.id),
                "participants": [],
                "matches": [],
                "status": "registration"  # registration, in_progress, completed
            }
            self.save_tournaments()

            # Créer l'embed d'annonce
            embed = discord.Embed(
                title=f"🏆 Nouveau tournoi : {nom}",
                description=description,
                color=discord.Color.blue(),
                timestamp=date_debut
            )
            embed.add_field(name="Jeu", value=jeu, inline=True)
            embed.add_field(name="Places", value=f"0/{max_participants}", inline=True)
            embed.add_field(name="Début", value=f"<t:{int(date_debut.timestamp())}:F>", inline=True)
            embed.set_footer(text=f"Organisé par {interaction.user.display_name}")

            # Créer les boutons d'inscription
            view = discord.ui.View()
            join_button = discord.ui.Button(
                custom_id=f"tournament_join_{tournament_id}",
                label="S'inscrire",
                style=discord.ButtonStyle.success
            )
            view.add_item(join_button)

            await interaction.response.send_message(embed=embed, view=view)

        except ValueError:
            await interaction.response.send_message(
                "❌ Format de date invalide. Utilisez JJ/MM/YYYY HH:MM",
                ephemeral=True
            )

    @app_commands.command(name="tournament", description="Voir les détails d'un tournoi")
    @app_commands.describe(
        tournament_id="ID du tournoi"
    )
    async def tournament_info(self, interaction: discord.Interaction, tournament_id: str):
        """Voir les détails d'un tournoi"""
        if tournament_id not in self.tournaments:
            return await interaction.response.send_message(
                "❌ Tournoi introuvable !",
                ephemeral=True
            )

        tournament = self.tournaments[tournament_id]
        start_date = datetime.fromisoformat(tournament["start_date"])

        embed = discord.Embed(
            title=f"🏆 {tournament['name']}",
            description=tournament["description"],
            color=discord.Color.blue()
        )

        embed.add_field(name="Jeu", value=tournament["game"], inline=True)
        embed.add_field(
            name="Participants",
            value=f"{len(tournament['participants'])}/{tournament['max_participants']}",
            inline=True
        )
        embed.add_field(
            name="Début",
            value=f"<t:{int(start_date.timestamp())}:F>",
            inline=True
        )
        embed.add_field(
            name="Statut",
            value=self.get_status_text(tournament["status"]),
            inline=True
        )

        if tournament["participants"]:
            participants_text = ""
            for i, p_id in enumerate(tournament["participants"], 1):
                member = interaction.guild.get_member(int(p_id))
                if member:
                    participants_text += f"{i}. {member.display_name}\n"
            embed.add_field(
                name="Liste des participants",
                value=participants_text or "Aucun participant",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    def get_status_text(self, status):
        """Obtenir le texte du statut en français"""
        return {
            "registration": "📝 Inscriptions ouvertes",
            "in_progress": "⚔️ En cours",
            "completed": "🏁 Terminé"
        }.get(status, status)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Gérer les interactions des boutons"""
        if not interaction.data or "custom_id" not in interaction.data:
            return

        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith("tournament_"):
            return

        action, tournament_id = custom_id.split("_")[1:]

        if action == "join":
            await self.handle_tournament_join(interaction, tournament_id)

    async def handle_tournament_join(self, interaction: discord.Interaction, tournament_id: str):
        """Gérer l'inscription à un tournoi"""
        if tournament_id not in self.tournaments:
            return await interaction.response.send_message(
                "❌ Ce tournoi n'existe plus.",
                ephemeral=True
            )

        tournament = self.tournaments[tournament_id]
        user_id = str(interaction.user.id)

        # Vérifications
        if user_id in tournament["participants"]:
            return await interaction.response.send_message(
                "❌ Vous êtes déjà inscrit à ce tournoi !",
                ephemeral=True
            )

        if len(tournament["participants"]) >= tournament["max_participants"]:
            return await interaction.response.send_message(
                "❌ Le tournoi est complet !",
                ephemeral=True
            )

        if tournament["status"] != "registration":
            return await interaction.response.send_message(
                "❌ Les inscriptions sont fermées !",
                ephemeral=True
            )

        # Ajouter le participant
        tournament["participants"].append(user_id)
        self.save_tournaments()

        # Mettre à jour l'affichage
        embed = interaction.message.embeds[0]
        for field in embed.fields:
            if field.name == "Places":
                field.value = f"{len(tournament['participants'])}/{tournament['max_participants']}"
                break

        view = discord.ui.View()
        join_button = discord.ui.Button(
            custom_id=f"tournament_join_{tournament_id}",
            label="S'inscrire",
            style=discord.ButtonStyle.success,
            disabled=len(tournament["participants"]) >= tournament["max_participants"]
        )
        view.add_item(join_button)

        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.send_message(
            "✅ Vous êtes inscrit au tournoi !",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Tournaments(bot))