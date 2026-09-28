from discord import Interaction, Embed, Webhook
from discord import app_commands
from discord.ext.commands import GroupCog
from lib.wiktionary import Wiktionary
import os
from urllib.parse import quote


async def _send_followup_result(
    followup: Webhook,
    wik: Wiktionary,
    page_id: int,
):
    if page_id < 0:
        await followup.send(content="word not found on the chosen dict")
        return

    defs, word = wik.definitions_by_id(page_id)

    if word is None:
        await followup.send(content="word not found on the chosen dict")
        return

    parts = []

    for lang, definitions in defs.items():
        formatted = Wiktionary.definitions_to_string(definitions)

        parts.append(f"**{lang}**\n{formatted}")

    description = "\n\n".join(parts)

    page_url = f"https://{wik.base_url}/wiki/{quote(word.replace(' ', '_'), safe='')}"

    embed = Embed(
        title=word,
        url=page_url,
        description=description[:4096],
    )

    await followup.send(
        embed=embed,
    )


class WiktionaryCog(GroupCog, group_name="wiktionary"):
    def __init__(self, bot):
        self.bot = bot
        self.user_agent = os.getenv("USER_AGENT")
        self.vi_wiki = Wiktionary("vi.wiktionary.org", self.user_agent)
        self.en_wiki = Wiktionary("en.wiktionary.org", self.user_agent)

    @app_commands.command(name="exact", description="search exact word")
    @app_commands.choices(
        dictionary=[
            app_commands.Choice(name="vietnamese", value=0),
            app_commands.Choice(name="english", value=1),
        ],
    )
    @app_commands.describe(
        word="word to search",
        dictionary="dictionary to use. default: english",
    )
    async def exact(
        self,
        interaction: Interaction,
        word: str,
        dictionary: int = 1,
    ):
        await interaction.response.defer()
        wik = (self.vi_wiki, self.en_wiki)[dictionary]
        page_id = wik.exact_match(word)
        await _send_followup_result(interaction.followup, wik, page_id)

    @app_commands.command(name="prefix", description="search by prefix")
    @app_commands.choices(
        dictionary=[
            app_commands.Choice(name="vietnamese", value=0),
            app_commands.Choice(name="english", value=1),
        ],
    )
    @app_commands.describe(
        prefix="prefix to search",
        category="category to match",
        dictionary="dictionary to use. default: english",
    )
    async def prefix(
        self,
        interaction: Interaction,
        prefix: str,
        category: str = "",
        dictionary: int = 1,
    ):
        await interaction.response.defer()
        wik = (self.vi_wiki, self.en_wiki)[dictionary]
        word_dict = wik.prefix_match(prefix, category)

        if len(word_dict) == 0:
            await interaction.followup.send(content="word not found on the chosen dict")
            return

        response = ""
        for word in word_dict:
            word_url = (
                f"https://{wik.base_url}/wiki/{quote(word.replace(' ', '_'), safe='')}"
            )
            response += f"[{word}]({word_url}): {word_dict[word]}\n"
        await interaction.followup.send(content=response, suppress_embeds=True)

    @app_commands.command(name="fetch", description="fetch definition by id")
    @app_commands.choices(
        dictionary=[
            app_commands.Choice(name="vietnamese", value=0),
            app_commands.Choice(name="english", value=1),
        ],
    )
    @app_commands.describe(
        id="id to search",
        dictionary="dictionary to use. default: english",
    )
    async def fetch(
        self,
        interaction: Interaction,
        id: int,
        dictionary: int = 1,
    ):
        wik = (self.vi_wiki, self.en_wiki)[dictionary]
        await interaction.response.defer()
        await _send_followup_result(interaction.followup, wik, id)
