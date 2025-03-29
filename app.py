import discord
from discord import Interaction
from discord import app_commands

from dotenv import load_dotenv
import os
import requests

import cog

load_dotenv()
token = os.getenv("TOKEN")
if not token:
    print("TOKEN not set!")
    exit(1)
elif not os.getenv("LLM_MODEL"):
    print("LLM_MODEL not set!")
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

    if os.getenv("ENABLE_AI"):
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
        emoji = discord.utils.get(message.guild.emojis, name="car")
        await message.channel.send(f"{emoji} ?")

    await bot.process_commands(message)


@bot.tree.command(name="numberfact", description="see random number fact")
@app_commands.describe(
    number="an integer"
)
async def numberfact(interaction: Interaction, number: int):
    url = f"http://numbersapi.com/{number}"
    response = requests.get(url)

    if response.status_code == 200:
        await interaction.response.send_message(response.text)


bot.run(token)
