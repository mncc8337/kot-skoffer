from discord import Interaction, Message
from discord import app_commands
from discord.ext.commands import GroupCog
from discord.ext import commands
from lib.noitu import NoiTu
import os


class NoiTuCog(GroupCog, group_name="noitu"):
    def __init__(self, bot):
        self.bot = bot
        self.noitu = NoiTu(os.getenv("USER_AGENT"))

    @app_commands.command(
        name="batdau", description="bắt đầu game mới. chỉ dùng được trong DM"
    )
    async def batdau(self, interaction: Interaction):
        await self.noitu.batdau(interaction)

    @app_commands.command(
        name="ketthuc", description="kết thúc game. chỉ dùng được trong DM"
    )
    async def ketthuc(self, interaction: Interaction):
        await self.noitu.ketthuc(interaction)

    @app_commands.command(
        name="gameloop",
        description="bắt đầu / kết thúc vòng lặp game. chỉ dùng được trong server",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def gameloop(self, interaction: Interaction):
        await self.noitu.gameloop(interaction)

    @app_commands.command(
        name="boqua",
        description="bỏ qua vòng chơi hiện tại. server cần phải có 3 người chạy lệnh này",
    )
    async def boqua(self, interaction: Interaction):
        await self.noitu.boqua(interaction)

    @app_commands.command(name="chuoi", description="in ra chuỗi từ hiện tại")
    async def chuoi(self, interaction: Interaction):
        await self.noitu.chuoi(interaction)

    @app_commands.command(name="tuky", description="chơi với bot. chỉ dùng trong server")
    async def tuky(self, interaction: Interaction):
        await self.noitu.tuky(interaction, self.bot)

    @app_commands.command(name="dinhnghia", description="lấy định nghĩa của 1 từ")
    @app_commands.describe(
        tu="từ cần định nghĩa",
    )
    async def dinhnghia(self, interaction: Interaction, tu: str):
        await self.noitu.dinhnghia(interaction, tu)

    @app_commands.command(
        name="noitiep",
        description="gợi ý các từ để nối tiếp. không thể dùng được nếu có gêm đang diễn ra",
    )
    @app_commands.describe(
        chu="chữ bắt đầu",
    )
    async def noitiep(self, interaction: Interaction, chu: str):
        await self.noitu.noitiep(interaction, chu)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        async with message.channel.typing():
            await self.noitu.handle_gameloop_message(self.bot, message)
