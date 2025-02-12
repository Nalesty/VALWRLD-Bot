const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const { colors } = require('../config.js');

const activeGames = new Map();

module.exports = {
    data: new SlashCommandBuilder()
        .setName('duel')
        .setDescription('Défier un autre membre en duel')
        .addUserOption(option =>
            option.setName('adversaire')
                .setDescription('Le membre à défier')
                .setRequired(true)),

    async execute(interaction) {
        const challenger = interaction.user;
        const opponent = interaction.options.getUser('adversaire');

        if (opponent.bot) {
            return interaction.reply({
                content: 'Vous ne pouvez pas défier un bot!',
                ephemeral: true
            });
        }

        if (opponent.id === challenger.id) {
            return interaction.reply({
                content: 'Vous ne pouvez pas vous défier vous-même!',
                ephemeral: true
            });
        }

        if (activeGames.has(opponent.id) || activeGames.has(challenger.id)) {
            return interaction.reply({
                content: 'L\'un des joueurs est déjà dans un duel!',
                ephemeral: true
            });
        }

        const embed = new EmbedBuilder()
            .setColor(colors.primary)
            .setTitle('⚔️ Défi en Duel')
            .setDescription(`${challenger} défie ${opponent} en duel!`)
            .addFields(
                { name: 'Pour accepter', value: 'Cliquez sur le bouton "Accepter"' },
                { name: 'Pour refuser', value: 'Cliquez sur le bouton "Refuser"' }
            );

        const response = await interaction.reply({
            embeds: [embed],
            components: [
                {
                    type: 1,
                    components: [
                        {
                            type: 2,
                            custom_id: 'accept',
                            label: 'Accepter',
                            style: 3,
                        },
                        {
                            type: 2,
                            custom_id: 'decline',
                            label: 'Refuser',
                            style: 4,
                        }
                    ]
                }
            ],
            fetchReply: true
        });

        const filter = i => {
            return i.user.id === opponent.id && ['accept', 'decline'].includes(i.customId);
        };

        try {
            const confirmation = await response.awaitMessageComponent({ filter, time: 30000 });

            if (confirmation.customId === 'accept') {
                const game = {
                    challenger: {
                        id: challenger.id,
                        hp: 100,
                        shield: false
                    },
                    opponent: {
                        id: opponent.id,
                        hp: 100,
                        shield: false
                    },
                    turn: challenger.id
                };

                activeGames.set(challenger.id, game);
                activeGames.set(opponent.id, game);

                const gameEmbed = new EmbedBuilder()
                    .setColor(colors.primary)
                    .setTitle('⚔️ Duel en cours')
                    .addFields(
                        { name: challenger.username, value: `❤️ ${game.challenger.hp}`, inline: true },
                        { name: opponent.username, value: `❤️ ${game.opponent.hp}`, inline: true },
                        { name: 'Tour', value: `C'est au tour de ${challenger}` }
                    );

                await confirmation.update({
                    embeds: [gameEmbed],
                    components: [
                        {
                            type: 1,
                            components: [
                                {
                                    type: 2,
                                    custom_id: 'attack',
                                    label: 'Attaquer',
                                    style: 1,
                                },
                                {
                                    type: 2,
                                    custom_id: 'shield',
                                    label: 'Se protéger',
                                    style: 1,
                                }
                            ]
                        }
                    ]
                });

                const gameCollector = response.createMessageComponentCollector({
                    time: 300000
                });

                gameCollector.on('collect', async i => {
                    const game = activeGames.get(i.user.id);
                    if (!game || game.turn !== i.user.id) {
                        return i.reply({
                            content: 'Ce n\'est pas votre tour!',
                            ephemeral: true
                        });
                    }

                    const currentPlayer = i.user.id === game.challenger.id ? game.challenger : game.opponent;
                    const otherPlayer = i.user.id === game.challenger.id ? game.opponent : game.challenger;

                    if (i.customId === 'attack') {
                        let damage = Math.floor(Math.random() * 20) + 10;
                        if (otherPlayer.shield) {
                            damage = Math.floor(damage / 2);
                            otherPlayer.shield = false;
                        }
                        otherPlayer.hp -= damage;
                    } else if (i.customId === 'shield') {
                        currentPlayer.shield = true;
                    }

                    game.turn = otherPlayer.id;

                    if (otherPlayer.hp <= 0) {
                        gameCollector.stop();
                        activeGames.delete(game.challenger.id);
                        activeGames.delete(game.opponent.id);

                        const winEmbed = new EmbedBuilder()
                            .setColor(colors.success)
                            .setTitle('🏆 Fin du duel')
                            .setDescription(`${i.user} remporte le duel!`);

                        await i.update({
                            embeds: [winEmbed],
                            components: []
                        });
                        return;
                    }

                    const updatedEmbed = new EmbedBuilder()
                        .setColor(colors.primary)
                        .setTitle('⚔️ Duel en cours')
                        .addFields(
                            { name: challenger.username, value: `❤️ ${game.challenger.hp}${game.challenger.shield ? ' 🛡️' : ''}`, inline: true },
                            { name: opponent.username, value: `❤️ ${game.opponent.hp}${game.opponent.shield ? ' 🛡️' : ''}`, inline: true },
                            { name: 'Tour', value: `C'est au tour de <@${game.turn}>` }
                        );

                    await i.update({
                        embeds: [updatedEmbed]
                    });
                });

                gameCollector.on('end', () => {
                    activeGames.delete(game.challenger.id);
                    activeGames.delete(game.opponent.id);
                    if (!response.editable) return;
                    response.edit({
                        components: []
                    });
                });

            } else {
                await confirmation.update({
                    content: 'Le défi a été refusé.',
                    embeds: [],
                    components: []
                });
            }
        } catch (error) {
            await interaction.editReply({
                content: 'Le défi a expiré.',
                embeds: [],
                components: []
            });
        }
    },
};
