import discord
from discord import Interaction
from discord import app_commands

from lib.message2interaction import MessageInteractionAdapter
from typing import Optional

from dotenv import load_dotenv
import os
import requests

import cog

load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
if not discord_token:
    print("TOKEN not set!")
    exit(1)

ai_enabled = os.getenv("ENABLE_AI")

if ai_enabled:
    if not os.getenv("LLM_MODEL"):
        print("LLM_MODEL not set!")
        exit(1)
    if not os.getenv("LLM_HISTORY_WINDOW"):
        print("LLM_HISTORY_WINDOW not set!")
        exit(1)
    if not os.getenv("LLM_INSTRUCTION"):
        print("LLM_INSTRUCTION not set!")
        exit(1)
    if not os.getenv("LLM_LOCAL_ONLY") and not os.getenv("OLLAMA_API_KEY"):
        print("OLLAMA_API_KEY not set!")
        exit(1)


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True

bot = discord.ext.commands.Bot(command_prefix=".", intents=intents)
bot.remove_command("help")


@bot.event
async def on_ready():
    print("kot: meow meow")

    await bot.add_cog(cog.RandomCog(bot))
    await bot.add_cog(cog.TodoCog(bot))
    await bot.add_cog(cog.SpinCog(bot))
    await bot.add_cog(cog.ImageCog(bot))
    await bot.add_cog(cog.WeatherCog(bot))

    if ai_enabled:
        await bot.add_cog(cog.AiCog(bot))

    await bot.tree.sync()
    print("kot: app commands synced")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="a car fight",
        )
    )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "kot" in message.content.lower():
        emoji = discord.utils.get(message.guild.emojis, name="car")
        await message.channel.send(str(emoji))

    if bot.user in message.mentions:
        if ai_enabled:
            ai_cog = bot.get_cog("AiCog")
            clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
            if not clean_content:
                clean_content = "meow"

            fake_interaction = MessageInteractionAdapter(message)

            await ai_cog.send_chatbot_message(
                interaction=fake_interaction,
                msg=clean_content,
                role="user",
                think="off",
                no_reply=False,
                continuation=False
            )
            return
        else:
            emoji = discord.utils.get(message.guild.emojis, name="car")
            await message.channel.send(f"{emoji} ?")


@bot.tree.command(name="numberfact", description="see random number fact")
@app_commands.describe(
    number="an integer"
)
async def numberfact(interaction: Interaction, number: int):
    url = f"http://numbersapi.com/{number}"
    response = requests.get(url)

    if response.status_code == 200:
        await interaction.response.send_message(response.text)


@bot.tree.command(name="text", description="get an image with texts")
@app_commands.describe(
    text="the content of the image",
    size="font size. default: 32",
    bg="background color, hex value e.g #aabbccdd or #aabbcc or #abc. default: #ffffff",
    fg="foreground color, hex value e.g #aabbccdd or #aabbcc or #abc. default: #000000",
    bold="use bold font. default: False",
    italic="use italic font. default: False",
)
async def text(
    interaction: Interaction,
    text: str,
    size: Optional[int] = 32,
    bg: Optional[str] = "#ffffff",
    fg: Optional[str] = "#000000",
    bold: Optional[bool] = False,
    italic: Optional[bool] = False
):
    image_cog = bot.get_cog("ImageCog")
    await image_cog.text.callback(
        image_cog,
        interaction,
        text,
        size,
        bg,
        fg,
        bold,
        italic
    )


bot.run(discord_token)
