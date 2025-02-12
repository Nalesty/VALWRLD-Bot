const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { setupStatsChannels } = require('../utils/channelStats.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('stats')
        .setDescription('Configurer les channels de statistiques')
        .addSubcommand(subcommand =>
            subcommand
                .setName('setup')
                .setDescription('Créer ou recréer les channels de statistiques'))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async execute(interaction) {
        await interaction.deferReply();

        try {
            await setupStatsChannels(interaction.guild);
            await interaction.editReply('Les channels de statistiques ont été configurés avec succès !');
        } catch (error) {
            console.error('Erreur lors de la configuration des stats:', error);
            await interaction.editReply('Une erreur est survenue lors de la configuration des channels de statistiques.');
        }
    },
};
