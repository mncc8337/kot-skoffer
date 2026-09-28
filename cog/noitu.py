from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from lib.noitu import NoiTu
import os


class NoiTuCog(GroupCog, group_name="noitu"):
    def __init__(self, bot):
        self.bot = bot
        self.noitu = NoiTu(os.getenv("USER_AGENT"))

    @app_commands.command(name="dinhnghia", description="lấy định nghĩa của 1 từ")
    @app_commands.describe(
        tu="từ cần định nghĩa",
    )
    async def dinhnghia(self, interaction: Interaction, tu: str):
        await self.noitu.dinhnghia(interaction, tu)

    @app_commands.command(name="noitiep", description="gợi ý các từ để nối tiếp")
    @app_commands.describe(
        chu="chữ bắt đầu",
    )
    async def noitiep(self, interaction: Interaction, chu: str):
        await self.noitu.noitiep(interaction, chu)
