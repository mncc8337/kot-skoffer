import discord
from discord.ext import commands, tasks
import discord

from dotenv import load_dotenv
import os
import requests
import json
import random

from todo_list import TODOList
import cat_farm
import data_loader

load_dotenv()
token = os.getenv("TOKEN")
if not token:
    print("TOKEN not set!")
    exit(1)

# decorator
def allowed_in_channels(*allowed_channels):
    def decorator(func):
        async def wrapper(ctx, *args, **kwargs):
            if ctx.channel.id not in allowed_channels:
                await ctx.send("meow meow, u kant use dis command heere!!")
                return
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

bot_data: data_loader.Data = data_loader.Data("data/general.json")
for key in [
    ("catfarm_channel", int),
    ("bottest_channel", int),
    ("city", str),
]:
    if key[0] not in bot_data.data.keys():
        bot_data.data.setdefault(key[0], key[1]())

todo_list = TODOList()
catfarm = cat_farm.CatFarm("data/catfarm.json")

global_heat = 32
@tasks.loop(seconds=150)
async def catfarm_update_health():
    global_heat = random.randrange(19, 38)
    channel = bot.get_channel(int(bot_data.data["catfarm_channel"]))
    if isinstance(channel, discord.TextChannel):
        await channel.send("global heat updated! temperature is now " + str(global_heat))
        await catfarm.update_health(channel, global_heat)
    else:
        await catfarm.update_health(None, global_heat)
    catfarm.save()

@tasks.loop(seconds=30)
async def catfarm_regenerate_health():
    channel = bot.get_channel(int(bot_data.data["catfarm_channel"]))
    if isinstance(channel, discord.TextChannel):
        await catfarm.regenerate_health(bot, channel)
    else:
        await catfarm.regenerate_health(bot, None)
    catfarm.save()

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="a car fight",
        )
    )
    catfarm_update_health.start()
    catfarm_regenerate_health.start()

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
async def settings(ctx, opcode, args):
    args = args.split(" ")

    match opcode:
        case "set":
            if len(args) < 2:
                await ctx.send("not enough arg")
                return
            if args[0] not in bot_data.data.keys():
                await ctx.send("no such key: " + args[0])
                return
            bot_data.data[args[0]] = args[1]
            await ctx.send(f"settings {args[0]} set to {args[1]}")

    bot_data.save()

@bot.command(name="roll")
@allowed_in_channels(int(bot_data.data["bottest_channel"]))
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
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,is_day,rain,showers,wind_speed_10m,wind_direction_10m&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max,rain_sum,showers_sum,wind_speed_10m_max,wind_gusts_10m_max,shortwave_radiation_sum&timezone=Asia%2FBangkok&forecast_days={days}"
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
async def todo(ctx, opcode: str = " ", param: str = ""):
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
@allowed_in_channels(int(bot_data.data["bottest_channel"]))
async def random_human_name(ctx):
    await ctx.send(await cat_farm.generate_human_name())

@bot.command(name="random_cat_name")
@allowed_in_channels(int(bot_data.data["bottest_channel"]))
async def random_cat_name(ctx):
    await ctx.send(await cat_farm.generate_cat_name())

@bot.command(name="farm")
@allowed_in_channels(int(bot_data.data["catfarm_channel"]))
async def farm(ctx, opcode, args = ""):
    if args != "":
        args = args.split(" ")
    else:
        args = []

    match opcode:
        case "lure":
            await catfarm.lure(ctx)
        case "feed":
            name = ""
            if len(args) > 1:
                name = args[0]
            await catfarm.feed(ctx, str(ctx.author.id), name)
        case "stat":
            if len(args):
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
