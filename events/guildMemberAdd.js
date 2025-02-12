const { EmbedBuilder } = require('discord.js');
const { colors, welcomeChannel } = require('../config.js');

module.exports = {
    name: 'guildMemberAdd',
    execute: async (member) => {
        const channel = member.guild.channels.cache.find(
            ch => ch.name === welcomeChannel
        );

        if (!channel) return;

        const embed = new EmbedBuilder()
            .setColor(colors.success)
            .setTitle('👋 Nouveau membre!')
            .setDescription(`Bienvenue ${member} sur ${member.guild.name}!`)
            .setThumbnail(member.user.displayAvatarURL({ dynamic: true }))
            .addFields(
                { name: 'Membre n°', value: `${member.guild.memberCount}`, inline: true },
                { name: 'Rejoint le', value: `<t:${Math.floor(member.joinedTimestamp / 1000)}:F>`, inline: true }
            )
            .setTimestamp();

        await channel.send({ embeds: [embed] });
    },
};
