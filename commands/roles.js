const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('role')
        .setDescription('Gestion des rôles')
        .addSubcommand(subcommand =>
            subcommand
                .setName('add')
                .setDescription('Ajouter un rôle à un membre')
                .addUserOption(option =>
                    option.setName('utilisateur')
                        .setDescription('L\'utilisateur')
                        .setRequired(true))
                .addRoleOption(option =>
                    option.setName('role')
                        .setDescription('Le rôle à ajouter')
                        .setRequired(true)))
        .addSubcommand(subcommand =>
            subcommand
                .setName('remove')
                .setDescription('Retirer un rôle d\'un membre')
                .addUserOption(option =>
                    option.setName('utilisateur')
                        .setDescription('L\'utilisateur')
                        .setRequired(true))
                .addRoleOption(option =>
                    option.setName('role')
                        .setDescription('Le rôle à retirer')
                        .setRequired(true)))
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageRoles),

    async execute(interaction) {
        const subcommand = interaction.options.getSubcommand();
        const user = interaction.options.getUser('utilisateur');
        const role = interaction.options.getRole('role');
        const member = interaction.guild.members.cache.get(user.id);

        if (!member) {
            return interaction.reply({
                content: 'Membre introuvable.',
                ephemeral: true
            });
        }

        try {
            if (subcommand === 'add') {
                await member.roles.add(role);
                await interaction.reply({
                    content: `Le rôle ${role} a été ajouté à ${user}.`,
                    ephemeral: true
                });
            } else if (subcommand === 'remove') {
                await member.roles.remove(role);
                await interaction.reply({
                    content: `Le rôle ${role} a été retiré de ${user}.`,
                    ephemeral: true
                });
            }
        } catch (error) {
            await interaction.reply({
                content: 'Une erreur est survenue lors de la modification des rôles.',
                ephemeral: true
            });
        }
    },
};
