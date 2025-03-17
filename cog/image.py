import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from typing import Optional

import re
import json
import random
import io
from PIL import Image, ImageDraw, ImageFont


HEX_REGEX = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
PALLETE: dict = None
PALLETE_COUNT: int

with open("visual_density.json", "r") as f:
    PALLETE = json.load(f)
PALLETE_COUNT = len(PALLETE["visual_density"])


class ImageCog(GroupCog, group_name="image"):
    def __init__(self, bot):
        self.bot = bot

    async def send_image(self, interaction: Interaction, image: Image):
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        discord_file = discord.File(fp=buffer, filename="image.png")
        await interaction.response.send_message(file=discord_file)

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

        font = None
        if not bold:
            font = ImageFont.truetype("ubuntu-font-family/UbuntuMono-R.ttf", size=size)
        else:
            font = ImageFont.truetype("ubuntu-font-family/UbuntuMono-B.ttf", size=size)

        width, height = int(font.getlength(text)), size
        image = Image.new('RGB', (width, height), color=bg)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, fill=fg, font=font)

        await self.send_image(interaction, image)

    @app_commands.command(name="asciify", description="asciify image")
    @app_commands.describe(size="character size")
    async def asciify(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        size: Optional[int],
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        if not size:
            size = 8

        src_image = Image.open(io.BytesIO(await image_attachment.read()))
        pixels = src_image.load()

        font_map = {
            "r": ImageFont.truetype("ubuntu-font-family/UbuntuMono-R.ttf", size=size),
            "ri": ImageFont.truetype("ubuntu-font-family/UbuntuMono-RI.ttf", size=size),
            "b": ImageFont.truetype("ubuntu-font-family/UbuntuMono-B.ttf", size=size),
            "bi": ImageFont.truetype("ubuntu-font-family/UbuntuMono-BI.ttf", size=size),
        }

        cwidth, cheight = int(font_map["r"].getlength("w")), size

        dst_width, dst_height = src_image.size
        dst_width = int(dst_width / cwidth)
        dst_height = int(dst_height / cheight)

        dst_image = Image.new('RGB', (dst_width * cwidth, dst_height * cheight), color='black')
        draw = ImageDraw.Draw(dst_image)

        for cx in range(0, dst_width):
            for cy in range(0, dst_height):
                x = cx * cwidth
                y = cy * cheight

                avg_color = [0, 0, 0]
                for i in range(x, x + cwidth):
                    for j in range(y, y + cheight):
                        if i < src_image.size[0] and j < src_image.size[1]:
                            color = pixels[i, j]
                            for n in range(0, 3):
                                avg_color[n] += color[n]

                for n in range(0, 3):
                    avg_color[n] /= cwidth * cheight
                rate = (avg_color[0] + avg_color[1] + avg_color[2]) / 3 / 255 * PALLETE_COUNT

                visual_density = min(int(rate + 0.5), PALLETE_COUNT-1)

                pallete = PALLETE["visual_density"][visual_density]
                draw_set = random.choice(pallete)

                # bg
                draw.rectangle(
                    [(x, y), (x + cwidth, y + cheight)],
                    fill=tuple(int(x * 0.1) for x in avg_color),
                )

                # fg
                draw.text(
                    (x, y),
                    draw_set[0],
                    fill=tuple(int(x) for x in avg_color),
                    font=font_map[draw_set[1]]
                )

        await self.send_image(interaction, dst_image)
