import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from typing import Optional

from lib import image_process
from PIL import Image

import re
import io


HEX_REGEX = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'


class ImageCog(GroupCog, group_name="image"):
    def __init__(self, bot):
        self.bot = bot

    async def reduce_size(self, image: Image.Image, max_file_size=10 * 1024 * 1024):
        width, height = image.size

        while True:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            size_in_bytes = buffer.tell()

            if size_in_bytes <= max_file_size:
                buffer.seek(0)
                return buffer, size_in_bytes

            width = int(width * 0.9)
            height = int(height * 0.9)
            image = image.resize((width, height), Image.Resampling.LANCZOS)

            if width < 100 or height < 100:
                break

        buffer.seek(0)
        return buffer, size_in_bytes


    async def send_image(self, interaction: Interaction, image: Image, name: str):
        image.save("images/" + name + ".png", format="PNG")
        buffer, fsize = await self.reduce_size(image)
        if fsize > 10 * 1024 * 1024:
            await interaction.followup.send("file size too large", ephemeral=True)
            return
        discord_file = discord.File(fp=buffer, filename=name + "..jpeg")
        await interaction.followup.send(file=discord_file)

    @app_commands.command(name="text", description="get an image with texts")
    @app_commands.describe(
        text="the content of the image",
        size="font size",
        bg="background color, hex value e.g #aabbcc",
        fg="foreground color, hex value e.g #aabbcc",
        use_bold="include this arg and type anything to use bold font",
    )
    async def text(
        self,
        interaction: Interaction,
        text: str,
        size: Optional[int],
        bg: Optional[str],
        fg: Optional[str],
        use_bold: Optional[str]
    ):
        if not size:
            size = 32

        if not bg:
            bg = "#ffffff"
        elif not re.match(HEX_REGEX, bg):
            await interaction.response.send_message(
                content="bg value is invalid",
                ephemeral=True,
            )
            return
        if not fg:
            fg = "#000000"
        elif not re.match(HEX_REGEX, fg):
            await interaction.response.send_message(
                content="fg value is invalid",
                ephemeral=True,
            )
            return

        bold = False
        if use_bold:
            bold = True

        await interaction.response.defer()

        await self.send_image(
            interaction,
            image_process.text(text, size, bg, fg, bold),
            text
        )

    @app_commands.command(name="asciify", description="asciify image")
    @app_commands.describe(
        bg_influence="how much the color of text will affect the bg. ranging from 0.0 to 1.0",
        no_color_mode="black and white mode. include this and type anything to enable",
    )
    async def asciify(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        character_size: Optional[int],
        bg_influence: Optional[float],
        no_color_mode: Optional[str],
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        if not character_size:
            character_size = 8
        if not bg_influence:
            bg_influence = 0.1
        else:
            bg_influence = max(min(bg_influence, 1.0), 0.0)

        no_color = False
        if no_color_mode:
            no_color = True

        if no_color:
            bg_influence = 0

        await interaction.response.defer()

        res_image = image_process.asciify(
            Image.open(io.BytesIO(await image_attachment.read())),
            character_size,
            bg_influence,
            no_color
        )
        await self.send_image(
            interaction,
            res_image,
            image_attachment.filename + f".{character_size}-{bg_influence}"
        )
