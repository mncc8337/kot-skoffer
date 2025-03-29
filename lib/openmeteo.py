import requests


# see https://open-meteo.com/en/docs for more details

WEATHER_BASE_URL = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longtitude}&timezone=auto&"
WEATHER_FORECAST_LENGTH_LIMIT = {
    "forecast_days": 16,
    "forecast_hours": 16 * 24,
    "forecast_minutely_15": 16 * 24 * 60 / 15,

    "past_days": 92,
    "past_hours": 92 * 24,
    "past_minutely_15": 92 * 24 * 60 / 15,
}
WEATHER_AVAILABLE_PARAMETERS = {
    "current": (
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "shortwave_radiation",
        "direct_radiation",
        "direct_normal_irradiance",
        "global_tilted_irradiance",
        "global_tilted_irradiance_instant",
        "diffuse_radiation",
        "sunshine_duration",
        "lightning_potential",
        "precipitation",
        "snowfall",
        "rain",
        "showers",
        "snowfall_height",
        "freezing_level_height",
        "cape",
        "wind_speed_10m",
        "wind_speed_80m",
        "wind_direction_10m",
        "wind_direction_80m",
        "wind_gusts_10m",
        "visibility",
        "weather_code",
        "pressure_msl",
        "surface_pressure",
        "cloud_cover",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "wind_speed_120m",
        "wind_speed_180m",
        "wind_direction_120m",
        "wind_direction_180m",
        "vapour_pressure_deficit",
        "evapotranspiration",
        "et0_fao_evapotranspiration",
        "precipitation_probability",
        "snow_depth",
        "soil_temperature_0cm",
        "soil_temperature_6cm",
        "soil_temperature_18cm",
        "soil_temperature_54cm",
        "soil_moisture_0_to_1cm",
        "soil_moisture_1_to_3cm",
        "soil_moisture_3_to_9cm",
        "soil_moisture_9_to_27cm",
        "soil_moisture_27_to_81cm",
        "is_day",
    ),
    "minutely_15": (
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "shortwave_radiation",
        "direct_radiation",
        "direct_normal_irradiance",
        "global_tilted_irradiance",
        "global_tilted_irradiance_instant",
        "diffuse_radiation",
        "sunshine_duration",
        "lightning_potential",
        "precipitation",
        "snowfall",
        "rain",
        "showers",
        "snowfall_height",
        "freezing_level_height",
        "cape",
        "wind_speed_10m",
        "wind_speed_80m",
        "wind_direction_10m",
        "wind_direction_80m",
        "wind_gusts_10m",
        "visibility",
        "weather_code",
    ),
    "hourly": (
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "pressure_msl",
        "surface_pressure",
        "cloud_cover",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "wind_speed_10m",
        "wind_speed_80m",
        "wind_speed_120m",
        "wind_speed_180m",
        "wind_direction_10m",
        "wind_direction_80m",
        "wind_direction_120m",
        "wind_direction_180m",
        "wind_gusts_10m",
        "shortwave_radiation",
        "direct_radiation",
        "direct_normal_irradiance",
        "diffuse_radiation",
        "global_tilted_irradiance",
        "vapour_pressure_deficit",
        "cape",
        "evapotranspiration",
        "et0_fao_evapotranspiration",
        "precipitation",
        "snowfall",
        "precipitation_probability",
        "rain",
        "showers",
        "weather_code",
        "snow_depth",
        "freezing_level_height",
        "visibility",
        "soil_temperature_0cm",
        "soil_temperature_6cm",
        "soil_temperature_18cm",
        "soil_temperature_54cm",
        "soil_moisture_0_to_1cm",
        "soil_moisture_1_to_3cm",
        "soil_moisture_3_to_9cm",
        "soil_moisture_9_to_27cm",
        "soil_moisture_27_to_81cm",
        "is_day",
    ),
    "daily": (
        "temperature_2m_max",
        "temperature_2m_mean",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_mean",
        "apparent_temperature_min",
        "precipitation_sum",
        "rain_sum",
        "showers_sum",
        "snowfall_sum",
        "precipitation_hours",
        "precipitation_probability_max",
        "precipitation_probability_mean",
        "precipitation_probability_min",
        "weather_code",
        "sunrise",
        "sunset",
        "sunshine_duration",
        "daylight_duration",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "wind_direction_10m_dominant",
        "shortwave_radiation_sum",
        "et0_fao_evapotranspiration",
        "uv_index_max",
        "uv_index_clear_sky_max",
    ),
}
WEATHER_PARAMETER_CATEGORY = {
    "temperature_2m": "Temperature",
    "dew_point_2m": "Temperature",
    "apparent_temperature": "Temperature",
    "temperature_2m_max": "Temperature",
    "temperature_2m_mean": "Temperature",
    "temperature_2m_min": "Temperature",
    "apparent_temperature_max": "Temperature",
    "apparent_temperature_mean": "Temperature",
    "apparent_temperature_min": "Temperature",
    "freezing_level_height": "Temperature",
    "soil_temperature_0cm": "Soil Temperature",
    "soil_temperature_6cm": "Soil Temperature",
    "soil_temperature_18cm": "Soil Temperature",
    "soil_temperature_54cm": "Soil Temperature",

    "relative_humidity_2m": "Humidity",

    "pressure_msl": "Pressure",
    "surface_pressure": "Pressure",

    "cloud_cover": "Cloud Cover",
    "cloud_cover_low": "Cloud Cover",
    "cloud_cover_mid": "Cloud Cover",
    "cloud_cover_high": "Cloud Cover",

    "wind_speed_10m": "Wind Speed",
    "wind_speed_80m": "Wind Speed",
    "wind_speed_120m": "Wind Speed",
    "wind_speed_180m": "Wind Speed",
    "wind_speed_10m_max": "Wind Speed",

    "wind_direction_10m": "Wind Direction",
    "wind_direction_80m": "Wind Direction",
    "wind_direction_120m": "Wind Direction",
    "wind_direction_180m": "Wind Direction",
    "wind_direction_10m_dominant": "Wind Direction",

    "wind_gusts_10m": "Wind Gusts",
    "wind_gusts_10m_max": "Wind Gusts",

    "shortwave_radiation": "Solar Radiation",
    "direct_radiation": "Solar Radiation",
    "direct_normal_irradiance": "Solar Radiation",
    "diffuse_radiation": "Solar Radiation",
    "global_tilted_irradiance": "Solar Radiation",
    "shortwave_radiation_sum": "Solar Radiation",

    "precipitation": "Precipitation",
    "rain": "Precipitation",
    "showers": "Precipitation",
    "precipitation_sum": "Precipitation",
    "rain_sum": "Precipitation",
    "showers_sum": "Precipitation",

    "snowfall": "Snowfall",
    "snowfall_sum": "Snowfall",
    "snow_depth": "Snowfall",
    "snowfall_height": "Snowfall",

    "precipitation_probability": "Precipitation Probability",
    "precipitation_probability_max": "Precipitation Probability",
    "precipitation_probability_mean": "Precipitation Probability",
    "precipitation_probability_min": "Precipitation Probability",

    "precipitation_hours": "Precipitation Duration",

    "evapotranspiration": "Evapotranspiration",
    "et0_fao_evapotranspiration": "Evapotranspiration",

    "visibility": "Visibility",

    "weather_code": "Weather Conditions",

    "cape": "Storm Potential",
    "lightning_potential": "Storm Potential",

    "sunshine_duration": "Sunlight Duration",
    "daylight_duration": "Sunlight Duration",

    "sunrise": "Sunrise & Sunset",
    "sunset": "Sunrise & Sunset",

    "uv_index_max": "UV Index",
    "uv_index_clear_sky_max": "UV Index",

    "soil_moisture_0_to_1cm": "Soil Moisture",
    "soil_moisture_1_to_3cm": "Soil Moisture",
    "soil_moisture_3_to_9cm": "Soil Moisture",
    "soil_moisture_9_to_27cm": "Soil Moisture",
    "soil_moisture_27_to_81cm": "Soil Moisture",

    "is_day": "Daylight Indicator"
}
WEATHER_PARAMETER_DESCRIPTION = {
    "temperature_2m": "Air temperature at 2 meters above ground",
    "relative_humidity_2m": "Relative humidity at 2 meters above ground",
    "dew_point_2m": "Dew point temperature at 2 meters above ground",
    "apparent_temperature": "Apparent temperature is the perceived feels-like temperature combining wind chill factor, relative humidity and solar radiation",
    "pressure_msl": "Atmospheric air pressure reduced to mean sea level",
    "surface_pressure": "Pressure at surface, which gets lower with increasing elevation",
    "cloud_cover": "Total cloud cover as an area fraction",
    "cloud_cover_low": "Low level clouds and fog up to 3 km altitude",
    "cloud_cover_mid": "Mid level clouds from 3 to 8 km altitude",
    "cloud_cover_high": "High level clouds from 8 km altitude",
    "wind_speed_10m": "Wind speed at 10 meters above ground",
    "wind_speed_80m": "Wind speed at 80 meters above ground",
    "wind_speed_120m": "Wind speed at 120 meters above ground",
    "wind_speed_180m": "Wind speed at 180 meters above ground",
    "wind_direction_10m": "Wind direction at 10 meters above ground",
    "wind_direction_80m": "Wind direction at 80 meters above ground",
    "wind_direction_120m": "Wind direction at 120 meters above ground",
    "wind_direction_180m": "Wind direction at 180 meters above ground",
    "wind_gusts_10m": "Gusts at 10 meters above ground as a maximum of the preceding hour",
    "shortwave_radiation": "Shortwave solar radiation as average of the preceding hour",
    "direct_radiation": "Direct solar radiation as average of the preceding hour on the horizontal plane",
    "direct_normal_irradiance": "Direct solar radiation on the normal plane (perpendicular to the sun)",
    "diffuse_radiation": "Diffuse solar radiation as average of the preceding hour",
    "global_tilted_irradiance": "Total radiation received on a tilted pane as average of the preceding hour",
    "vapour_pressure_deficit": "Vapour Pressure Deficit (VPD) in kilopascal (kPa). High VPD (>1.6) increases plant transpiration, low VPD (<0.4) decreases it",
    "cape": "Convective available potential energy",
    "evapotranspiration": "Evapotranspiration from land surface and plants",
    "et0_fao_evapotranspiration": "ET₀ Reference Evapotranspiration of a well-watered grass field",
    "precipitation": "Total precipitation (rain, showers, snow) sum of the preceding hour",
    "snowfall": "Snowfall amount of the preceding hour in centimeters",
    "precipitation_probability": "Probability of precipitation with more than 0.1 mm",
    "rain": "Rain from large-scale weather systems in millimeters",
    "showers": "Showers from convective precipitation in millimeters",
    "weather_code": "Weather condition as a numeric WMO code",
    "snow_depth": "Snow depth on the ground",
    "freezing_level_height": "Altitude above sea level of the 0°C level",
    "visibility": "Viewing distance in meters",
    "soil_temperature_0cm": "Temperature in the soil at 0 cm depth",
    "soil_temperature_6cm": "Temperature in the soil at 6 cm depth",
    "soil_temperature_18cm": "Temperature in the soil at 18 cm depth",
    "soil_temperature_54cm": "Temperature in the soil at 54 cm depth",
    "soil_moisture_0_to_1cm": "Average soil water content at 0-1 cm depth",
    "soil_moisture_1_to_3cm": "Average soil water content at 1-3 cm depth",
    "soil_moisture_3_to_9cm": "Average soil water content at 3-9 cm depth",
    "soil_moisture_9_to_27cm": "Average soil water content at 9-27 cm depth",
    "soil_moisture_27_to_81cm": "Average soil water content at 27-81 cm depth",
    "is_day": "1 if the current time step has daylight, 0 at night",
    "temperature_2m_max": "Maximum daily air temperature at 2 meters above ground",
    "temperature_2m_mean": "Mean daily air temperature at 2 meters above ground",
    "temperature_2m_min": "Minimum daily air temperature at 2 meters above ground",
    "apparent_temperature_max": "Maximum daily apparent temperature",
    "apparent_temperature_mean": "Mean daily apparent temperature",
    "apparent_temperature_min": "Minimum daily apparent temperature",
    "precipitation_sum": "Sum of daily precipitation (including rain, showers, and snowfall)",
    "rain_sum": "Sum of daily rain",
    "showers_sum": "Sum of daily showers",
    "snowfall_sum": "Sum of daily snowfall",
    "precipitation_hours": "The number of hours with rain",
    "precipitation_probability_max": "Maximum probability of precipitation",
    "precipitation_probability_mean": "Mean probability of precipitation",
    "precipitation_probability_min": "Minimum probability of precipitation",
    "sunrise": "Sunrise time",
    "sunset": "Sunset time",
    "sunshine_duration": "Number of seconds of sunshine per day",
    "daylight_duration": "Number of seconds of daylight per day",
    "wind_speed_10m_max": "Maximum wind speed at 10 meters above ground",
    "wind_gusts_10m_max": "Maximum wind gusts at 10 meters above ground",
    "wind_direction_10m_dominant": "Dominant wind direction at 10 meters above ground",
    "shortwave_radiation_sum": "Sum of solar radiation on a given day in Megajoules",
    "uv_index_max": "Daily maximum UV Index",
    "uv_index_clear_sky_max": "Daily maximum UV Index assuming cloud-free conditions"
}
WEATHER_WMO_CODE = {
    "-1": "No data",
    "0": "Clear",
    "1": "Mostly clear",
    "2": "Partly cloudy",
    "3": "Overcast",
    "45": "Fog",
    "48": "Rime fog",
    "51": "Light drizzle",
    "53": "Moderate drizzle",
    "55": "Heavy drizzle",
    "56": "Light freezing drizzle",
    "57": "Heavy freezing drizzle",
    "61": "Light rain",
    "63": "Moderate rain",
    "65": "Heavy rain",
    "66": "Light freezing rain",
    "67": "Heavy freezing rain",
    "71": "Light snow",
    "73": "Moderate snow",
    "75": "Heavy snow",
    "77": "Snow grains",
    "80": "Light showers",
    "81": "Moderate showers",
    "82": "Heavy showers",
    "85": "Light snow showers",
    "86": "Heavy snow showers",
    "95": "Thunderstorm",
    "96": "Thunderstorm, light hail",
    "99": "Thunderstorm, heavy hail"
}


def search_location(query: str, limit: int = 1, user_agent: str = "dummy"):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit={limit}"
    response = requests.get(url, headers={"User-Agent": user_agent})

    if response.status_code != 200:
        return None
    return response.json()


def reverse_location(lat: float, lon: float, user_agent: str = "dummy"):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url, headers={"User-Agent": user_agent})

    if response.status_code != 200:
        return None
    return response.json()


class OpenMeteoWeather:
    def __init__(self, user_agent: str, latitude: float, longtitude: float):
        self.user_agent = user_agent
        self.latitude = latitude
        self.longtitude = longtitude

        self.parameters = {
            "current": set(),
            "minutely_15": set(),
            "hourly": set(),
            "daily": set(),
        }

        self.forecast_length = {
            "forecast_days": 0,
            "forecast_hours": 0,
            "forecast_minutely_15": 0,

            "past_days": 0,
            "past_hours": 0,
            "past_minutely_15": 0,
        }

    def get_url(self):
        ret = WEATHER_BASE_URL.format(
            latitude=self.latitude,
            longtitude=self.longtitude
        )

        for key in self.parameters.keys():
            if len(self.parameters[key]) == 0:
                continue
            ret += key + "=" + ",".join(self.parameters[key]) + "&"

        for key in self.forecast_length.keys():
            ret += key + "=" + str(self.forecast_length[key]) + "&"

        return ret

    def set_location(self, latitude: float, longtitude: float):
        self.latitude = latitude
        self.longtitude = longtitude

    def add_variables(self, model: str, *items):
        if model not in WEATHER_AVAILABLE_PARAMETERS.keys():
            raise Exception(f"model {model} is invalid")

        for item in items:
            if item not in WEATHER_AVAILABLE_PARAMETERS[model]:
                raise Exception(f"item {item} is invalid")
            self.parameters[model].add(item)

    def remove_variables(self, model: str, *items):
        if model not in WEATHER_AVAILABLE_PARAMETERS.keys():
            raise Exception(f"model {model} is invalid")

        for item in items:
            if item not in WEATHER_AVAILABLE_PARAMETERS[model]:
                raise Exception(f"item {item} is invalid")
            self.parameters[model].remove(item)

    def change_forecast_length(self, model: str, value):
        if model not in WEATHER_FORECAST_LENGTH_LIMIT.keys():
            raise Exception(f"model {model} is invalid")
        if value > WEATHER_FORECAST_LENGTH_LIMIT[model]:
            raise Exception(f"value exceeding limit (value {value}, limit {WEATHER_FORECAST_LENGTH_LIMIT[model]})")
        self.forecast_length[model] = value

    def request(self):
        response = requests.get(
            self.get_url(),
            headers={"User-Agent": self.user_agent}
        )

        if response.status_code != 200:
            return None

        return response.json()
