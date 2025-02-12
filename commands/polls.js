const { SlashCommandBuilder, EmbedBuilder, ButtonBuilder, ButtonStyle, ActionRowBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

// Chemin vers le fichier de sauvegarde
const POLLS_FILE = path.join(__dirname, '../data/polls.json');

// Fonction pour charger les sondages
function loadPolls() {
    try {
        if (fs.existsSync(POLLS_FILE)) {
            const data = fs.readFileSync(POLLS_FILE, 'utf8');
            return new Map(Object.entries(JSON.parse(data)));
        }
    } catch (error) {
        console.error('Erreur lors du chargement des sondages:', error);
    }
    return new Map();
}

// Fonction pour sauvegarder les sondages
function savePolls(polls) {
    try {
        const directory = path.dirname(POLLS_FILE);
        if (!fs.existsSync(directory)) {
            fs.mkdirSync(directory, { recursive: true });
        }
        fs.writeFileSync(POLLS_FILE, JSON.stringify(Object.fromEntries(polls)), 'utf8');
    } catch (error) {
        console.error('Erreur lors de la sauvegarde des sondages:', error);
    }
}

module.exports = {
    data: new SlashCommandBuilder()
        .setName('sondage')
        .setDescription('Créer un sondage interactif')
        .addStringOption(option =>
            option.setName('question')
                .setDescription('La question du sondage')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('option1')
                .setDescription('Première option')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('option2')
                .setDescription('Deuxième option')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('option3')
                .setDescription('Troisième option (optionnel)'))
        .addStringOption(option =>
            option.setName('option4')
                .setDescription('Quatrième option (optionnel)'))
        .addStringOption(option =>
            option.setName('duree')
                .setDescription('Durée du sondage (ex: 1h, 2d)')),

    async execute(interaction) {
        try {
            const question = interaction.options.getString('question');
            const options = [
                interaction.options.getString('option1'),
                interaction.options.getString('option2'),
                interaction.options.getString('option3'),
                interaction.options.getString('option4')
            ].filter(Boolean);
            const duration = interaction.options.getString('duree');

            // Créer l'embed
            const embed = new EmbedBuilder()
                .setTitle('📊 ' + question)
                .setColor('#3498db')
                .setTimestamp()
                .setFooter({ text: `Créé par ${interaction.user.tag}` });

            // Créer les boutons
            const buttons = options.map((option, index) => {
                return new ButtonBuilder()
                    .setCustomId(`poll_${interaction.id}_${index}`)
                    .setLabel(`${option} (0)`)
                    .setStyle(ButtonStyle.Primary);
            });

            // Organiser les boutons en lignes
            const rows = [];
            for (let i = 0; i < buttons.length; i += 2) {
                const row = new ActionRowBuilder().addComponents(buttons.slice(i, i + 2));
                rows.push(row);
            }

            // Stocker les données du sondage
            const pollData = {
                question,
                options,
                votes: Array(options.length).fill(0),
                voters: [],
                author: interaction.user.id,
                endTime: duration ? Date.now() + parseDuration(duration) : null
            };

            // Ajouter la durée à l'embed si spécifiée
            if (duration) {
                const endTime = new Date(pollData.endTime);
                embed.addFields({
                    name: 'Se termine',
                    value: `<t:${Math.floor(endTime.getTime() / 1000)}:R>`,
                    inline: false
                });
            }

            // Envoyer le sondage
            const message = await interaction.reply({
                embeds: [embed],
                components: rows,
                fetchReply: true
            });

            // Stocker les données du sondage et sauvegarder
            interaction.client.polls.set(message.id, pollData);
            savePolls(interaction.client.polls);

        } catch (error) {
            console.error('Erreur lors de la création du sondage:', error);
            await interaction.reply({
                content: '❌ Une erreur est survenue lors de la création du sondage.',
                ephemeral: true
            });
        }
    }
};

function parseDuration(duration) {
    const unit = duration.slice(-1).toLowerCase();
    const value = parseInt(duration.slice(0, -1));

    switch (unit) {
        case 'h':
            return value * 3600000; // heures en ms
        case 'd':
            return value * 86400000; // jours en ms
        default:
            return 0;
    }
}