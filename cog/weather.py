import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog

import json
import random
from io import BytesIO
import lib.openmeteo as weatherapi
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker


Y_AXIS_MAX_TICKS = 25
X_AXIS_MAX_TICKS = 75


def random_vibrant_color():
    return mcolors.to_hex((
        random.randint(50, 200) / 255,
        random.randint(50, 200) / 255,
        random.randint(50, 200) / 255
    ))


async def process_location(location, lat, lon):
    location_name = ""
    if location != "":
        data = weatherapi.search_location(location, 1, "kot-skoffer")
        if not data or len(data) < 1:
            return (None, None, None)
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        location_name = data[0]["display_name"]
    else:
        data = weatherapi.reverse_location(lat, lon, "kot-skoffer")
        if not data:
            return (None, None, None)
        lat = data["lat"]
        lon = data["lon"]
        location_name = data["display_name"]

    return (location_name, lat, lon)


class WeatherCog(GroupCog, group_name="weather"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="search",
        description="search an location using name"
    )
    async def search(self, interaction: Interaction, name: str):
        data = weatherapi.search_location(name, limit=10, user_agent="kot-skoffer")
        if not data or len(data) < 1:
            await interaction.response.send_message("no location found", ephemeral=True)
            return

        content = f"found {len(data)} match(es)\n"
        for loc in data:
            content += f"{loc["display_name"]}\n"
            content += f"\tlat {loc["lat"]}, lon {loc["lon"]}\n"
            content += f"\t[see location](https://www.openstreetmap.org/?mlat={loc["lat"]}&mlon={loc["lon"]}&zoom=14)\n"

        await interaction.response.send_message(content)

    @app_commands.command(name="parameters", description="see all parameters of models")
    @app_commands.choices(
        model=[
            app_commands.Choice(name="current", value="current"),
            app_commands.Choice(name="minutely", value="minutely_15"),
            app_commands.Choice(name="hourly", value="hourly"),
            app_commands.Choice(name="daily", value="daily"),
        ],
    )
    async def parameters(
        self,
        interaction: Interaction,
        model: str,
    ):
        await interaction.response.send_message(
            "parameters of " + model + " model\n" +
            "```\n" + "\n".join(weatherapi.WEATHER_AVAILABLE_PARAMETERS[model]) + "\n```",
            ephemeral=True
        )

    @app_commands.command(name="explain", description="get description of an parameter")
    async def explain(
        self,
        interaction: Interaction,
        parameter: str,
    ):
        if parameter not in weatherapi.WEATHER_PARAMETER_DESCRIPTION.keys():
            await interaction.response.send_message("parameters " + parameter + "not exists", ephemeral=True)
            return
        await interaction.response.send_message(
            f"{parameter}: {weatherapi.WEATHER_PARAMETER_DESCRIPTION[parameter]}",
            ephemeral=True
        )

    @app_commands.command(name="current", description="get current weather data")
    @app_commands.describe(
        parameters="list of parameters to plot in format \"param1, param2, param3\"",
        location="location name to get weather",
        lat="latitude if \"location\" is not provided",
        lon="longtitude if \"location\" if not provided",
    )
    async def current(
        self,
        interaction: Interaction,
        parameters: str,
        location: str = "",
        lat: float = 0.0,
        lon: float = 0.0,
    ):
        location_name, lat, lon = await process_location(location, lat, lon)
        if not location_name:
            await interaction.response.send_message("location not found", ephemeral=True)
            return

        api = weatherapi.OpenMeteoWeather("kot-skoffer", lat, lon)
        param = [p.strip().lower() for p in parameters.split(",")]
        try:
            api.add_variables("current", *param)
        except Exception as e:
            await interaction.response.send_message(f"```\nerror when adding variables\n{e}\n```")
            return

        data = api.request()
        if not data:
            await interaction.response.send_message("cannot get data from open-meteo")
            return

        message = f"weather stat of {location_name}:\n"
        message += f"```\n{json.dumps(data["current"], indent=4)}\n```\n[request url]({api.get_url()})"
        await interaction.response.send_message(message)

    @app_commands.command(
        name="plot",
        description="plot multiple parameters overtime",
    )
    @app_commands.describe(
        model="model",
        parameters="parameters to plot. list is accepted in format \"param1,param2,param3\"",
        location="location name to get weather",
        lat="latitude if \"location\" is not provided",
        lon="longtitude if \"location\" is not provided",
        forecast_minutes="length to forecast (model \"minutely\"). maximum: 23040, default: 60",
        forecast_hours="length to forecast (model \"hourly\"). maximum: 384, default: 6",
        forecast_days="length to forecast (model \"daily\"). maximum: 16, default: 5",
        past_days="past time to forecast (model \"daily\"). maximum; 92, default: 0",
        past_hours="past time to forecast (model \"hourly\"). maximum: 228, default: 0",
        past_minutes="past time to forecast (model \"minutely\"). maximum: 132480, default: 0",
    )
    @app_commands.choices(
        model=[
            app_commands.Choice(name="minutely", value="minutely_15"),
            app_commands.Choice(name="hourly", value="hourly"),
            app_commands.Choice(name="daily", value="daily"),
        ],
    )
    async def plot(
        self,
        interaction: Interaction,
        model: str,
        parameters: str,
        location: str = "",
        lat: float = 0.0,
        lon: float = 0.0,
        forecast_minutes: int = 60,
        forecast_hours: int = 6,
        forecast_days: int = 5,
        past_days: int = 0,
        past_hours: int = 0,
        past_minutes: int = 0,
    ):
        location_name, lat, lon = await process_location(location, lat, lon)
        if not location_name:
            await interaction.response.send_message("location not found", ephemeral=True)
            return

        api = weatherapi.OpenMeteoWeather("kot-skoffer", lat, lon)
        param = [p.strip().lower() for p in parameters.split(",")]
        try:
            api.add_variables(model, *param)

            match model:
                case "minutely_15":
                    api.change_forecast_length("forecast_minutely_15", int(forecast_minutes / 15))
                    api.change_forecast_length("past_minutely_15", int(past_minutes / 15))
                case "hourly":
                    api.change_forecast_length("forecast_hours", forecast_hours)
                    api.change_forecast_length("past_hours", past_hours)
                case "daily":
                    api.change_forecast_length("forecast_days", forecast_days)
                    api.change_forecast_length("past_days", past_days)
        except Exception as e:
            await interaction.response.send_message(f"```\nerror when adding variables\n{e}\n```", ephemeral=True)
            return


        await interaction.response.defer()

        data = api.request()
        if not data:
            await interaction.followup.send("cannot get data from open-meteo")
            return

        # plotting
        timeline = data[model]["time"]
        dataunit = data[model + "_units"]
        datatype = {}
        figs = []

        # grouping same type of data into one graph
        for parameter in data[model].keys():
            if parameter == "time":
                continue
            category = weatherapi.WEATHER_PARAMETER_CATEGORY[parameter]
            if category not in datatype:
                datatype[category] = []
            datatype[category].append(parameter)

        # draw graphs
        for category in datatype.keys():
            plt.figure(figsize=(14, 10), dpi=150)

            x_axis_ticks = min(X_AXIS_MAX_TICKS, len(timeline))
            y_axis_ticks = min(Y_AXIS_MAX_TICKS, len(timeline))

            for parameter in datatype[category]:
                plt.plot(
                    timeline,
                    data[model][parameter],
                    # marker=random.choice("s^x*"),
                    linestyle="-",
                    color=random_vibrant_color(),
                    label=parameter,
                )

                ax = plt.gca()

                if parameter == "weather_code":
                    prev_code = -2
                    for i in range(len(timeline)):
                        wmo_code = data[model][parameter][i]
                        if not wmo_code:
                            wmo_code = -1
                        if wmo_code == prev_code:
                            continue
                        prev_code = wmo_code
                        ax.annotate(
                            weatherapi.WEATHER_WMO_CODE[str(wmo_code)],
                            (i, wmo_code),
                            textcoords="offset points",
                            xytext=(0, 5),
                            rotation=-90,
                            ha='center'
                        )
                else:
                    maxval = max((x for x in data[model][parameter] if x is not None))
                    minval = min((x for x in data[model][parameter] if x is not None))
                    deltaval = maxval - minval
                    minstep = deltaval / y_axis_ticks / 3

                    start_point = 0
                    while not data[model][parameter][start_point]:
                        start_point += 1
                    # find peak/valley
                    for i in range(start_point, len(timeline)):
                        if i == start_point or i == len(timeline) - 1:
                            if not data[model][parameter][i]:
                                continue

                            ax.annotate(
                                data[model][parameter][i],
                                (i, data[model][parameter][i]),
                                textcoords="offset points",
                                xytext=(0, 5),
                                ha='center'
                            )
                        else:
                            prev_val = data[model][parameter][i - 1]
                            current_val = data[model][parameter][i]
                            next_val = data[model][parameter][i + 1]
                            if not prev_val or not current_val or not next_val:
                                continue

                            if abs(prev_val - current_val) < minstep and abs(next_val - current_val) < minstep:
                                continue

                            prev_slope = (current_val - prev_val) / deltaval * y_axis_ticks
                            next_slope = (next_val - current_val) / deltaval * y_axis_ticks
                            if (
                                (prev_slope * next_slope >= 0 and abs(prev_slope - next_slope) > 4.5)
                                or (prev_slope * next_slope <= 0 and abs(prev_slope) + abs(next_slope) > 0.2)
                            ):
                                ax.annotate(
                                    data[model][parameter][i],
                                    (i, data[model][parameter][i]),
                                    textcoords="offset points",
                                    xytext=(0, 5),
                                    ha='center'
                                )

            unit = dataunit[random.choice(datatype[category])]
            if unit != "":
                unit = f" ({unit})"

            plt.xticks(rotation=90)
            plt.ylabel(f"{category}{unit}")
            plt.title(f"{category} of {location_name} over time")
            plt.legend()
            plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.7, color="gray")
            plt.tight_layout()

            ax = plt.gca()
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=x_axis_ticks))
            ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=y_axis_ticks))
            ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))

            buf = BytesIO()
            plt.savefig(buf, format="PNG", bbox_inches="tight")
            plt.close()
            buf.seek(0)
            figs.append(discord.File(fp=buf, filename=category + ".png"))

        await interaction.followup.send(f"plotted {model} weather stat of {location_name}\n[request url]({api.get_url()})", files=figs)
