const { SlashCommandBuilder, PermissionFlagsBits, ChannelType } = require('discord.js');
const { createModEmbed } = require('../utils/embeds.js');
const { modLogChannel } = require('../config.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('mod')
        .setDescription('Commandes de modération')
        .addSubcommand(subcommand =>
            subcommand
                .setName('kick')
                .setDescription('Expulser un membre')
                .addUserOption(option =>
                    option.setName('utilisateur')
                        .setDescription('L\'utilisateur à expulser')
                        .setRequired(true))
                .addStringOption(option =>
                    option.setName('raison')
                        .setDescription('Raison de l\'expulsion')))
        .addSubcommand(subcommand =>
            subcommand
                .setName('ban')
                .setDescription('Bannir un membre')
                .addUserOption(option =>
                    option.setName('utilisateur')
                        .setDescription('L\'utilisateur à bannir')
                        .setRequired(true))
                .addStringOption(option =>
                    option.setName('raison')
                        .setDescription('Raison du bannissement')))
        .addSubcommand(subcommand =>
            subcommand
                .setName('clear')
                .setDescription('Supprimer des messages')
                .addIntegerOption(option =>
                    option.setName('nombre')
                        .setDescription('Nombre de messages à supprimer')
                        .setRequired(true)
                        .setMinValue(1)
                        .setMaxValue(100)))
        .addSubcommand(subcommand =>
            subcommand
                .setName('move')
                .setDescription('Déplacer un membre vers un autre salon vocal')
                .addUserOption(option =>
                    option.setName('utilisateur')
                        .setDescription('L\'utilisateur à déplacer')
                        .setRequired(true))
                .addChannelOption(option =>
                    option.setName('salon')
                        .setDescription('Le salon vocal de destination')
                        .setRequired(true)
                        .addChannelTypes(ChannelType.GuildVoice)))
        .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers),

    async execute(interaction) {
        // Vérification du channel de logs
        const logChannel = interaction.guild.channels.cache.find(
            channel => channel.name === modLogChannel
        ) || await interaction.guild.channels.create({
            name: modLogChannel,
            type: ChannelType.GuildText,
            permissionOverwrites: [
                {
                    id: interaction.guild.id,
                    deny: [PermissionFlagsBits.SendMessages],
                    allow: [PermissionFlagsBits.ViewChannel]
                }
            ]
        });

        const subcommand = interaction.options.getSubcommand();
        const user = interaction.options.getUser('utilisateur');
        const reason = interaction.options.getString('raison') || 'Aucune raison fournie';
        const member = user ? interaction.guild.members.cache.get(user.id) : null;

        try {
            switch (subcommand) {
                case 'kick':
                    if (!member) {
                        return interaction.reply({
                            content: '❌ Membre introuvable.',
                            ephemeral: true
                        });
                    }
                    await member.kick(reason);
                    await interaction.reply({
                        embeds: [createModEmbed('Expulsion', user, interaction.user, reason)]
                    });
                    break;

                case 'ban':
                    if (!member) {
                        return interaction.reply({
                            content: '❌ Membre introuvable.',
                            ephemeral: true
                        });
                    }
                    await member.ban({ reason });
                    await interaction.reply({
                        embeds: [createModEmbed('Bannissement', user, interaction.user, reason)]
                    });
                    break;

                case 'clear':
                    const amount = interaction.options.getInteger('nombre');
                    const messages = await interaction.channel.bulkDelete(amount, true);
                    await interaction.reply({
                        content: `✅ ${messages.size} messages ont été supprimés.`,
                        ephemeral: true
                    });
                    break;

                case 'move':
                    if (!member) {
                        return interaction.reply({
                            content: '❌ Membre introuvable.',
                            ephemeral: true
                        });
                    }
                    const channel = interaction.options.getChannel('salon');
                    if (!member.voice.channel) {
                        return interaction.reply({
                            content: '❌ Ce membre n\'est pas dans un salon vocal.',
                            ephemeral: true
                        });
                    }
                    await member.voice.setChannel(channel);
                    await interaction.reply({
                        content: `✅ ${member} a été déplacé vers ${channel}.`,
                        ephemeral: true
                    });
                    break;
            }

            // Log de l'action
            if (subcommand !== 'clear') {
                await logChannel.send({
                    embeds: [createModEmbed(
                        subcommand === 'move' ? 'Déplacement' : 
                        subcommand === 'kick' ? 'Expulsion' : 'Bannissement',
                        user,
                        interaction.user,
                        reason
                    )]
                });
            }
        } catch (error) {
            console.error(error);
            await interaction.reply({
                content: '❌ Une erreur est survenue lors de l\'exécution de la commande.',
                ephemeral: true
            });
        }
    },
};