const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');

// Chemin vers le fichier de sauvegarde
const POLLS_FILE = path.join(__dirname, '../data/polls.json');

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
    name: 'interactionCreate',
    async execute(interaction) {
        try {
            if (!interaction.isButton()) return;

            const [type, pollId, optionIndex] = interaction.customId.split('_');
            if (type !== 'poll') return;

            const pollData = interaction.client.polls.get(interaction.message.id);
            if (!pollData) {
                return await interaction.reply({
                    content: '❌ Ce sondage n\'existe plus.',
                    ephemeral: true
                });
            }

            // Vérifier si le sondage est terminé
            if (pollData.endTime && Date.now() > pollData.endTime) {
                return await interaction.reply({
                    content: '❌ Ce sondage est terminé.',
                    ephemeral: true
                });
            }

            // Vérifier si l'utilisateur a déjà voté
            if (pollData.voters.includes(interaction.user.id)) {
                return await interaction.reply({
                    content: '❌ Vous avez déjà voté sur ce sondage.',
                    ephemeral: true
                });
            }

            // Enregistrer le vote
            pollData.votes[optionIndex]++;
            pollData.voters.push(interaction.user.id);

            // Sauvegarder les modifications
            interaction.client.polls.set(interaction.message.id, pollData);
            savePolls(interaction.client.polls);

            // Mettre à jour les boutons
            const buttons = pollData.options.map((option, index) => {
                return new ButtonBuilder()
                    .setCustomId(`poll_${pollId}_${index}`)
                    .setLabel(`${option} (${pollData.votes[index]})`)
                    .setStyle(ButtonStyle.Primary);
            });

            // Organiser les boutons en lignes
            const rows = [];
            for (let i = 0; i < buttons.length; i += 2) {
                const row = new ActionRowBuilder().addComponents(buttons.slice(i, i + 2));
                rows.push(row);
            }

            // Mettre à jour l'embed avec les résultats actuels
            const embed = EmbedBuilder.from(interaction.message.embeds[0]);

            // Mettre à jour le message
            await interaction.message.edit({
                embeds: [embed],
                components: rows
            });

            // Confirmer le vote
            await interaction.reply({
                content: '✅ Votre vote a été enregistré !',
                ephemeral: true
            });

        } catch (error) {
            console.error('Erreur lors du traitement du vote:', error);
            await interaction.reply({
                content: '❌ Une erreur est survenue lors du traitement de votre vote.',
                ephemeral: true
            }).catch(() => {});
        }
    }
};