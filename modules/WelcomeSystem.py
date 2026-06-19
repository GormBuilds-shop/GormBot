from discord.ext.commands import Cog, Bot
from discord import Member
from utils.Constants import MAIN_GUILD_ID, NEWBIE_ROLE_ID

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import GormBot


class WelcomeSystem(Cog):
    def __init__(self, bot: 'GormBot'):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: Member):
        guild = member.guild

        if guild.id != MAIN_GUILD_ID:
            return

        role = guild.get_role(NEWBIE_ROLE_ID)
        if role is None:
            self.bot.logger.warning("Newbie role no longer exists, new members wont receive a role")
            return

        await member.add_roles(role, reason="new member")


def setup(bot: Bot):
    bot.add_cog(WelcomeSystem(bot))
