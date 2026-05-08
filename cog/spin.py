from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from lib.lucky_wheel import LuckyWheel
from typing import Optional


class SpinCog(GroupCog, group_name="spin"):
    def __init__(self, bot):
        self.bot = bot
        self.wheel = LuckyWheel("data/lucky_wheel.json")

    @app_commands.command(name="spin", description="spin the lucky wheel")
    async def spin(self, interaction: Interaction):
        await self.wheel.spin(interaction)
        self.wheel.save()

    @app_commands.command(name="add", description="add an item to lucky wheel")
    async def dd(
        self,
        interaction: Interaction,
        name: str,
        value: int,
        weight: Optional[int] = 1
    ):
        self.wheel.add(name, value, weight, interaction)
        await interaction.response.send_message(f"item {name} added")

        self.wheel.save()

    @app_commands.command(name="remove", description="remove an item from lucky wheel")
    async def remove(self, interaction: Interaction, name: str):
        if name not in self.wheel.get_data(interaction)["item"].keys():
            await interaction.response.send_message("no such item " + name)
        self.wheel.remove(name, interaction)
        await interaction.response.send_message(f"item \"{name}\" removed")

        self.wheel.save()

    @app_commands.command(name="set_weight", description="set new weight for an item")
    async def set_weight(
        self,
        interaction: Interaction,
        name: str,
        weight: int
    ):
        if weight <= 0:
            await interaction.response.send_message(
                content="invalid weight, must be a positive integer",
                ephemeral=True,
            )
            return

        self.wheel.set_weight(name, weight, interaction)
        await interaction.response.send_message(f"item {name}'s weight set to {weight}")

        self.wheel.save()

    @app_commands.command(name="set_value", description="set new value for an item")
    async def set_value(
        self,
        interaction: Interaction,
        name: str,
        value: int
    ):
        self.wheel.set_value(name, value, interaction)
        await interaction.response.send_message(f"item {name}'s value set to {value}")

        self.wheel.save()

    @app_commands.command(name="list", description="list all item in the lucky wheel")
    async def list(self, interaction: Interaction):
        await self.wheel.list(interaction)

    @app_commands.command(name="user", description="show lucky wheel score of all users")
    async def user(self, interaction: Interaction):
        await self.wheel.user(interaction)
