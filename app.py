import discord
from discord.ext import commands
from discord.ext.commands import Context, parameter

from dotenv import load_dotenv
import os
import requests
import json
import random

import data_loader
from todo_list import TODOList
from lucky_wheel import LuckyWheel
import random_name

load_dotenv()
token = os.getenv("TOKEN")
if not token:
    print("TOKEN not set!")
    exit(1)


def allowed_channels(*channel_ids):
    def predicate(ctx):
        return ctx.channel.id in channel_ids
    return commands.check(predicate)


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

bot_data: data_loader.Data = data_loader.Data("data/general.json")
for key in [
    # properties in general.json and their default value
    ("bottest_channel", 0),
    ("city", "hue"),
    ("weather_api", "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,rain,showers,wind_speed_10m,wind_direction_10m&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,rain_sum,showers_sum,wind_speed_10m_max,wind_direction_10m_dominant,shortwave_radiation_sum&timezone=Asia%2FBangkok&forecast_days={days}"),
]:
    if key[0] not in bot_data.data.keys():
        bot_data.data.setdefault(key[0], key[1])

todo_list = TODOList("data/todos.json")
wheel = LuckyWheel("data/lucky_wheel.json")

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="a car fight",
        )
    )

    print("kot: meow meow")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("meow meow, u kant use dis command heere!!")


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


@bot.command(
    name="settings",
    brief="access bot settings",
    description="read/write bot settings"
)
async def settings(
    ctx: Context,
    opcode: str = parameter(description="operation, can be set, get or list"),
    *args
):
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


@bot.command(
    name="numberfact",
    brief="see number fact",
    description="see random number fact"
)
async def numberfact(
    ctx: Context,
    number: int = parameter(description="an integer")
):
    url = f"http://numbersapi.com/{number}"
    response = requests.get(url)

    if response.status_code == 200:
        await ctx.send(response.text)


@bot.command(
    name="roll",
    brief="roll random number",
    description="get some random number in specified range"
)
@allowed_channels(bot_data.data["bottest_channel"])
async def roll(
    ctx: Context,
    lbound: int = parameter(description="lower bound", default=1),
    hbound: int = parameter(description="higher bound", default=6),
    times: int = parameter(description="number of rolls", default=1)
):
    rolls = ""
    rolls += str(random.randint(lbound, hbound)) + " "

    message = await ctx.send(rolls)
    for _ in range(times - 1):
        rolls += str(random.randint(lbound, hbound)) + " "
        await message.edit(content=rolls)


@bot.command(
    name="weather",
    brief="weather data",
    description="get weather data from anywhere"
)
async def weather(
    ctx: Context,
    city_name: str = parameter(
        description="city name, use \"_\" for default. can be omit if not specifying days",
        default="_"
    ),
    days: int = parameter(description="number of days to be forcast", default=0)
):
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


@bot.command(name="todo", brief="todo list", description="todo list")
async def todo(
    ctx: Context,
    opcode: str = parameter(
        description="operation. can be add, remove and toggle. omit to show todo list",
        default=""
    ),
    *, param: str = ""
):
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


@bot.command(
    name="randomname",
    brief="get random name",
    description="get random name"
)
@allowed_channels(bot_data.data["bottest_channel"])
async def randomname(
    ctx: Context,
    type: str = parameter(
        description="name type. can be cat and human",
        default="cat"
    )
):
    match type:
        case "human":
            await ctx.send(await random_name.generate_human_name())
        case "cat":
            await ctx.send(await random_name.generate_cat_name())
        case _:
            await ctx.send("no such type " + type)


@bot.command(name="randomimage", brief="get random image", description="get random image")
async def randomimage(ctx: Context):
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
        await ctx.send("no image to choose")
        return

    file = discord.File(os.path.join(pwd, item))
    await ctx.send(file=file)


@bot.command(
    name="spin",
    brief="lucky wheel",
    description="customizable lucky wheel"
)
async def spin(
    ctx: Context,
    opcode: str = parameter(
        description="operation. can be add, remove, list and user. omit to spin",
        default=""
    ),
    *args
):
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

bot.run(token)
