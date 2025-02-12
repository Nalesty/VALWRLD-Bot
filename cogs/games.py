import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
import asyncio
from datetime import datetime

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games_data_file = "data/games_data.json"
        self.quiz_questions = {
            "gaming": [
                {
                    "question": "Quel est le nom du plombier rouge emblématique de Nintendo ?",
                    "options": ["Mario", "Luigi", "Wario", "Waluigi"],
                    "correct": 0
                },
                {
                    "question": "Dans quel jeu trouve-t-on Lara Croft ?",
                    "options": ["Uncharted", "Tomb Raider", "Indiana Jones", "Prince of Persia"],
                    "correct": 1
                },
                {
                    "question": "Quel est le nom du hérisson bleu de SEGA ?",
                    "options": ["Knuckles", "Tails", "Shadow", "Sonic"],
                    "correct": 3
                },
                {
                    "question": "Quel jeu a popularisé le genre 'Battle Royale' ?",
                    "options": ["PUBG", "Fortnite", "Apex Legends", "Call of Duty: Warzone"],
                    "correct": 0
                },
                {
                    "question": "Quelle est la console de jeu la plus vendue de tous les temps ?",
                    "options": ["PlayStation 2", "Nintendo DS", "Game Boy", "PlayStation 4"],
                    "correct": 0
                },
                {
                    "question": "Dans quel jeu trouve-t-on le personnage de Master Chief ?",
                    "options": ["Doom", "Halo", "Gears of War", "Destiny"],
                    "correct": 1
                }
            ]
        }
        self.active_games = {}
        # Créer le dossier data s'il n'existe pas
        if not os.path.exists('data'):
            os.makedirs('data')
        self.load_data()

    def load_data(self):
        """Charger les données des jeux"""
        try:
            if os.path.exists(self.games_data_file):
                with open(self.games_data_file, 'r') as f:
                    self.active_games = json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des données : {e}")
            self.active_games = {}
            self.save_data()

    def save_data(self):
        """Sauvegarder les données des jeux"""
        try:
            with open(self.games_data_file, 'w') as f:
                json.dump(self.active_games, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données : {e}")

    @app_commands.command(name="quiz", description="Démarrer un quiz sur les jeux vidéo")
    async def quiz(self, interaction: discord.Interaction):
        """Démarrer un quiz gaming"""
        # Vérifier si un quiz est déjà en cours dans ce salon
        if str(interaction.channel_id) in self.active_games:
            return await interaction.response.send_message(
                "❌ Un quiz est déjà en cours dans ce salon !",
                ephemeral=True
            )

        # Sélectionner des questions aléatoires (3 questions)
        questions = random.sample(self.quiz_questions["gaming"], 3)

        # Créer une nouvelle session de quiz
        quiz_data = {
            "questions": questions,
            "current_question": 0,
            "scores": {},
            "started_at": datetime.now().isoformat()
        }
        self.active_games[str(interaction.channel_id)] = quiz_data

        # Créer l'embed d'introduction
        embed = discord.Embed(
            title="🎮 Quiz Gaming",
            description="Le quiz va commencer ! Vous avez 20 secondes pour répondre à chaque question.\n"
                       "Répondez en tapant le numéro de votre réponse (1, 2, 3 ou 4).",
            color=discord.Color.blue()
        )
        embed.add_field(name="Questions", value="3 questions")
        embed.add_field(name="Temps par question", value="20 secondes")
        embed.set_footer(text="Préparez-vous !")

        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)  # Attendre 5 secondes avant de commencer
        await self.send_next_question(interaction.channel)

    async def send_next_question(self, channel):
        """Envoyer la prochaine question du quiz"""
        quiz_data = self.active_games[str(channel.id)]

        if quiz_data["current_question"] >= len(quiz_data["questions"]):
            # Quiz terminé
            embed = discord.Embed(
                title="🏆 Quiz terminé !",
                description="Voici les résultats :",
                color=discord.Color.gold()
            )

            # Trier les scores
            sorted_scores = sorted(
                quiz_data["scores"].items(),
                key=lambda x: x[1],
                reverse=True
            )

            if not sorted_scores:
                embed.add_field(
                    name="Aucun participant",
                    value="Personne n'a marqué de points !",
                    inline=False
                )
            else:
                for i, (user_id, score) in enumerate(sorted_scores, 1):
                    user = channel.guild.get_member(int(user_id))
                    if user:
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👏"
                        embed.add_field(
                            name=f"{medal} {user.display_name}",
                            value=f"{score} point{'s' if score > 1 else ''}",
                            inline=False
                        )

            await channel.send(embed=embed)
            del self.active_games[str(channel.id)]
            self.save_data()
            return

        # Envoyer la question
        question = quiz_data["questions"][quiz_data["current_question"]]
        question_num = quiz_data["current_question"] + 1

        embed = discord.Embed(
            title=f"Question {question_num}/3",
            description=question["question"],
            color=discord.Color.blue()
        )

        for i, option in enumerate(question["options"], 1):
            embed.add_field(
                name=f"Option {i}",
                value=option,
                inline=True
            )

        embed.set_footer(text="Vous avez 20 secondes pour répondre ! Tapez le numéro de votre réponse.")
        message = await channel.send(embed=embed)

        # Attendre les réponses
        answered_users = set()

        def check(m):
            return (
                m.channel.id == channel.id and
                m.content.isdigit() and
                1 <= int(m.content) <= len(question["options"]) and
                m.author.id not in answered_users
            )

        end_time = datetime.now().timestamp() + 20
        while datetime.now().timestamp() < end_time:
            try:
                msg = await self.bot.wait_for('message', timeout=end_time - datetime.now().timestamp(), check=check)
                user_id = str(msg.author.id)
                answered_users.add(msg.author.id)

                # Vérifier la réponse
                if int(msg.content) - 1 == question["correct"]:
                    if user_id not in quiz_data["scores"]:
                        quiz_data["scores"][user_id] = 0
                    quiz_data["scores"][user_id] += 1
                    await msg.add_reaction("✅")
                else:
                    await msg.add_reaction("❌")

            except asyncio.TimeoutError:
                break

        # Afficher la réponse correcte
        correct_option = question["options"][question["correct"]]
        embed = discord.Embed(
            title=f"⏰ Temps écoulé !",
            description=f"La bonne réponse était : **{correct_option}** (Option {question['correct'] + 1})",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)

        quiz_data["current_question"] += 1
        await asyncio.sleep(3)  # Pause entre les questions
        await self.send_next_question(channel)

    @app_commands.command(name="rpc", description="Jouer à Pierre-Papier-Ciseaux")
    @app_commands.choices(choix=[
        app_commands.Choice(name="Pierre", value="pierre"),
        app_commands.Choice(name="Papier", value="papier"),
        app_commands.Choice(name="Ciseaux", value="ciseaux")
    ])
    async def rpc(self, interaction: discord.Interaction, choix: str):
        choices = ["pierre", "papier", "ciseaux"]
        bot_choice = random.choice(choices)

        emojis = {
            "pierre": "🪨",
            "papier": "📄",
            "ciseaux": "✂️"
        }

        def get_result(user, bot):
            if user == bot:
                return "Égalité!"
            if (
                (user == "pierre" and bot == "ciseaux") or
                (user == "papier" and bot == "pierre") or
                (user == "ciseaux" and bot == "papier")
            ):
                return "Vous avez gagné!"
            return "Vous avez perdu!"

        result = get_result(choix, bot_choice)

        embed = discord.Embed(
            title="Pierre-Papier-Ciseaux",
            color=discord.Color.blue()
        )
        embed.add_field(name="Votre choix", value=f"{emojis[choix]} {choix}", inline=True)
        embed.add_field(name="Choix du bot", value=f"{emojis[bot_choice]} {bot_choice}", inline=True)
        embed.add_field(name="Résultat", value=result, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GamesCog(bot))