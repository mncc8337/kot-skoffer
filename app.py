import discord
from discord.ext import commands, tasks
import discord

from dotenv import load_dotenv
import os
import requests
import json
import random

import data_loader
from todo_list import TODOList
import cat_farm
from lucky_wheel import LuckyWheel

load_dotenv()
token = os.getenv("TOKEN")
if not token:
    print("TOKEN not set!")
    exit(1)

async def allowed_in_channels(ctx, *allowed_channels):
    if ctx.channel.id not in allowed_channels:
        await ctx.send("meow meow, u kant use dis command heere!!")
        return False
    return True

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

bot_data: data_loader.Data = data_loader.Data("data/general.json")
for key in [
    # properties in general.json and their default value
    ("catfarm_channel", 0),
    ("bottest_channel", 0),
    ("city", "hue"),
    ("weather_api", "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,rain,showers,wind_speed_10m,wind_direction_10m&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,rain_sum,showers_sum,wind_speed_10m_max,wind_direction_10m_dominant,shortwave_radiation_sum&timezone=Asia%2FBangkok&forecast_days={days}"),
]:
    if key[0] not in bot_data.data.keys():
        bot_data.data.setdefault(key[0], key[1])

todo_list = TODOList("data/todos.json")
catfarm = cat_farm.CatFarm("data/catfarm.json")
wheel = LuckyWheel("data/lucky_wheel.json")

global_heat = 28
@tasks.loop(seconds=1500)
async def catfarm_update_temperature():
    global_heat = random.randrange(19, 38)
    channel = bot.get_channel(int(bot_data.data["catfarm_channel"]))
    if isinstance(channel, discord.TextChannel):
        await channel.send("global heat updated! temperature is now " + str(global_heat))
    catfarm.save()

@tasks.loop(seconds=30)
async def catfarm_update_health():
    channel = bot.get_channel(int(bot_data.data["catfarm_channel"]))
    if isinstance(channel, discord.TextChannel):
        await catfarm.update_health(bot, channel, global_heat)
    else:
        await catfarm.update_health(bot, None, global_heat)
    catfarm.save()

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="a car fight",
        )
    )
    catfarm_update_temperature.start()
    catfarm_update_health.start()

    print("kot: meow meow")

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

@bot.command(name="settings")
async def settings(ctx, opcode: str, *, args = ""):
    if args != "":
        args = args.split(" ")
    else:
        args = []

    match opcode:
        case "set":
            if len(args) < 2:
                await ctx.send("not enough arg")
                return
            if args[0] not in bot_data.data.keys():
                await ctx.send("no such key: " + args[0])
                return
            bot_data.data[args[0]] = type(bot_data.data[args[0]])(args[1])
            await ctx.send(f"{args[0]} set to {args[1]}")
        case "get":
            if len(args) < 1:
                await ctx.send("not enough arg")
                return
            if args[0] not in bot_data.data.keys():
                await ctx.send("no such key: " + args[0])
                return
            await ctx.send(f"{bot_data.data[args[0]]}")
        case "list":
            await ctx.send(" ".join(bot_data.data.keys()))

    bot_data.save()

@bot.command(name="numberfact")
async def numberfact(ctx, number: int):
    url = f"http://numbersapi.com/{number}"
    response = requests.get(url)

    if response.status_code == 200:
        await ctx.send(response.text)

@bot.command(name="roll")
async def roll(ctx, lbound: int = 1, hbound: int = 6, times: int = 1):
    if not await allowed_in_channels(ctx, bot_data.data["bottest_channel"]): return

    rolls = ""
    rolls += str(random.randint(lbound, hbound)) + " "

    message = await ctx.send(rolls)
    for _ in range(times - 1):
        rolls += str(random.randint(lbound, hbound)) + " "
        await message.edit(content=rolls)

@bot.command(name="weather")
async def weather(ctx, city_name: str = "_", days: int = 0):
    lat: float = 0
    lon: float = 0
    message: str = ""

    if city_name == "_":
        city_name = bot_data.data["city"]

    # get coordinate using city name
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    response = requests.get(url, headers={ "User-Agent": "kot-skoffer" })
    if response.status_code == 200:
        data = response.json()
        if data:
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            city_name = data[0]["display_name"]
        else:
            await ctx.send(f"no such city {city_name}")
            return
    else:
        await ctx.send("cannot request city coordinate")
        return

    # get weather info
    url = bot_data.data["weather_api"].format(lat=lat, lon=lon, days=days)
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        message += f"weather stat of {city_name}:\n"
        message += f"```# current\n{json.dumps(data["current"], indent=4)}```"
        await ctx.send(message)

        if days > 0:
            for day in range(days):
                message = ""
                message += f"```# day +{day}\n"
                message += "{\n"
                for key in data["daily"].keys():
                    message += f"    \"{key}\": {data["daily"][key][day]},\n"
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

    todo_list.save()

@bot.command(name="randomname")
async def randomname(ctx, type: str = "cat"):
    if not await allowed_in_channels(ctx, bot_data.data["bottest_channel"]): return

    match type:
        case "human":
            await ctx.send(await cat_farm.generate_human_name())
        case "cat":
            await ctx.send(await cat_farm.generate_cat_name())
        case _:
            await ctx.send("no such type " + type)

@bot.command(name="randomimage")
async def randomimage(ctx):
    pwd = "./images"
    item: str = ""

    def listdir(path):
        l = os.listdir(path)
        nl = []
        for item in l:
            _, ext = os.path.splitext(item)
            if (
                ext in ( ".png", ".jpg", ".jpeg", ".webp", ".gif" )
                or os.path.isdir(os.path.join(path, item))
            ):
                nl.append(item)

        return nl

    while (item == "" or len(listdir(pwd))) and os.path.isdir(os.path.join(pwd, item)):
        pwd = os.path.join(pwd, item)
        item = random.choice(listdir(pwd))

    if item == "":
        await ctx.send("no image to choose")
        return

    file = discord.File(os.path.join(pwd, item))
    await ctx.send(file=file)

@bot.command(name="spin")
async def spin(ctx, opcode: str = "", *, args = ""):
    if args != "":
        args = args.split(" ")
    else:
        args = []

    match opcode:
        case "":
            await wheel.spin(ctx)
        case "add":
            if len(args) < 2:
                await ctx.send("not enough arg")
                return
            wheel.add(args[0], int(args[1]))
            await ctx.send(f"item {args[0]} added")
        case "remove":
            if len(args) < 1:
                await ctx.send("not enough arg")
                return
            if args[0] not in wheel.data["item"].keys():
                await ctx.send("no such item " + args[0])
            wheel.remove(args[0])
            await ctx.send(f"item {args[0]} removed")
        case "list":
            await wheel.list(ctx)
        case "user":
            await wheel.user(ctx)

    wheel.save()


@bot.command(name="farm")
async def farm(ctx, opcode: str = "", *, args = ""):
    if not await allowed_in_channels(ctx, bot_data.data["catfarm_channel"]): return

    if args != "":
        args = args.split(" ")
    else:
        args = []

    match opcode:
        case "lure":
            await catfarm.lure(ctx)
        case "feed":
            if len(args) > 0 and args[0] not in catfarm.data[str(ctx.author.id)].keys():
                await ctx.send(f"no such cat {args[0]}")
                return
            name = ""
            if len(args) > 0:
                name = args[0]
            await catfarm.feed(ctx, str(ctx.author.id), name)
        case "stat":
            if len(args):
                if args[0] not in catfarm.data[str(ctx.author.id)].keys():
                    await ctx.send(f"no such cat {args[0]}")
                    return
                await catfarm.stat(ctx, str(ctx.author.id), args[0])
            else:
                await catfarm.check(ctx, str(ctx.author.id))
        case _:
            content = "cat farm stat:\n"
            for user_id in catfarm.data.keys():
                user = await bot.fetch_user(int(user_id))
                if not user:
                    continue
                content += f"- {user.name}:"
                for name in catfarm.data[user_id].keys():
                    content += " " + name
                content += "\n"
            await ctx.send(content)

    catfarm.save()

bot.run(token)
