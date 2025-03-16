import discord
from discord.ext import commands
from discord import Interaction

from dotenv import load_dotenv
import os
import requests
import json

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

bot = commands.Bot(command_prefix=".", intents=intents)
bot.remove_command("help")

settings_cog = cog.SettingsCog(bot)
random_cog = cog.RandomCog(bot)
todo_cog = cog.TodoCog(bot)
spin_cog = cog.SpinCog(bot)
ai_cog = cog.AiCog(bot)


@bot.event
async def on_ready():
    print("kot: meow meow")

    await bot.add_cog(settings_cog)
    await bot.add_cog(random_cog)
    await bot.add_cog(todo_cog)
    await bot.add_cog(spin_cog)
    await bot.add_cog(ai_cog)

    await bot.tree.sync()

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

    if "ping" in message.content.lower():
        await message.channel.send("pong")

    if "kot" in message.content.lower():
        emoji = discord.utils.get(message.guild.emojis, name="car")
        await message.channel.send(str(emoji))

    if bot.user in message.mentions:
        emoji = discord.utils.get(message.guild.emojis, name="car")
        await message.channel.send(f"{emoji} ?")

    await bot.process_commands(message)


@bot.tree.command(name="numberfact", description="see random number fact")
async def numberfact(interaction: Interaction, number: int):
    url = f"http://numbersapi.com/{number}"
    response = requests.get(url)

    if response.status_code == 200:
        await interaction.response.send_message(response.text)


@bot.tree.command(name="weather", description="get weather data from anywhere")
async def weather(interaction: Interaction, city_name: str, days: int,):
    lat: float = 0
    lon: float = 0
    message: str = ""

    if city_name == "_":
        city_name = settings_cog.bot_data.data["city"]

    # get coordinate using city name
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    response = requests.get(url, headers={"User-Agent": "kot-skoffer"})
    if response.status_code == 200:
        data = response.json()
        if data:
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            city_name = data[0]["display_name"]
        else:
            await interaction.response.send_message(f"no such city {city_name}")
            return
    else:
        await interaction.response.send_message("cannot request city coordinate")
        return

    # get weather info
    url = settings_cog.bot_data.data["weather_api"].format(lat=lat, lon=lon, days=days)
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        message += f"weather stat of {city_name}:\n"
        message += f"```# current\n{json.dumps(data["current"], indent=4)}```"
        await interaction.response.send_message(message)

        if days > 0:
            for day in range(days):
                message = ""
                message += f"```# day +{day}\n"
                message += "{\n"
                for key in data["daily"].keys():
                    message += f"    \"{key}\": {data["daily"][key][day]},\n"
                message += "}```"
                await interaction.response.send_message(message)


bot.run(token)
