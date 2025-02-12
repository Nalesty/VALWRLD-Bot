import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import List, Dict

class Card:
    def __init__(self, suit: str, value: str):
        self.suit = suit
        self.value = value

    def __str__(self):
        return f"{self.value}{self.suit}"

class BlackjackGame:
    def __init__(self):
        self.deck = self.create_deck()
        self.player_hand: List[Card] = []
        self.dealer_hand: List[Card] = []

    def create_deck(self) -> List[Card]:
        suits = ['♠', '♥', '♦', '♣']
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [Card(suit, value) for suit in suits for value in values]
        random.shuffle(deck)
        return deck

    def draw_card(self) -> Card:
        return self.deck.pop()

    def calculate_hand(self, hand: List[Card]) -> int:
        total = 0
        aces = 0

        for card in hand:
            if card.value == 'A':
                aces += 1
                total += 11
            elif card.value in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card.value)

        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    def format_hand(self, hand: List[Card], hide_dealer: bool = False) -> str:
        if hide_dealer:
            return f"{hand[0]} | ?"
        return " | ".join(str(card) for card in hand)

class BlackjackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games: Dict[int, BlackjackGame] = {}

    @app_commands.command(name="blackjack", description="Jouer au Blackjack")
    async def blackjack(self, interaction: discord.Interaction):
        if interaction.user.id in self.games:
            await interaction.response.send_message("Vous avez déjà une partie en cours!", ephemeral=True)
            return

        game = BlackjackGame()
        self.games[interaction.user.id] = game

        # Distribution initiale
        game.player_hand.extend([game.draw_card(), game.draw_card()])
        game.dealer_hand.extend([game.draw_card(), game.draw_card()])

        embed = discord.Embed(title="🎲 Blackjack", color=discord.Color.blue())
        embed.add_field(name="🎰 Croupier", value=game.format_hand(game.dealer_hand, True), inline=False)
        embed.add_field(name="👤 Vous", value=game.format_hand(game.player_hand), inline=False)

        # Création des boutons
        hit_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Tirer", custom_id="hit")
        stand_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Rester", custom_id="stand")
        
        view = discord.ui.View()
        view.add_item(hit_button)
        view.add_item(stand_button)

        async def hit_callback(interaction: discord.Interaction):
            game = self.games.get(interaction.user.id)
            if not game:
                return

            game.player_hand.append(game.draw_card())
            player_score = game.calculate_hand(game.player_hand)

            embed = discord.Embed(title="🎲 Blackjack", color=discord.Color.blue())
            embed.add_field(name="🎰 Croupier", value=game.format_hand(game.dealer_hand, True), inline=False)
            embed.add_field(name="👤 Vous", value=game.format_hand(game.player_hand), inline=False)

            if player_score > 21:
                embed.add_field(name="Résultat", value="Vous avez dépassé 21! Perdu!", inline=False)
                await interaction.response.edit_message(embed=embed, view=None)
                del self.games[interaction.user.id]
            else:
                await interaction.response.edit_message(embed=embed)

        async def stand_callback(interaction: discord.Interaction):
            game = self.games.get(interaction.user.id)
            if not game:
                return

            dealer_score = game.calculate_hand(game.dealer_hand)
            while dealer_score < 17:
                game.dealer_hand.append(game.draw_card())
                dealer_score = game.calculate_hand(game.dealer_hand)

            player_score = game.calculate_hand(game.player_hand)

            embed = discord.Embed(title="🎲 Blackjack", color=discord.Color.blue())
            embed.add_field(name="🎰 Croupier", value=game.format_hand(game.dealer_hand, False), inline=False)
            embed.add_field(name="👤 Vous", value=game.format_hand(game.player_hand), inline=False)

            if dealer_score > 21:
                result = "Le croupier a dépassé 21! Gagné!"
            elif player_score > dealer_score:
                result = "Vous avez gagné!"
            elif player_score < dealer_score:
                result = "Le croupier gagne!"
            else:
                result = "Égalité!"

            embed.add_field(name="Résultat", value=result, inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
            del self.games[interaction.user.id]

        hit_button.callback = hit_callback
        stand_button.callback = stand_callback

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(BlackjackCog(bot))
