import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.polls_file = "data/polls.json"
        self.polls = {}
        self.load_polls()

    def load_polls(self):
        """Charger les sondages depuis le fichier JSON"""
        try:
            # Créer le dossier data s'il n'existe pas
            if not os.path.exists('data'):
                os.makedirs('data')
                print(f"✅ Dossier data créé avec succès")

            if os.path.exists(self.polls_file):
                with open(self.polls_file, 'r', encoding='utf-8') as f:
                    self.polls = json.load(f)
                    print(f"✅ Sondages chargés : {len(self.polls)} sondages")
            else:
                # Créer le fichier s'il n'existe pas
                self.polls = {}
                self.save_polls()
                print(f"✅ Nouveau fichier de sondages créé")

        except Exception as e:
            print(f"❌ Erreur lors du chargement des sondages : {str(e)}")
            self.polls = {}

    def save_polls(self):
        """Sauvegarder les sondages dans le fichier JSON"""
        try:
            with open(self.polls_file, 'w', encoding='utf-8') as f:
                json.dump(self.polls, f, indent=4, ensure_ascii=False)
                print(f"✅ Sondages sauvegardés")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des sondages : {str(e)}")

    @app_commands.command(name="poll", description="Créer un sondage")
    @app_commands.describe(
        question="La question du sondage",
        option1="Option 1",
        option2="Option 2",
        option3="Option 3 (optionnel)",
        option4="Option 4 (optionnel)",
        duree="Durée du sondage (ex: 1h, 2d)"
    )
    async def create_poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        duree: str = None
    ):
        """Créer un sondage avec jusqu'à 4 options"""
        try:
            # Préparer les options
            options = [option1, option2]
            if option3:
                options.append(option3)
            if option4:
                options.append(option4)

            # Calculer la durée si spécifiée
            end_time = None
            if duree:
                try:
                    unit = duree[-1].lower()
                    value = int(duree[:-1])
                    if unit == 'h':
                        end_time = datetime.now() + timedelta(hours=value)
                    elif unit == 'd':
                        end_time = datetime.now() + timedelta(days=value)
                    else:
                        return await interaction.response.send_message(
                            "❌ Format de durée invalide. Utilisez h pour les heures ou d pour les jours (ex: 2h, 1d)",
                            ephemeral=True
                        )
                except ValueError:
                    return await interaction.response.send_message(
                        "❌ Format de durée invalide",
                        ephemeral=True
                    )

            # Créer l'embed
            embed = discord.Embed(
                title="📊 " + question,
                description="Cliquez sur un bouton pour voter !",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            # Ajouter les options à l'embed
            for i, option in enumerate(options, 1):
                embed.add_field(
                    name=f"Option {i}",
                    value=option,
                    inline=True
                )

            if end_time:
                embed.add_field(
                    name="Se termine",
                    value=f"<t:{int(end_time.timestamp())}:R>",
                    inline=False
                )

            embed.set_footer(text=f"Créé par {interaction.user.name}")

            # Créer les boutons
            buttons = []
            view = discord.ui.View()
            for i, option in enumerate(options, 1):
                button = discord.ui.Button(
                    custom_id=f"poll_{i}",
                    label=f"{option} (0)",
                    style=discord.ButtonStyle.primary
                )
                buttons.append(button)
                view.add_item(button)

            # Envoyer le message
            message = await interaction.response.send_message(embed=embed, view=view)
            if isinstance(message, discord.InteractionMessage):
                message_id = str(message.id)
            else:
                message_id = str(interaction.id)

            # Sauvegarder le sondage
            self.polls[message_id] = {
                "question": question,
                "options": options,
                "votes": {str(i): [] for i in range(1, len(options) + 1)},
                "author_id": str(interaction.user.id),
                "end_time": end_time.isoformat() if end_time else None,
                "created_at": datetime.now().isoformat()
            }
            self.save_polls()

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue lors de la création du sondage : {str(e)}",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Gérer les votes"""
        if not interaction.data or "custom_id" not in interaction.data:
            return

        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith("poll_"):
            return

        try:
            poll_id = str(interaction.message.id)
            if poll_id not in self.polls:
                return await interaction.response.send_message(
                    "❌ Ce sondage n'existe plus.",
                    ephemeral=True
                )

            poll = self.polls[poll_id]
            option = custom_id.split("_")[1]
            user_id = str(interaction.user.id)

            # Vérifier si le sondage est terminé
            if poll["end_time"]:
                end_time = datetime.fromisoformat(poll["end_time"])
                if datetime.now() > end_time:
                    return await interaction.response.send_message(
                        "❌ Ce sondage est terminé.",
                        ephemeral=True
                    )

            # Vérifier si l'utilisateur a déjà voté
            has_voted = any(user_id in voters for voters in poll["votes"].values())
            if has_voted:
                return await interaction.response.send_message(
                    "❌ Vous avez déjà voté sur ce sondage.",
                    ephemeral=True
                )

            # Ajouter le vote
            poll["votes"][option].append(user_id)
            self.save_polls()

            # Mettre à jour l'affichage
            embed = interaction.message.embeds[0]
            view = discord.ui.View()

            for i, opt in enumerate(poll["options"], 1):
                votes = len(poll["votes"][str(i)])
                button = discord.ui.Button(
                    custom_id=f"poll_{i}",
                    label=f"{opt} ({votes})",
                    style=discord.ButtonStyle.primary
                )
                view.add_item(button)

            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.send_message(
                "✅ Vote enregistré !",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue lors du traitement de votre vote : {str(e)}",
                ephemeral=True
            ).catch(lambda _: None)

async def setup(bot):
    await bot.add_cog(Polls(bot))