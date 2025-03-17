import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from typing import Optional

import os
import random
import lib.random_name as random_name


class RandomCog(GroupCog, group_name="random"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="roll",
        description="get some random number in specified range"
    )
    @app_commands.describe(
        lbound="lower bound",
        hbound="higher bound",
        times="how many rolls",
    )
    async def roll(
        self,
        interaction: Interaction,
        lbound: Optional[int],
        hbound: Optional[int],
        times: Optional[int],
    ):
        if not lbound:
            lbound = 1
        if not hbound:
            hbound = 6
        if not times:
            times = 1

        rolls = ""
        rolls += str(random.randint(lbound, hbound)) + " "

        await interaction.response.send_message(rolls)
        for _ in range(times - 1):
            rolls += str(random.randint(lbound, hbound)) + " "
            await interaction.edit_original_response(content=rolls)

    @app_commands.command(
        name="catname",
        description="get random cat name"
    )
    async def catname(self, interaction: Interaction):
        await interaction.response.send_message(await random_name.generate_cat_name())

    @app_commands.command(
        name="name",
        description="get random human name"
    )
    async def name(self, interaction: Interaction):
        await interaction.response.send_message(await random_name.generate_human_name())

    @app_commands.command(name="image", description="get random image")
    async def image(self, interaction: Interaction):
        pwd = "./images"
        item: str = ""

        def listdir(path):
            lst = os.listdir(path)
            new_lst = []
            for item in lst:
                _, ext = os.path.splitext(item)
                if (
                    ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")
                    or os.path.isdir(os.path.join(path, item))
                ):
                    new_lst.append(item)

            return new_lst

        while (
            item == ""
            or (
                len(listdir(pwd))
                and os.path.isdir(os.path.join(pwd, item))
            )
        ):
            pwd = os.path.join(pwd, item)
            item = random.choice(listdir(pwd))

        if item == "":
            await interaction.response.send_message("no image to choose")
            return

        file = discord.File(os.path.join(pwd, item))
        await interaction.response.send_message(file=file)
