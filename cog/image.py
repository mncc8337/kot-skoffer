import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from typing import Optional

from lib import image_process
from PIL import Image

import re
import io
import requests


HEX_REGEX = r'^#([A-Fa-f0-9]{8}|[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'


class ImageCog(GroupCog, group_name="image"):
    def __init__(self, bot):
        self.bot = bot

    def post_to_0x0st(self, file_path):
        response = None
        with open(file_path, "rb") as file:
            response = requests.post(
                "https://0x0.st",
                files={"file": file},
                headers={"User-Agent": "kot-skoffer"}
            )

        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"kot: failed to post image {file_path}. {response.text}")
            return None

    async def send_high_quality_image(self, interaction: Interaction, image: Image, name: str):
        image.save("images/image_process/" + name + ".png", format="PNG")

        buffer, _ = image_process.reduce_size(image)
        discord_file = discord.File(fp=buffer, filename=name + ".png")

        image_url = self.post_to_0x0st("images/image_process/" + name + ".png")
        if image_url:
            msg = f"""done processing. sent with full quality via 0x0.st and low quality via attachment.
[full image at 0x0.st]({image_url}).
**NOTE:** the high quality one will be deleted after 30 days"""
            await interaction.followup.send(msg, file=discord_file)
        else:
            await interaction.followup.send("done processing. unable to send the high quality one, sent with low quality via attachment instead.", file=discord_file)

    async def send_image(self, interaction: Interaction, image: Image, name: str):
        buffer, _ = image_process.reduce_size(image)
        discord_file = discord.File(fp=buffer, filename=name + ".png")
        await interaction.followup.send(file=discord_file)

    @app_commands.command(name="text", description="get an image with texts")
    @app_commands.describe(
        text="the content of the image",
        size="font size. default: 32",
        bg="background color, hex value e.g #aabbccdd or #aabbcc or #abc. default: #ffffff",
        fg="foreground color, hex value e.g #aabbccdd or #aabbcc or #abc. default: #000000",
        bold="use bold font. default: False",
    )
    async def text(
        self,
        interaction: Interaction,
        text: str,
        size: Optional[int] = 32,
        bg: Optional[str] = "#ffffff",
        fg: Optional[str] = "#000000",
        bold: Optional[bool] = False
    ):
        if not re.match(HEX_REGEX, bg):
            await interaction.response.send_message(
                content="bg value is invalid",
                ephemeral=True,
            )
            return

        if not re.match(HEX_REGEX, fg):
            await interaction.response.send_message(
                content="fg value is invalid",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        await self.send_image(
            interaction,
            image_process.text(text, size, bg, fg, bold),
            text
        )

    @app_commands.command(name="asciify", description="asciify image")
    @app_commands.describe(
        character_size="size of characters. default: 8",
        bg_influence="how much the color of text will affect the bg. ranging from 0.0 to 1.0. default: 0.3",
        no_color="black and white mode. default: False",
        chars_only="only draw characters. default: False",
    )
    async def asciify(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        character_size: Optional[int] = 8,
        bg_influence: Optional[float] = 0.3,
        no_color: Optional[bool] = False,
        chars_only: Optional[bool] = False,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        bg_influence = max(min(bg_influence, 1.0), 0.0)

        if no_color:
            bg_influence = 0

        await interaction.response.defer()

        res_image = image_process.asciify(
            Image.open(io.BytesIO(await image_attachment.read())),
            character_size,
            bg_influence,
            no_color,
            chars_only,
        )

        await self.send_high_quality_image(
            interaction,
            res_image,
            image_attachment.filename + f".{character_size}-{bg_influence}"
        )
