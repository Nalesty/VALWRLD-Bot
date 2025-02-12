const { ActivityType } = require('discord.js');
const { setupStatsChannels, updateStatsChannels } = require('../utils/channelStats.js');
const { statsUpdateInterval } = require('../config.js');

module.exports = {
    name: 'ready',
    once: true,
    async execute(client) {
        console.log(`Bot connecté en tant que ${client.user.tag}`);

        client.user.setPresence({
            activities: [{
                name: '/help pour les commandes',
                type: ActivityType.Playing
            }],
            status: 'online'
        });

        // Initialisation des channels de stats pour chaque serveur
        for (const guild of client.guilds.cache.values()) {
            try {
                await setupStatsChannels(guild);
                // Mise à jour périodique des stats
                setInterval(() => updateStatsChannels(guild), statsUpdateInterval);
            } catch (error) {
                console.error(`Erreur lors de l'initialisation des stats pour ${guild.name}:`, error);
            }
        }
    },
};