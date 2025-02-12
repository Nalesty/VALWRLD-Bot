const getServerStats = async (guild) => {
    const members = await guild.members.fetch();
    
    return {
        totalUsers: guild.memberCount,
        onlineUsers: members.filter(member => 
            member.presence?.status === 'online' || 
            member.presence?.status === 'dnd' || 
            member.presence?.status === 'idle'
        ).size,
        botCount: members.filter(member => member.user.bot).size,
        channelCount: guild.channels.cache.size,
        textChannels: guild.channels.cache.filter(c => c.type === 0).size,
        voiceChannels: guild.channels.cache.filter(c => c.type === 2).size,
        roleCount: guild.roles.cache.size,
    };
};

module.exports = {
    getServerStats
};
