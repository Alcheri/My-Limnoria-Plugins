###
# Copyright © 2021 - 2024, Barry Suridge
# All rights reserved.
###
import math
import re
import aiohttp
import asyncio
from datetime import datetime
from functools import lru_cache
from supybot import callbacks, ircutils, log
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weatherstack')
except ImportError:
    _ = lambda x: x

# Unicode Symbols
APOSTROPHE = u'\N{APOSTROPHE}'
DEGREE_SIGN = u'\N{DEGREE SIGN}'
PERCENT_SIGN = u'\N{PERCENT SIGN}'
QUOTATION_MARK = u'\N{QUOTATION MARK}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:110.0) Gecko/20100101 Firefox/110.0'
}

### Utility Functions ###
def handle_error(error: Exception, context: str = None):
    """Log and raise an error with context."""
    log.error(f"Error: {error} | Context: {context or 'None'}")
    raise callbacks.Error(f"An error occurred: {str(error)}")

def contains_number(value) -> bool:
    """Check if a string contains a number."""
    if not isinstance(value, str):
        raise ValueError("Input to contains_number must be a string.")
    return bool(re.findall(r"[0-9]+", value))

def colour_uvi(uvi: float) -> str:
    """Assign a descriptive text and colour to the UV Index value."""
    ranges = [
        (0, 3, 'light green', 'Low'),
        (3, 6, 'yellow', 'Moderate'),
        (6, 8, 'orange', 'High'),
        (8, 11, 'red', 'Very High'),
        (11, float('inf'), 'purple', 'Extreme')
    ]
    if uvi < 0:
        return ircutils.mircColor("Unknown UVI", "light grey")
    for lower, upper, colour, description in ranges:
        if lower <= uvi < upper:
            return ircutils.mircColor(f"UVI {uvi} ({description})", colour)
    return ircutils.mircColor("UVI Unknown", "grey")

def colour_temperature(celsius: float) -> str:
    """Colourize and format temperatures."""
    ranges = [
        (float('-inf'), 0, 'blue'),
        (0, 1, 'teal'),
        (1, 10, 'light blue'),
        (10, 20, 'light green'),
        (20, 30, 'yellow'),
        (30, 40, 'orange'),
        (40, float('inf'), 'red')
    ]
    for lower, upper, colour in ranges:
        if lower <= celsius < upper:
            formatted_temp = f"{celsius}{DEGREE_SIGN}C"
            return ircutils.mircColor(formatted_temp, colour)
    return ircutils.mircColor(f"{celsius}{DEGREE_SIGN}C", "grey")

@lru_cache(maxsize=64)
def dd2dms(longitude: float, latitude: float) -> tuple[str, str]:
    """Convert decimal degrees to degrees, minutes, and seconds."""
    def convert(coord):
        split_deg = math.modf(coord)
        degrees = int(split_deg[1])
        minutes = abs(int(math.modf(split_deg[0] * 60)[1]))
        seconds = abs(round(math.modf(split_deg[0] * 60)[0] * 60, 2))
        if seconds == 60.0:  # Handle rollover
            seconds = 0.0
            minutes += 1
        if minutes == 60:
            minutes = 0
            degrees += 1 if degrees >= 0 else -1
        return degrees, minutes, seconds

    degrees_x, minutes_x, seconds_x = convert(longitude)
    degrees_y, minutes_y, seconds_y = convert(latitude)

    x = f"{abs(degrees_x)}{DEGREE_SIGN}{minutes_x}{APOSTROPHE} {seconds_x}{QUOTATION_MARK} {'W' if degrees_x < 0 else 'E'}"
    y = f"{abs(degrees_y)}{DEGREE_SIGN}{minutes_y}{APOSTROPHE} {seconds_y}{QUOTATION_MARK} {'S' if degrees_y < 0 else 'N'}"
    return x, y

### Weatherstack Plugin ###
class Weatherstack(callbacks.Plugin):
    """
    A Weather plugin for Limnoria using the WeatherStack API.
    """
    threaded = False

    def __init__(self, irc):
        super().__init__(irc)

    ### API Integration Functions ###
    async def query_postal_code(self, code: str) -> list[float]:
        """Resolve latitude and longitude from a postcode using pgeocode."""
        postcode, countrycode = self._parse_postcode(code)
        try:
            from pgeocode import Nominatim
            nomi = Nominatim(countrycode)
            zip_data = nomi.query_postal_code(postcode)
            if zip_data.latitude is None or zip_data.longitude is None:
                raise ValueError("Incomplete data from pgeocode.")
            return [zip_data.latitude, zip_data.longitude]
        except Exception:
            log.warning(f"Falling back to OpenWeather API for '{postcode}, {countrycode}'.")
            return await self.query_postal_code_openweather(code)

    async def query_postal_code_openweather(self, code: str) -> list[float]:
        """Fallback: Use OpenWeather Geocoding API to resolve postcode."""
        apikey = self.registryValue("openweatherAPI")
        if not apikey:
            raise callbacks.Error("OpenWeather API key is missing.")
        url = "http://api.openweathermap.org/geo/1.0/zip"
        params = {"zip": code, "appid": apikey}
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    handle_error(f"Failed to resolve postcode: {response.status}", "OpenWeather Geocoding")
                data = await response.json()
        return [data["lat"], data["lon"]]

    async def fetch_weather(self, location: str) -> dict:
        """Fetch weather data from WeatherStack."""
        apikey = self.registryValue("weatherstackAPI")
        if not apikey:
            raise callbacks.Error("Weatherstack API key is missing.")
        url = "http://api.weatherstack.com/current"
        params = {"access_key": apikey, "query": location, "units": "m"}
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    handle_error(f"Failed to fetch weather: {response.status}", "WeatherStack API")
                return await response.json()

    ### Formatting Functions ###
    def format_weather_output(self, response: dict) -> str:
        """Format weather data for display."""
        location = response.get('location', {})
        current = response.get('current', {})
        coords = self.format_coordinates(location)
        weather = self.format_current_conditions(current)
        local_time = datetime.strptime(location['localtime'], "%Y-%m-%d %H:%M").strftime("%d-%m-%Y %H:%M")
        return f"{location['name']}, {location['region']}, {location['country']} | {coords} | {local_time} | {weather}"

    def format_coordinates(self, location: dict) -> str:
        """Format location coordinates."""
        lon, lat = dd2dms(float(location['lon']), float(location['lat']))
        return f"Lat: {lat}, Lon: {lon}"

    def format_current_conditions(self, current: dict) -> str:
        """Format current weather conditions."""
        description = re.sub(r"[^\w\s]", "", str(current['weather_descriptions']))
        temp = colour_temperature(current['temperature'])
        feels_like = colour_temperature(current['feelslike'])
        wind = f"{current['wind_speed']} Km/h {current['wind_dir']}"
        humidity = f"Humidity {current['humidity']}{PERCENT_SIGN}"
        precip = f"Precip: {current['precip']} mm/h"
        uvi = colour_uvi(current['uv_index'])
        return f"{description}, {humidity}, {precip}, Temp: {temp}, Feels like: {feels_like}, Wind: {wind}, {uvi}"

    ### IRC Command ###
    @wrap(["text"])
    def weather(self, irc, msg, args, location: str):
        """Get weather information for a town or city."""
        # Not 'enabled' in #channel.
        if not self.registryValue('enabled', msg.channel, irc.network):
            return
        
        if not location:
            irc.error("Specify a valid location (e.g., 'Ballarat, AU' or '3350, AU').")
            return
        location = location.lower()
        try:
            if contains_number(location):
                lat, lon = asyncio.run(self.query_postal_code(location))
                location = asyncio.run(self.get_location_by_coordinates(lat, lon))
            data = asyncio.run(self.fetch_weather(location))
            result = self.format_weather_output(data)
            irc.reply(result, prefixNick=False)
        except Exception as e:
            handle_error(e, "Weather Command")


Class = Weatherstack
