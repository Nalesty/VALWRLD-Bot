const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const { colors } = require('../config.js');

class BlackjackGame {
    constructor() {
        this.deck = this.createDeck();
        this.playerHand = [];
        this.dealerHand = [];
    }

    createDeck() {
        const suits = ['♠', '♥', '♦', '♣'];
        const values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
        const deck = [];
        
        for (const suit of suits) {
            for (const value of values) {
                deck.push({ suit, value });
            }
        }
        
        return this.shuffle(deck);
    }

    shuffle(deck) {
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        return deck;
    }

    drawCard() {
        return this.deck.pop();
    }

    calculateHand(hand) {
        let sum = 0;
        let aces = 0;

        for (const card of hand) {
            if (card.value === 'A') {
                aces += 1;
                sum += 11;
            } else if (['J', 'Q', 'K'].includes(card.value)) {
                sum += 10;
            } else {
                sum += parseInt(card.value);
            }
        }

        while (sum > 21 && aces > 0) {
            sum -= 10;
            aces -= 1;
        }

        return sum;
    }

    formatHand(hand, hidden = false) {
        if (hidden) {
            return `${hand[0].value}${hand[0].suit} | ?`;
        }
        return hand.map(card => `${card.value}${card.suit}`).join(' | ');
    }
}

module.exports = {
    data: new SlashCommandBuilder()
        .setName('blackjack')
        .setDescription('Jouer au Blackjack'),

    async execute(interaction) {
        const game = new BlackjackGame();
        
        // Distribution initiale
        game.playerHand.push(game.drawCard(), game.drawCard());
        game.dealerHand.push(game.drawCard(), game.drawCard());

        const createGameEmbed = (hideDealer = true, gameOver = false) => {
            const embed = new EmbedBuilder()
                .setColor(colors.primary)
                .setTitle('🎲 Blackjack')
                .addFields(
                    { name: '🎰 Croupier', value: game.formatHand(game.dealerHand, hideDealer) },
                    { name: '👤 Vous', value: game.formatHand(game.playerHand) }
                );

            if (gameOver) {
                const playerScore = game.calculateHand(game.playerHand);
                const dealerScore = game.calculateHand(game.dealerHand);
                
                let result;
                if (playerScore > 21) {
                    result = 'Vous avez dépassé 21! Perdu!';
                } else if (dealerScore > 21) {
                    result = 'Le croupier a dépassé 21! Gagné!';
                } else if (playerScore > dealerScore) {
                    result = 'Vous avez gagné!';
                } else if (playerScore < dealerScore) {
                    result = 'Le croupier gagne!';
                } else {
                    result = 'Égalité!';
                }
                
                embed.addFields({ name: 'Résultat', value: result });
            }

            return embed;
        };

        const response = await interaction.reply({
            embeds: [createGameEmbed()],
            components: [
                {
                    type: 1,
                    components: [
                        {
                            type: 2,
                            custom_id: 'hit',
                            label: 'Tirer',
                            style: 1,
                        },
                        {
                            type: 2,
                            custom_id: 'stand',
                            label: 'Rester',
                            style: 1,
                        }
                    ]
                }
            ],
            fetchReply: true
        });

        const collector = response.createMessageComponentCollector({
            time: 60000
        });

        collector.on('collect', async i => {
            if (i.user.id !== interaction.user.id) {
                return i.reply({ content: 'Ce n\'est pas votre partie!', ephemeral: true });
            }

            if (i.customId === 'hit') {
                game.playerHand.push(game.drawCard());
                const playerScore = game.calculateHand(game.playerHand);

                if (playerScore > 21) {
                    collector.stop();
                    await i.update({
                        embeds: [createGameEmbed(false, true)],
                        components: []
                    });
                } else {
                    await i.update({
                        embeds: [createGameEmbed()]
                    });
                }
            } else if (i.customId === 'stand') {
                let dealerScore = game.calculateHand(game.dealerHand);
                while (dealerScore < 17) {
                    game.dealerHand.push(game.drawCard());
                    dealerScore = game.calculateHand(game.dealerHand);
                }

                collector.stop();
                await i.update({
                    embeds: [createGameEmbed(false, true)],
                    components: []
                });
            }
        });

        collector.on('end', () => {
            if (!interaction.replied) {
                interaction.editReply({
                    components: []
                });
            }
        });
    },
};
