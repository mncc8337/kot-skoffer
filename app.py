import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
import requests
import json
import random

load_dotenv()
token = os.getenv("TOKEN")
if not token:
    print("TOKEN not set!")
    exit(1)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print("meow meow")
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

    await bot.process_commands(message)

# @bot.command(name="hello")
# async def hello(ctx):
#     await ctx.send(f"hello, {ctx.author.name}!")

@bot.command(name="roll")
async def roll(ctx, lbound: int = 1, hbound: int = 6, times: int = 1):
    rolls = ""
    rolls += str(random.randint(lbound, hbound)) + " "

    message = await ctx.send(rolls)
    for _ in range(times - 1):
        rolls += str(random.randint(lbound, hbound)) + " "
        await message.edit(content=rolls)

@bot.command(name="fibo")
async def fibo(ctx, size: int = 1):
    if size < 1:
        await ctx.send("tf?")
        return

    a = 1
    b = 2
    c = 3

    content = "1"
    message = await ctx.send(content)
    size -= 1

    while size > 0:
        content += " " + str(a)
        t = c
        c += b
        a = b
        b = t
        size -= 1

        await message.edit(content=content)

@bot.command(name="weather")
async def weather(ctx, days: int = 1):
    url = f"https://api.open-meteo.com/v1/forecast?latitude=16.4619&longitude=107.5955&current=temperature_2m,apparent_temperature,is_day,rain,showers,wind_speed_10m,wind_direction_10m&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max,rain_sum,showers_sum,wind_speed_10m_max,wind_gusts_10m_max,shortwave_radiation_sum&timezone=Asia%2FBangkok&forecast_days={days}"
    response = requests.get(url).json()
    await ctx.send(f"```# current\n{json.dumps(response["current"], indent=4)}```")

    for day in range(days):
        message = f"```# day +{day}\n"
        message += "{\n"
        for key in response["daily"].keys():
            message += f"    \"{key}\": {response["daily"][key][day]},\n"
        message += "}```"
        await ctx.send(message)

bot.run(token)
