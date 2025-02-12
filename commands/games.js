const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('rpc')
        .setDescription('Jouer à Pierre-Papier-Ciseaux')
        .addStringOption(option =>
            option.setName('choix')
                .setDescription('Votre choix')
                .setRequired(true)
                .addChoices(
                    { name: 'Pierre', value: 'pierre' },
                    { name: 'Papier', value: 'papier' },
                    { name: 'Ciseaux', value: 'ciseaux' }
                )),

    async execute(interaction) {
        const choices = ['pierre', 'papier', 'ciseaux'];
        const userChoice = interaction.options.getString('choix');
        const botChoice = choices[Math.floor(Math.random() * choices.length)];

        const getResult = (user, bot) => {
            if (user === bot) return 'Égalité!';
            if (
                (user === 'pierre' && bot === 'ciseaux') ||
                (user === 'papier' && bot === 'pierre') ||
                (user === 'ciseaux' && bot === 'papier')
            ) {
                return 'Vous avez gagné!';
            }
            return 'Vous avez perdu!';
        };

        const emojis = {
            pierre: '🪨',
            papier: '📄',
            ciseaux: '✂️'
        };

        const result = getResult(userChoice, botChoice);

        await interaction.reply({
            content: `
Vous: ${emojis[userChoice]} ${userChoice}
Bot: ${emojis[botChoice]} ${botChoice}
Résultat: ${result}`,
        });
    },
};
