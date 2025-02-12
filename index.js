const { Client, GatewayIntentBits, Collection } = require('discord.js');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Configuration du client avec les intents nécessaires
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildVoiceStates,
        GatewayIntentBits.GuildMessageReactions
    ]
});

// Collections pour stocker les commandes et les données
client.commands = new Collection();
client.polls = new Collection();

// Charger les sondages sauvegardés
const pollsPath = path.join(__dirname, 'data/polls.json');
try {
    if (fs.existsSync(pollsPath)) {
        const pollsData = JSON.parse(fs.readFileSync(pollsPath, 'utf8'));
        Object.entries(pollsData).forEach(([key, value]) => {
            client.polls.set(key, value);
        });
        console.log('✅ Sondages chargés depuis la sauvegarde');
    }
} catch (error) {
    console.error('⚠️ Erreur lors du chargement des sondages:', error);
}

// Chargement des commandes
const commandsPath = path.join(__dirname, 'commands');
const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));

for (const file of commandFiles) {
    const command = require(path.join(commandsPath, file));
    if ('data' in command && 'execute' in command) {
        client.commands.set(command.data.name, command);
        console.log(`✅ Commande chargée: ${command.data.name}`);
    } else {
        console.log(`⚠️ La commande ${file} manque de propriétés requises.`);
    }
}

// Chargement des événements
const eventsPath = path.join(__dirname, 'events');
const eventFiles = fs.readdirSync(eventsPath).filter(file => file.endsWith('.js'));

for (const file of eventFiles) {
    const event = require(path.join(eventsPath, file));
    if (event.once) {
        client.once(event.name, (...args) => event.execute(...args));
    } else {
        client.on(event.name, (...args) => event.execute(...args));
    }
    console.log(`✅ Événement chargé: ${event.name}`);
}

// Gestion des interactions
client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    const command = client.commands.get(interaction.commandName);
    if (!command) return;

    try {
        await command.execute(interaction);
    } catch (error) {
        console.error(`Erreur dans la commande ${interaction.commandName}:`, error);
        const reponse = {
            content: 'Une erreur est survenue lors de l\'exécution de la commande.',
            ephemeral: true
        };

        if (interaction.replied || interaction.deferred) {
            await interaction.followUp(reponse);
        } else {
            await interaction.reply(reponse);
        }
    }
});

// Connexion du bot
client.login(process.env.TOKEN).then(() => {
    console.log(`Bot connecté en tant que ${client.user.tag}`);
}).catch(error => {
    console.error('Erreur de connexion:', error);
});