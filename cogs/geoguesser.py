import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Dict, List

class Location:
    def __init__(self, name: str, description: str, region: str, indices: List[str]):
        self.name = name
        self.description = description
        self.region = region
        self.indices = indices

QUEBEC_LOCATIONS = [
    Location(
        "Vieux-Québec",
        "Un site du patrimoine mondial de l'UNESCO avec des fortifications historiques",
        "Capitale-Nationale",
        [
            "Je suis entouré de murs de pierre",
            "Le Château Frontenac me surplombe",
            "Mes rues pavées rappellent l'Europe"
        ]
    ),
    Location(
        "Mont-Royal",
        "Une montagne emblématique au cœur d'une grande ville",
        "Montréal",
        [
            "Je suis un parc urbain sur une colline",
            "Une grande croix illuminée me couronne",
            "Je offre une vue panoramique sur la métropole"
        ]
    ),
    Location(
        "Château Frontenac",
        "L'hôtel le plus photographié au monde",
        "Québec",
        [
            "Je domine le fleuve Saint-Laurent",
            "Mes tourelles sont emblématiques",
            "Je suis un symbole de l'hôtellerie de luxe"
        ]
    ),
    Location(
        "Parc national de la Gaspésie",
        "Un paradis pour les randonneurs et les amoureux de la nature",
        "Gaspésie",
        [
            "Je abrite des caribous",
            "Mes monts Chic-Chocs sont majestueux",
            "Je suis un refuge pour la faune"
        ]
    ),
    Location(
        "Basilique Notre-Dame",
        "Une église néo-gothique spectaculaire",
        "Montréal",
        [
            "Mon intérieur est bleu et doré",
            "Je suis située dans le Vieux-Montréal",
            "Mes vitraux racontent l'histoire de la ville"
        ]
    )
]

class GeoGuesserGame:
    def __init__(self):
        self.location = random.choice(QUEBEC_LOCATIONS)
        self.indices_revealed = 0
        self.attempts = 0
        self.max_attempts = 3
        self.points = 100

    def reveal_next_hint(self) -> str:
        if self.indices_revealed < len(self.location.indices):
            hint = self.location.indices[self.indices_revealed]
            self.indices_revealed += 1
            self.points -= 20
            return hint
        return "Plus d'indices disponibles!"

    def check_guess(self, guess: str) -> bool:
        return guess.lower() == self.location.name.lower()

class GeoGuesserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games: Dict[int, GeoGuesserGame] = {}

    @app_commands.command(name="geoguesser", description="Jouer à GeoGuesser Québec")
    async def geoguesser(self, interaction: discord.Interaction):
        if interaction.user.id in self.games:
            await interaction.response.send_message("Vous avez déjà une partie en cours!", ephemeral=True)
            return

        game = GeoGuesserGame()
        self.games[interaction.user.id] = game

        embed = discord.Embed(
            title="🗺️ GeoGuesser Québec",
            description="Devinez le lieu au Québec à partir des indices!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Premier indice",
            value=game.location.indices[0],
            inline=False
        )
        
        embed.add_field(
            name="Points possibles",
            value=str(game.points),
            inline=True
        )
        
        embed.add_field(
            name="Tentatives restantes",
            value=f"{game.max_attempts - game.attempts}/{game.max_attempts}",
            inline=True
        )

        # Création des boutons
        hint_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Indice suivant", custom_id="hint")
        
        view = discord.ui.View()
        view.add_item(hint_button)

        async def hint_callback(interaction: discord.Interaction):
            game = self.games.get(interaction.user.id)
            if not game:
                return

            hint = game.reveal_next_hint()
            embed = interaction.message.embeds[0]
            embed.insert_field_at(
                index=len(embed.fields),
                name=f"Indice {game.indices_revealed}",
                value=hint,
                inline=False
            )
            embed.set_field_at(
                index=-2,
                name="Points possibles",
                value=str(game.points),
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed)

        hint_button.callback = hint_callback

        await interaction.response.send_message(
            "Pour deviner, utilisez la commande `/guess <votre réponse>`\nPar exemple: `/guess Vieux-Québec`",
            embed=embed,
            view=view
        )

    @app_commands.command(name="guess", description="Faire une supposition pour GeoGuesser Québec")
    @app_commands.describe(reponse="Votre supposition pour le lieu")
    async def guess(self, interaction: discord.Interaction, reponse: str):
        game = self.games.get(interaction.user.id)
        if not game:
            await interaction.response.send_message(
                "Vous n'avez pas de partie en cours! Utilisez `/geoguesser` pour commencer.",
                ephemeral=True
            )
            return

        game.attempts += 1
        
        if game.check_guess(reponse):
            embed = discord.Embed(
                title="🎉 Félicitations!",
                description=f"Vous avez trouvé! C'était bien {game.location.name}!\nPoints gagnés: {game.points}",
                color=discord.Color.green()
            )
            embed.add_field(name="Description", value=game.location.description, inline=False)
            embed.add_field(name="Région", value=game.location.region, inline=True)
            
            del self.games[interaction.user.id]
            await interaction.response.send_message(embed=embed)
        else:
            if game.attempts >= game.max_attempts:
                embed = discord.Embed(
                    title="❌ Partie terminée",
                    description=f"Vous avez épuisé vos tentatives! La réponse était: {game.location.name}",
                    color=discord.Color.red()
                )
                embed.add_field(name="Description", value=game.location.description, inline=False)
                embed.add_field(name="Région", value=game.location.region, inline=True)
                
                del self.games[interaction.user.id]
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"Ce n'est pas la bonne réponse! Il vous reste {game.max_attempts - game.attempts} tentative(s).",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(GeoGuesserCog(bot))
