import discord
from discord import app_commands
from discord.ext import commands
import lib.data_loader as data_loader


class SettingsCog(commands.GroupCog, group_name="settings"):
    def __init__(self, bot):
        self.bot = bot

        self.bot_data: data_loader.Data = data_loader.Data("data/general.json")
        for key in [
            # properties in general.json and their default value
            ("city", "hue"),
            ("weather_api", "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,rain,showers,wind_speed_10m,wind_direction_10m&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,rain_sum,showers_sum,wind_speed_10m_max,wind_direction_10m_dominant,shortwave_radiation_sum&timezone=Asia%2FBangkok&forecast_days={days}"),
        ]:
            if key[0] not in self.bot_data.data.keys():
                self.bot_data.data.setdefault(key[0], key[1])

    @app_commands.command(name="list", description="show all settings. use settingsset and settingsget to write/read")
    async def listcmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(" ".join(self.bot_data.data.keys()))

    @app_commands.command(name="set", description="set settings")
    async def setcmd(self, interaction: discord.Interaction, key: str, value: str,):
        if key not in self.bot_data.data.keys():
            await interaction.response.send_message("no such key: " + key)
            return
        self.bot_data.data[key] = type(self.bot_data.data[key])(value)
        await interaction.response.send_message(f"{key} set to {value}")

        self.bot_data.save()

    @app_commands.command(name="get", description="get settings value")
    async def getcmd(self, interaction: discord.Interaction, key: str,):
        if key not in self.bot_data.data.keys():
            await interaction.response.send_message("no such key: " + key)
            return
        await interaction.response.send_message(f"{self.bot_data.data[key]}")
