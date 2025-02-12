const { ChannelType } = require('discord.js');
const { statsUpdateInterval } = require('../config.js');

const statsChannels = new Map();

const formatStatChannel = (name, value) => `📊 ${name}: ${value}`;

const updateStatsChannels = async (guild) => {
    try {
        const stats = {
            userCount: guild.memberCount,
            memberCount: guild.members.cache.filter(member => !member.user.bot).size,
            onlineUserCount: guild.members.cache.filter(member => 
                member.presence?.status === 'online' || 
                member.presence?.status === 'dnd'
            ).size,
            channelCount: guild.channels.cache.size,
            roleCount: guild.roles.cache.size,
            botCount: guild.members.cache.filter(member => member.user.bot).size,
            dndCount: guild.members.cache.filter(member => 
                !member.user.bot && member.presence?.status === 'dnd'
            ).size,
            onlineMemberCount: guild.members.cache.filter(member => 
                !member.user.bot && member.presence?.status === 'online'
            ).size,
            awayCount: guild.members.cache.filter(member => 
                !member.user.bot && member.presence?.status === 'idle'
            ).size,
            offlineCount: guild.members.cache.filter(member => 
                !member.user.bot && (!member.presence || member.presence.status === 'offline')
            ).size,
            guildBoosts: guild.premiumSubscriptionCount,
            boostLevel: guild.premiumTier,
            boosterCount: guild.members.cache.filter(member => member.premiumSince).size,
            emojiCount: guild.emojis.cache.size
        };

        for (const [key, channel] of statsChannels.get(guild.id) || []) {
            if (stats[key] !== undefined) {
                await channel.setName(formatStatChannel(key, stats[key]));
            }
        }
    } catch (error) {
        console.error('Erreur lors de la mise à jour des stats:', error);
    }
};

const setupStatsChannels = async (guild) => {
    const category = await guild.channels.create({
        name: '📊 Statistiques du serveur',
        type: ChannelType.GuildCategory
    });

    const channels = new Map();
    const statsToTrack = [
        'userCount', 'memberCount', 'onlineUserCount', 'channelCount',
        'roleCount', 'botCount', 'boosterCount', 'emojiCount'
    ];

    for (const stat of statsToTrack) {
        const channel = await guild.channels.create({
            name: formatStatChannel(stat, '...'),
            type: ChannelType.GuildVoice,
            parent: category.id,
            permissionOverwrites: [
                {
                    id: guild.id,
                    deny: ['Connect']
                }
            ]
        });
        channels.set(stat, channel);
    }

    statsChannels.set(guild.id, channels);
    await updateStatsChannels(guild);
};

module.exports = {
    setupStatsChannels,
    updateStatsChannels
};
