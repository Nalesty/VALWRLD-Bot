import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
        self.invites_file = "data/invites.json"
        self.load_invites()

    def load_invites(self):
        """Charger les données des invitations"""
        try:
            with open(self.invites_file, 'r') as f:
                self.invites = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.invites = {}
            self.save_invites()

    def save_invites(self):
        """Sauvegarder les données des invitations"""
        with open(self.invites_file, 'w') as f:
            json.dump(self.invites, f, indent=4)

    async def cache_invites(self, guild):
        """Mettre en cache les invitations actuelles du serveur"""
        guild_invites = await guild.invites()
        self.invites[str(guild.id)] = {
            invite.code: {
                "uses": invite.uses,
                "inviter": str(invite.inviter.id) if invite.inviter else None,
                "created_at": invite.created_at.isoformat(),
                "max_uses": invite.max_uses,
                "expires_at": invite.expires_at.isoformat() if invite.expires_at else None
            } for invite in guild_invites
        }
        self.save_invites()

    @commands.Cog.listener()
    async def on_ready(self):
        """Mettre en cache les invitations de tous les serveurs au démarrage"""
        for guild in self.bot.guilds:
            try:
                await self.cache_invites(guild)
            except discord.Forbidden:
                print(f"Pas la permission de voir les invitations sur {guild.name}")

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Mettre à jour le cache quand une nouvelle invitation est créée"""
        guild_id = str(invite.guild.id)
        if guild_id not in self.invites:
            self.invites[guild_id] = {}

        self.invites[guild_id][invite.code] = {
            "uses": invite.uses,
            "inviter": str(invite.inviter.id) if invite.inviter else None,
            "created_at": invite.created_at.isoformat(),
            "max_uses": invite.max_uses,
            "expires_at": invite.expires_at.isoformat() if invite.expires_at else None
        }
        self.save_invites()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Détecter quelle invitation a été utilisée quand un membre rejoint"""
        guild = member.guild
        guild_id = str(guild.id)
        try:
            # Récupérer les invitations actuelles
            new_invites = await guild.invites()
            old_invites = self.invites.get(guild_id, {})

            # Trouver l'invitation qui a été utilisée
            for invite in new_invites:
                if invite.code in old_invites:
                    if invite.uses > old_invites[invite.code]["uses"]:
                        inviter_id = old_invites[invite.code]["inviter"]
                        if inviter_id:
                            inviter = guild.get_member(int(inviter_id))
                            if inviter:
                                # Mettre à jour les statistiques de l'inviteur
                                if "inviter_stats" not in self.invites[guild_id]:
                                    self.invites[guild_id]["inviter_stats"] = {}

                                if inviter_id not in self.invites[guild_id]["inviter_stats"]:
                                    self.invites[guild_id]["inviter_stats"][inviter_id] = {
                                        "total_invites": 0,
                                        "valid_invites": 0,
                                        "left_members": 0,
                                        "history": []
                                    }

                                stats = self.invites[guild_id]["inviter_stats"][inviter_id]
                                stats["total_invites"] += 1
                                stats["valid_invites"] += 1
                                stats["history"].append({
                                    "member_id": str(member.id),
                                    "joined_at": datetime.now().isoformat()
                                })

                                # Créer l'embed de bienvenue avec l'information sur l'invitation
                                embed = discord.Embed(
                                    title="👋 Nouveau membre",
                                    description=f"{member.mention} a été invité par {inviter.mention}",
                                    color=discord.Color.green(),
                                    timestamp=datetime.now()
                                )
                                embed.set_thumbnail(url=member.display_avatar.url)
                                embed.add_field(
                                    name="📊 Statistiques de l'inviteur",
                                    value=f"Total: {stats['total_invites']}\nActifs: {stats['valid_invites']}\nPartis: {stats['left_members']}"
                                )

                                # Trouver un salon approprié pour envoyer l'information
                                system_channel = guild.system_channel
                                if system_channel:
                                    await system_channel.send(embed=embed)

                                self.save_invites()
                                break

            # Mettre à jour le cache
            await self.cache_invites(guild)

        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Mettre à jour les statistiques quand un membre quitte"""
        guild_id = str(member.guild.id)
        if guild_id in self.invites and "inviter_stats" in self.invites[guild_id]:
            # Chercher qui a invité ce membre
            for inviter_id, stats in self.invites[guild_id]["inviter_stats"].items():
                for invite in stats["history"]:
                    if invite["member_id"] == str(member.id):
                        stats["valid_invites"] -= 1
                        stats["left_members"] += 1
                        self.save_invites()
                        break

    @app_commands.command(name="invites", description="Voir vos statistiques d'invitations")
    async def view_invites(self, interaction: discord.Interaction, membre: discord.Member = None):
        """Voir les statistiques d'invitations d'un membre"""
        target = membre or interaction.user
        guild_id = str(interaction.guild.id)

        # Récupérer les statistiques d'invitation
        if guild_id in self.invites and "inviter_stats" in self.invites[guild_id]:
            stats = self.invites[guild_id]["inviter_stats"].get(str(target.id), {
                "total_invites": 0,
                "valid_invites": 0,
                "left_members": 0,
                "history": []
            })
        else:
            stats = {
                "total_invites": 0,
                "valid_invites": 0,
                "left_members": 0,
                "history": []
            }

        # Récupérer les invitations actives
        guild_invites = await interaction.guild.invites()
        active_invites = [invite for invite in guild_invites if invite.inviter and invite.inviter.id == target.id]

        # Créer l'embed
        embed = discord.Embed(
            title=f"📊 Statistiques d'invitations de {target.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="Total d'invitations",
            value=f"• Total: {stats['total_invites']}\n• Actifs: {stats['valid_invites']}\n• Partis: {stats['left_members']}",
            inline=True
        )
        embed.add_field(
            name="Invitations actives",
            value=str(len(active_invites)),
            inline=True
        )

        if active_invites:
            invites_text = ""
            for invite in active_invites[:5]:
                expiration = f"(Expire: <t:{int(invite.expires_at.timestamp())}:R>)" if invite.expires_at else ""
                uses_text = f"{invite.uses}/{invite.max_uses}" if invite.max_uses else f"{invite.uses}/∞"
                invites_text += f"• discord.gg/{invite.code} : {uses_text} {expiration}\n"
            embed.add_field(
                name="Dernières invitations",
                value=invites_text,
                inline=False
            )

        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="createinvite", description="Créer une invitation temporaire")
    @app_commands.describe(
        duree="Durée de validité (ex: 1h, 2d)",
        max_uses="Nombre maximum d'utilisations",
        raison="Raison de la création de l'invitation"
    )
    async def create_invite(
        self,
        interaction: discord.Interaction,
        duree: str = None,
        max_uses: int = None,
        raison: str = None
    ):
        """Créer une invitation temporaire"""
        try:
            # Convertir la durée si spécifiée
            expires_in = None
            if duree:
                unit = duree[-1].lower()
                value = int(duree[:-1])
                if unit == 'h':
                    expires_in = timedelta(hours=value)
                elif unit == 'd':
                    expires_in = timedelta(days=value)
                else:
                    return await interaction.response.send_message(
                        "❌ Format de durée invalide. Utilisez h pour les heures ou d pour les jours (ex: 2h, 1d)",
                        ephemeral=True
                    )

            # Créer l'invitation
            invite = await interaction.channel.create_invite(
                max_age=int(expires_in.total_seconds()) if expires_in else None,
                max_uses=max_uses,
                reason=f"Créée par {interaction.user} - {raison}" if raison else f"Créée par {interaction.user}"
            )

            embed = discord.Embed(
                title="✨ Invitation créée",
                description=f"discord.gg/{invite.code}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )

            if expires_in:
                embed.add_field(
                    name="Expire",
                    value=f"<t:{int((datetime.now() + expires_in).timestamp())}:R>",
                    inline=True
                )

            if max_uses:
                embed.add_field(
                    name="Utilisations max",
                    value=str(max_uses),
                    inline=True
                )

            if raison:
                embed.add_field(
                    name="Raison",
                    value=raison,
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "❌ Format de durée invalide",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas la permission de créer des invitations",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))