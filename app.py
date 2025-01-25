import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
import requests
import json
import random
import asyncio

from todo_list import TODOList
import cat_farm

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

todo_list = TODOList()
catfarm = cat_farm.CatFarm()

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

    if "kot" in message.content.lower():
        emoji = discord.utils.get(message.guild.emojis, name="car")
        await message.channel.send(str(emoji))

    if bot.user in message.mentions:
        emoji = discord.utils.get(message.guild.emojis, name="car")
        await message.channel.send(f"? {emoji}")

    await bot.process_commands(message)

# @bot.command(name="hello")
# async def hello(ctx):
#     await ctx.send(f"hello, {ctx.author.name}!")

@bot.command(name="roll")
async def roll(ctx, lbound: int = 1, hbound: int = 6, times: int = 1):
    if times > 100:
        await ctx.send("too many requests!")
        return

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
    if size > 25:
        await ctx.send("too many requests!")
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
async def weather(ctx, lat: float = 16.4619, lon: float = 107.5955, days: int = 1):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,is_day,rain,showers,wind_speed_10m,wind_direction_10m&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max,rain_sum,showers_sum,wind_speed_10m_max,wind_gusts_10m_max,shortwave_radiation_sum&timezone=Asia%2FBangkok&forecast_days={days}"
    response = requests.get(url).json()
    await ctx.send(f"```# current\n{json.dumps(response["current"], indent=4)}```")

    for day in range(days):
        message = f"```# day +{day}\n"
        message += "{\n"
        for key in response["daily"].keys():
            message += f"    \"{key}\": {response["daily"][key][day]},\n"
        message += "}```"
        await ctx.send(message)

@bot.command(name="todo")
async def todo(ctx, opcode: str = " ", *, param: str = ""):
    match opcode:
        case "add":
            todo_list.add(str(param))
        case "remove":
            todo_list.remove(int(param))
        case "toggle":
            todo_list.toggle(int(param))
        case _:
            await ctx.send(todo_list.text())

@bot.command(name="random_human_name")
async def random_human_name(ctx):
    await ctx.send(await cat_farm.generate_human_name())

@bot.command(name="random_cat_name")
async def random_cat_name(ctx):
    await ctx.send(await cat_farm.generate_cat_name())

@bot.command(name="farm")
async def farm(ctx, opcode: str = " ", *, args = ""):
    if args != "":
        args = args.split(" ")
    else:
        args = []

    match opcode:
        case "lure":
            cnt = 1
            if len(args) >= 1:
                cnt = int(args[0])
            if cnt > 25:
                await ctx.send("too many requests!")
                return
            tasks = []
            for _ in range(cnt):
                tasks.append(asyncio.create_task(catfarm.lure(ctx)))
            for task in tasks:
                await task
        case "fight":
            await catfarm.fight(ctx)
        case "stop":
            catfarm.stop_fight()
        case "feed":
            cnt = 1
            if len(args) >= 1:
                cnt = int(args[0])
            if cnt > 25:
                await ctx.send("too many requests!")
                return
            tasks = []
            for _ in range(cnt):
                tasks.append(asyncio.create_task(catfarm.feed(ctx)))
            for task in tasks:
                await task
        case "stat":
            await ctx.send(catfarm.cats[args[0]])
        case _:
            await ctx.send(" ".join(list(catfarm.cats.keys())))

bot.run(token)
