const { EmbedBuilder } = require('discord.js');
const { colors } = require('../config.js');

const createModEmbed = (action, target, moderator, reason) => {
    return new EmbedBuilder()
        .setColor(colors.warning)
        .setTitle(`🛡️ ${action}`)
        .addFields(
            { name: 'Utilisateur', value: `${target.tag} (${target.id})`, inline: true },
            { name: 'Modérateur', value: `${moderator.tag}`, inline: true },
            { name: 'Raison', value: reason }
        )
        .setTimestamp();
};

module.exports = {
    createModEmbed
};
