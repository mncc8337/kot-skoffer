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
import asyncio


HEX_REGEX = r'^#([A-Fa-f0-9]{8}|[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
HOST_SERVICE = "0x0.st"


class ImageCog(GroupCog, group_name="image"):
    def __init__(self, bot):
        self.bot = bot

    def post_to_host_service(self, file_path):
        try:
            response = None
            with open(file_path, "rb") as file:
                response = requests.post(
                    "https://" + HOST_SERVICE,
                    files={"file": file},
                    headers={"User-Agent": "kot-skoffer"}
                )

            if response.status_code == 200:
                return response.text.strip()
            else:
                print(f"kot: failed to post image {file_path}. {response.text}")
                return None
        except Exception as e:
            print(f"kot: failed to post image {file_path}. {e}")
            return None

    async def send_high_quality_image(self, interaction: Interaction, image: Image, name: str):
        await asyncio.to_thread(image.save, "images/" + name + ".png", format="PNG")

        buffer, _ = await asyncio.to_thread(image_process.reduce_size, image)
        discord_file = discord.File(fp=buffer, filename=name + ".png")

        image_url = await asyncio.to_thread(self.post_to_host_service, "images/image_process/" + name + ".png")
        if image_url:
            msg = f"""{interaction.user.mention} done processing. sent with full quality via {HOST_SERVICE} and low quality (maybe downscaled) via attachment.
[full image at {HOST_SERVICE}]({image_url}).
**NOTE:** the high quality one will be deleted after 30 days"""
            await interaction.followup.send(msg, file=discord_file)
        else:
            await interaction.followup.send("done processing. unable to send the high quality one, sent with low quality via attachment instead. image maybe downscaled", file=discord_file)

    async def send_image(self, interaction: Interaction, image: Image, name: str):
        buffer, _ = image_process.reduce_size(image)
        discord_file = discord.File(fp=buffer, filename=name + ".png")
        await interaction.followup.send(file=discord_file)

    @app_commands.command(name="paste", description="paste foreground onto background")
    @app_commands.describe(
        position_x="x position of foreground image. default: 0",
        position_y="y position of foreground image. default: 0",
    )
    async def paste(
        self,
        interaction: Interaction,
        background_attachment: discord.Attachment,
        foreground_attachment: discord.Attachment,
        position_x: Optional[int] = 0,
        position_y: Optional[int] = 0,
    ):
        if not background_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="bg is not an image",
                ephemeral=True,
            )
            return

        if not foreground_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="fg is not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        background = Image.open(io.BytesIO(await background_attachment.read()))
        foreground = Image.open(io.BytesIO(await foreground_attachment.read()))
        await asyncio.to_thread(image_process.paste, background, foreground, (position_x, position_y))

        await self.send_high_quality_image(
            interaction,
            background,
            background_attachment.filename
        )

    @app_commands.command(name="crop", description="self explanatory")
    async def crop(
        self,
        interaction: Interaction,
        img_attachment: discord.Attachment,
        x: int,
        y: int,
        w: int,
        h: int,
    ):
        if not img_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="img is not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        img = Image.open(io.BytesIO(await img_attachment.read()))

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.crop, img, (x, y, x + w, y + h)),
            img_attachment.filename + " cropped"
        )

    @app_commands.command(name="composite", description="composite 2 images")
    async def composite(
        self,
        interaction: Interaction,
        img1_attachment: discord.Attachment,
        img2_attachment: discord.Attachment,
        mask_img_attachment: discord.Attachment,
    ):
        if not img1_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="img1 is not an image",
                ephemeral=True,
            )
            return

        if not img2_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="img2 is not an image",
                ephemeral=True,
            )
            return

        if not mask_img_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="mask_img is not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        img1 = Image.open(io.BytesIO(await img1_attachment.read()))
        img2 = Image.open(io.BytesIO(await img2_attachment.read()))
        mask = Image.open(io.BytesIO(await mask_img_attachment.read()))

        if img1.size[0] != img2.size[0] or img1.size[1] != img2.size[1]:
            await interaction.followup.send(
                content=f"img1 and img2 need to be the same size. ({img1.size[0]}x{img1.size[1]} and {img2.size[0]}x{img2.size[1]})",
            )
            return

        if img1.size[0] != mask.size[0] or img1.size[1] != mask.size[1]:
            await interaction.followup.send(
                content=f"img1 and mask need to be the same size. ({img1.size[0]}x{img1.size[1]} and {mask.size[0]}x{mask.size[1]})",
            )
            return

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.composite, img1, img2, mask),
            img1_attachment.filename + " and " + img2_attachment.filename + " composite"
        )

    @app_commands.command(name="blend", description="blend 2 images")
    async def blend(
        self,
        interaction: Interaction,
        img1_attachment: discord.Attachment,
        img2_attachment: discord.Attachment,
        alpha: float,
    ):
        if not img1_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="img1 is not an image",
                ephemeral=True,
            )
            return

        if not img2_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="img2 is not an image",
                ephemeral=True,
            )
            return

        alpha = min(max(alpha, 0.0), 1.0)

        await interaction.response.defer()

        img1 = Image.open(io.BytesIO(await img1_attachment.read()))
        img2 = Image.open(io.BytesIO(await img2_attachment.read()))

        if img1.size[0] != img2.size[0] or img1.size[1] != img2.size[1]:
            await interaction.followup.send(
                content=f"img1 and img2 need to be the same size. ({img1.size[0]}x{img1.size[1]} and {img2.size[0]}x{img2.size[1]})",
                ephemeral=True
            )
            return

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.blend, img1, img2, alpha),
            img1_attachment.filename + " and " + img2_attachment.filename + " blend"
        )

    @app_commands.command(name="invert_transparency", description="self explanatory")
    async def invert_transparency(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        image = Image.open(io.BytesIO(await image_attachment.read()))

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.invert_transparency, image),
            image_attachment.filename
        )

    @app_commands.command(name="rotate", description="rotate an image counter-clockwise")
    async def rotate(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        theta: float,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        image = Image.open(io.BytesIO(await image_attachment.read()))

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.rotate, image, theta),
            image_attachment.filename
        )

    @app_commands.command(name="apply_opacity", description="lower the alpha component of the image by a factor")
    @app_commands.describe(alpha="ranging from 0.0 to 1.0")
    async def apply_opacity(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        alpha: float,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        image = Image.open(io.BytesIO(await image_attachment.read()))

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.opacity, image, alpha),
            image_attachment.filename
        )

    @app_commands.command(name="getchannel", description="get a specific channel from an image")
    @app_commands.choices(channel=[
        app_commands.Choice(name="red", value="R"),
        app_commands.Choice(name="green", value="G"),
        app_commands.Choice(name="blue", value="B"),
    ])
    async def getchannel(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        channel: str,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        image = Image.open(io.BytesIO(await image_attachment.read()))

        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.get_channel, image, channel[0]),
            image_attachment.filename
        )

    @app_commands.command(name="getsize", description="self explanatory")
    async def getsize(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        image = Image.open(io.BytesIO(await image_attachment.read()))
        discord_file = discord.File(
            fp=io.BytesIO(await image_attachment.read()),
            filename=image_attachment.filename
        )

        await interaction.followup.send(f"{image.size[0]}x{image.size[1]}", file=discord_file)

    @app_commands.command(name="resize", description="self explanatory")
    async def resize(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        width: int,
        height: int,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        image = Image.open(io.BytesIO(await image_attachment.read()))
        image = await asyncio.to_thread(image_process.resize, image, (width, height))

        await self.send_high_quality_image(
            interaction,
            image,
            image_attachment.filename
        )

    @app_commands.command(name="linear_gradient", description="generate a linear gradient")
    async def linear_gradient(self, interaction: Interaction):
        await interaction.response.defer()
        await self.send_image(
            interaction,
            Image.linear_gradient("L"),
            "linear_gradient"
        )

    @app_commands.command(name="radial_gradient", description="generate a radial gradient")
    async def radial_gradient(self, interaction: Interaction):
        await interaction.response.defer()
        await self.send_image(
            interaction,
            Image.radial_gradient("L"),
            "radial_gradient"
        )

    @app_commands.command(name="noise", description="generate a gaussian noise")
    async def noise(
        self,
        interaction: Interaction,
        width: int,
        height: int,
        sigma: float,
    ):
        await interaction.response.defer()
        await self.send_high_quality_image(
            interaction,
            await asyncio.to_thread(image_process.noise, (width, height), sigma),
            "linear_gradient"
        )

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
            await asyncio.to_thread(image_process.text, text, size, bg, fg, bold),
            text
        )

    @app_commands.command(name="asciify", description="asciify image")
    @app_commands.describe(
        character_size="size of characters. default: 8",
        bg_influence="how much the color of text will affect the bg. ranging from 0.0 to 1.0. default: 0.3",
        no_color="black and white mode. default: False",
        chars_only="only draw characters. default: False",
        invert_brightness="use dark characters for bright area",
    )
    async def asciify(
        self,
        interaction: Interaction,
        image_attachment: discord.Attachment,
        character_size: Optional[int] = 8,
        bg_influence: Optional[float] = 0.3,
        no_color: Optional[bool] = False,
        chars_only: Optional[bool] = False,
        invert_brightness: Optional[bool] = False,
    ):
        if not image_attachment.content_type.startswith("image/"):
            await interaction.response.send_message(
                content="not an image",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        bg_influence = max(min(bg_influence, 1.0), 0.0)

        if no_color:
            bg_influence = 0

        res_image = await asyncio.to_thread(
            image_process.asciify,
            Image.open(io.BytesIO(await image_attachment.read())),
            character_size,
            bg_influence,
            no_color,
            chars_only,
            invert_brightness,
        )

        await self.send_high_quality_image(
            interaction,
            res_image,
            image_attachment.filename + f".{character_size}-{bg_influence}"
        )
