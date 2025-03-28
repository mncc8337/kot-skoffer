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
WEATHER_AVAILABLE_ITEMS = {
    "current": (
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
        "global_tilted_irradiance_instant",
        "sunshine_duration",
        "lightning_potential",
        "snowfall_height",
    ),
    "minutely_15": (
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


def search_location(query, limit=1, user_agent="dummy"):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit={limit}"
    response = requests.get(url, headers={"User-Agent": user_agent})

    return response.json()


class OpenMeteoWeather:
    items = {
        "current": set(),
        "minutely_15": set(),
        "hourly": set(),
        "daily": set(),
    }

    forecast_length = {
        "forecast_days": 0,
        "forecast_hours": 0,
        "forecast_minutely_15": 0,

        "past_days": 0,
        "past_hours": 0,
        "past_minutely_15": 0,
    }

    user_agent = ""
    latitude = 0.0
    longtitude = 0.0

    def __init__(self, user_agent: str, latitude: float, longtitude: float):
        self.user_agent = user_agent
        self.latitude = latitude
        self.longtitude = longtitude

    def get_url(self):
        ret = WEATHER_BASE_URL.format(
            latitude=self.latitude,
            longtitude=self.longtitude
        )

        for key in self.items.keys():
            if len(self.items[key]) == 0:
                continue
            ret += key + "=" + ",".join(self.items[key]) + "&"

        return ret

    def set_location(self, latitude: float, longtitude: float):
        self.latitude = latitude
        self.longtitude = longtitude

    def add_forecast_items(self, _type: str, *items):
        if _type not in WEATHER_AVAILABLE_ITEMS.keys():
            raise Exception(f"type {_type} is invalid")

        for item in items:
            if item not in WEATHER_AVAILABLE_ITEMS[_type]:
                raise Exception(f"item {item} is invalid")
            self.items[_type].add(item)

    def remove_forecast_items(self, _type: str, *items):
        if _type not in WEATHER_AVAILABLE_ITEMS.keys():
            raise Exception(f"type {_type} is invalid")

        for item in items:
            if item not in WEATHER_AVAILABLE_ITEMS[_type]:
                raise Exception(f"item {item} is invalid")
            self.items[_type].remove(item)

    def change_forecast_length(self, _type: str, value):
        if _type not in WEATHER_FORECAST_LENGTH_LIMIT.keys():
            raise Exception(f"type {_type} is invalid")
        if value > WEATHER_FORECAST_LENGTH_LIMIT[_type]:
            raise Exception(f"value exceeding limit (value {value}, limit {WEATHER_FORECAST_LENGTH_LIMIT[_type]})")
        self.forecast_length[_type] = value

    def request(self):
        response = requests.get(
            self.get_url(),
            headers={"User-Agent": self.user_agent}
        )

        if response.status_code != 200:
            return None

        return response.json()
