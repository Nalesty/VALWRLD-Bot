const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const { colors } = require('../config.js');
const { getServerStats } = require('../utils/stats.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('info')
        .setDescription('Affiche les informations du serveur'),
    
    async execute(interaction) {
        const stats = await getServerStats(interaction.guild);
        
        const embed = new EmbedBuilder()
            .setColor(colors.primary)
            .setTitle(`📊 Informations sur ${interaction.guild.name}`)
            .addFields(
                { name: '👥 Membres', value: `Total: ${stats.totalUsers}\nEn ligne: ${stats.onlineUsers}\nBots: ${stats.botCount}`, inline: true },
                { name: '📝 Canaux', value: `Total: ${stats.channelCount}\nTextuels: ${stats.textChannels}\nVocaux: ${stats.voiceChannels}`, inline: true },
                { name: '🎭 Rôles', value: `${stats.roleCount}`, inline: true },
                { name: '📅 Créé le', value: `<t:${Math.floor(interaction.guild.createdTimestamp / 1000)}:F>`, inline: true },
                { name: '👑 Propriétaire', value: `<@${interaction.guild.ownerId}>`, inline: true }
            )
            .setThumbnail(interaction.guild.iconURL({ dynamic: true }));

        await interaction.reply({ embeds: [embed] });
    },
};
