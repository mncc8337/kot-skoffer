import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from typing import Optional

import os
import random
import requests
import lib.random_name as random_name

LANGS = [
    "random",
    "aa", "ab", "ae", "af", "ak", "am", "an", "ar", "as", "av", "ay", "az",
    "ba", "be", "bg", "bh", "bi", "bm", "bn", "bo", "br", "bs", "ca", "ce",
    "ch", "co", "cr", "cs", "cu", "cv", "cy", "da", "de", "dv", "dz", "ee",
    "el", "en", "eo", "es", "et", "eu", "fa", "ff", "fi", "fj", "fo", "fr",
    "fy", "ga", "gd", "gl", "gn", "gu", "gv", "ha", "he", "hi", "ho", "hr",
    "ht", "hu", "hy", "hz", "ia", "id", "ie", "ig", "ii", "ik", "io", "is",
    "it", "iu", "ja", "jv", "ka", "kg", "ki", "kj", "kk", "kl", "km", "kn",
    "ko", "kr", "ks", "ku", "kv", "kw", "ky", "la", "lb", "lg", "li", "ln",
    "lo", "lt", "lu", "lv", "mg", "mh", "mi", "mk", "ml", "mn", "mr", "ms",
    "mt", "my", "na", "nb", "nd", "ne", "ng", "nl", "nn", "no", "nr", "nv",
    "ny", "oc", "oj", "om", "or", "os", "pa", "pi", "pl", "ps", "pt", "qu",
    "rm", "rn", "ro", "ru", "rw", "sa", "sc", "sd", "se", "sg", "si", "sk",
    "sl", "sm", "sn", "so", "sq", "sr", "ss", "st", "su", "sv", "sw", "ta",
    "te", "tg", "th", "ti", "tk", "tl", "tn", "to", "tr", "ts", "tt", "tw",
    "ty", "ug", "uk", "ur", "uz", "ve", "vi", "vo", "wa", "wo", "xh", "yi",
    "yo", "za", "zh", "zu",
]


class RandomCog(GroupCog, group_name="random"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="roll",
        description="get some random number in specified range"
    )
    @app_commands.describe(lbound="lower bound. default: 1", hbound="higher bound. default: 6", times="how many rolls. default: 1",)
    async def roll(
        self,
        interaction: Interaction,
        lbound: Optional[int] = 1,
        hbound: Optional[int] = 6,
        times: Optional[int] = 1,
    ):
        rolls = ""
        rolls += str(random.randint(lbound, hbound)) + " "

        await interaction.response.send_message(rolls)
        for _ in range(times - 1):
            rolls += str(random.randint(lbound, hbound)) + " "
            await interaction.edit_original_response(content=rolls)

    @app_commands.command(name="catname", description="get random cat name")
    async def catname(self, interaction: Interaction):
        await interaction.response.send_message(await random_name.generate_cat_name())

    @app_commands.command(name="name", description="get random human name")
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

    async def autocomplete_lang(self, interaction: Interaction, current: str):
        return [
            app_commands.Choice(name=code, value=code)
            for code in LANGS if code.startswith(current.lower())
        ][:25]

    @app_commands.command(name="wiki", description="get random wikipedia page")
    @app_commands.describe(lang="2 characters word indicating language (en, es, fr, ...). default: en")
    @app_commands.autocomplete(lang=autocomplete_lang)
    async def wiki(
        self,
        interaction: Interaction,
        lang: Optional[str] = "en",
    ):
        from datetime import datetime, timezone
        from html2text import html2text
        import asyncio

        if lang == "random":
            lang = random.choice(LANGS)
        elif lang not in LANGS:
            await interaction.response.send_message(
                content="lang " + lang + " does not exist",
                ephemeral=True,
            )
            return

        try:
            page = await asyncio.to_thread(requests.get, f"https://{lang}.wikipedia.org/api/rest_v1/page/random/summary")
            page = page.json()
        except Exception as e:
            await interaction.response.send_message(
                content="failed to get random page. " + str(e),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=page["title"],
            url=page["content_urls"]["desktop"]["page"],
            timestamp=datetime.strptime(
                page["timestamp"],
                "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        )
        if page.get("description"):
            embed.description = page["description"]
        # if page.get("thumbnail"):
        #     embed.set_thumbnail(url=page["thumbnail"]["source"])
        if page.get("originalimage"):
            embed.set_image(url=page["originalimage"]["source"])

        embed.add_field(name="brief", value=html2text(page["extract_html"]))
        if page.get("coordinates"):
            embed.add_field(name="coordinates", value=f"{page["coordinates"]["lat"]}, {page["coordinates"]["lon"]}")

        await interaction.response.send_message(embed=embed)
