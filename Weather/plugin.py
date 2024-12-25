###
# Copyright © MMXXIV, Barry Suridge
# All rights reserved.
#
###
#
# A fully asynchronous Weather plugin for Limnoria using the OpenWeather and Google Maps APIs.
#
##
import json
import math
try:
    import aiohttp       # asynchronous HTTP client and server framework
    import asyncio       # asynchronous I/O
except ImportError as ie:
    raise Exception(f'Cannot import module: {ie}')
from datetime import datetime, timezone

import supybot.world as world
import supybot.conf as conf
from supybot import ircutils, callbacks, log
from supybot.commands import *

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weather')
except ImportError:
    _ = lambda x: x

# Constants
APOSTROPHE = u'\N{APOSTROPHE}'
DEGREE_SIGN = u'\N{DEGREE SIGN}'
PERCENT_SIGN = u'\N{PERCENT SIGN}'
QUOTATION_MARK = u'\N{QUOTATION MARK}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:110.0) Gecko/20100101 Firefox/110.0'
}
FILENAME = conf.supybot.directories.data.dirize('Weather.db')

# Global Error Routine
def handle_error(error: Exception, context: str = None, user_message: str = "An error occurred."):
    """
    Log and handle errors gracefully.

    Args:
        error (Exception): The exception object.
        context (str): Additional context about the error.
        user_message (str): Message to display to the user.
    """
    log.error(f"Error occurred: {error} | Context: {context or 'No additional context provided.'}")
    raise callbacks.Error(user_message)

class Weather(callbacks.Plugin):
    """
    A simple Weather plugin for Limnoria
    using the OpenWeather and Google Maps APIs.
    """
    threaded = False

    def __init__(self, irc):
        super().__init__(irc)
        self.db = {}
        self.load_db()
        world.flushers.append(self.flush_db)

    def load_db(self):
        try:
            with open(FILENAME, 'r') as f:
                self.db = json.load(f)
        except FileNotFoundError:
            self.db = {}
        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse the database file: {e}")
            self.db = {}
        except Exception as e:
            log.warning(f"Unable to load database: {e}")

    def flush_db(self):
        try:
            with open(FILENAME, 'w') as f:
                json.dump(self.db, f, indent=4)
        except Exception as e:
            log.warning(f"Unable to save database: {e}")

    def die(self):
        self.flush_db()
        world.flushers.remove(self.flush_db)
        super().die()
    
    #XXX Utilities

    # adapted from https://www.epa.gov/enviro/uv-index-description
    @staticmethod
    def colour_uvi(uvi: float) -> str:
        """
        Assigns a descriptive text and colour to the UV Index value.
        """
        # Define ranges, colours, and descriptions
        ranges = [
            (0, 3, 'light green', 'Low'),
            (3, 6, 'yellow', 'Moderate'),
            (6, 8, 'orange', 'High'),
            (8, 11, 'red', 'Very High'),
            (11, float('inf'), 'purple', 'Extreme')
        ]

        # Handle invalid values
        if uvi < 0:
            return ircutils.mircColor(f"Unknown UVI", "light grey")

        # Match the UV index to a range and return coloured text with description
        for lower, upper, colour, description in ranges:
            if lower <= uvi < upper:
                return ircutils.mircColor(f"UVI {uvi} ({description})", colour)

        # Fallback (should not happen)
        return ircutils.mircColor("UVI Unknown", "grey")

    @staticmethod
    def colour_temperature(celsius: float) -> str:
        """
        Colourise and format temperatures.
        """
        # Define ranges, colours, and descriptions
        ranges = [
            (float('-inf'), 0, 'blue'),         # Below 0°C
            (0, 1, 'teal'),                     # Exactly 0°C
            (1, 10, 'light blue'),              # 1°C to < 10°C
            (10, 20, 'light green'),            # 10°C to < 20°C
            (20, 30, 'yellow'),                 # 20°C to < 30°C
            (30, 40, 'orange'),                 # 30°C to < 40°C
            (40, float('inf'), 'red')           # 40°C and above
        ]

        # Ensure the input is a float
        c = float(celsius)

        # Match the temperature to a range and colour it
        for lower, upper, colour in ranges:
            if lower <= c < upper:
                formatted_temp = f"{c}{DEGREE_SIGN}C"
                return ircutils.mircColor(formatted_temp, colour)

        # Fallback (should not happen)
        return ircutils.mircColor(f"{c}{DEGREE_SIGN}C", "grey")
    
    def dd2dms(self, longitude, latitude):
        """Convert decimal degrees to degrees, minutes, and seconds."""
        def convert(coord):
            split_deg = math.modf(coord)
            degrees = int(split_deg[1])
            minutes = abs(int(math.modf(split_deg[0] * 60)[1]))
            seconds = abs(round(math.modf(split_deg[0] * 60)[0] * 60, 2))
            return degrees, minutes, seconds

        degrees_x, minutes_x, seconds_x = convert(longitude)
        degrees_y, minutes_y, seconds_y = convert(latitude)

        x = f"{abs(degrees_x)}{DEGREE_SIGN}{minutes_x}{APOSTROPHE} {seconds_x}{QUOTATION_MARK} {'W' if degrees_x < 0 else 'E'}"
        y = f"{abs(degrees_y)}{DEGREE_SIGN}{minutes_y}{APOSTROPHE} {seconds_y}{QUOTATION_MARK} {'S' if degrees_y < 0 else 'N'}"
        return x, y

    def format_location(self, lat: float, lon: float, location: str) -> str:
        """Format location and coordinates for display."""
        lat_dms, lon_dms = self.dd2dms(lon, lat)
        return f"{location} (Lat: {lat_dms}, Lon: {lon_dms})"

    def format_current_conditions(self, current: dict) -> str:
        """Format current weather conditions for display."""

        temp = self.colour_temperature(round(current['temp']))
        feels_like = self.colour_temperature(round(current['feels_like']))
        desc = current['weather'][0]['description'].capitalize()
        humidity = f"Humidity: {current['humidity']}{PERCENT_SIGN}"
        cloud = f"Clouds: {current['clouds']}"
        log.error(f"{current}")
        wind_speed = f"Wind: {round(current['wind_speed'] * 3.6)} Km/h"
        wind_direction = self._get_wind_direction(current['wind_deg'])
        uvi_index = self.colour_uvi(round(current['uvi']))

        return f"{desc}, Temp: {temp}, Feels like: {feels_like}, {humidity}, {cloud}{PERCENT_SIGN}, {wind_speed} {wind_direction}, {uvi_index}"

    @staticmethod
    def _get_wind_direction(degrees: float) -> str:
        """
        Calculate and return the wind direction as text.
        """
        degrees = degrees % 360  # Normalise to 0-359
        # Ensure degrees is a float for calculations
        val = int((degrees / 22.5) + 0.5)
    
        # Purely textual wind direction labels
        directions = [
            'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
        ]
    
        # Return the corresponding direction
        return directions[val % 16]

    #XXX Async Functions

    async def fetch_data(self, url: str, params: dict) -> dict:
        """
        Fetch JSON data from the given URL with specified parameters.

        Args:
            url (str): The API endpoint URL.
            params (dict): Query parameters.

        Returns:
            dict: Parsed JSON response.
        """
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            handle_error(e, context=f"HTTP error for {url} with {params}")
        except Exception as e:
            handle_error(e, context=f"Fetching data from {url} with {params}")

    async def google_maps(self, address: str) -> tuple:
        """Get location data from Google Maps API."""
        apikey = self.registryValue('googlemapsAPI')
        if not apikey:
            raise callbacks.Error("Google Maps API key is missing. Configure it with plugins.Weather.googlemapsAPI [your_key].")

        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {'address': address, 'key': apikey}

        log.debug(f"Using Google Maps API with {url} and params: {params}")

        data = await self.fetch_data(url, params)
        if data.get('status') != 'OK':
            handle_error(data.get('status', 'Unknown error'), context=f"Google Maps API for address {address}")

        result = data['results'][0]
        lat = result['geometry']['location']['lat']
        lng = result['geometry']['location']['lng']
        postcode = next((c['short_name'] for c in result.get('address_components', []) if 'postal_code' in c.get('types', [])), 'N/A')
        place_id = result.get('place_id', 'N/A')
        formatted_address = result.get('formatted_address', 'Unknown location')

        return formatted_address, lat, lng, postcode, place_id

    async def openweather(self, lat, lon):
        """Fetch weather data from OpenWeather API."""
        apikey = self.registryValue('openweatherAPI')
        if not apikey:
            raise callbacks.Error("Please configure the OpenWeather API key via plugins.Weather.openweatherAPI [your_key_here]")

        url = 'https://api.openweathermap.org/data/3.0/onecall'
        params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'hourly,minutely,alerts',
            'appid': apikey,
            'units': 'metric'
        }
        log.debug(f"Weather: using URL {url} with params {params} (openweather)")

        data = await self.fetch_data(url, params)
        return data

    async def format_weather_results(self, location: str, weather_data: dict) -> str:
        """Format weather data for display."""
        formatted_data = [self.format_location(weather_data['lat'], weather_data['lon'], location)]
        formatted_data.append(self.format_current_conditions(weather_data['current']))
        return ' | '.join(formatted_data)

    async def format_forecast_results(self, location, weather_data):
        """Format multi-day forecast data for display."""
        daily = weather_data['daily']
        formatted_data = [f"Forecast for {location}:"]

        for day in daily[:5]:  # Limit to the next 5 days
            date = datetime.fromtimestamp(day['dt'], tz=timezone.utc).strftime('%A')
            desc = day['weather'][0]['description'].capitalize()
            min_temp = self.colour_temperature(round(day['temp']['min']))
            max_temp = self.colour_temperature(round(day['temp']['max']))
            formatted_data.append(f"{date}: {desc}, Min: {min_temp}, Max: {max_temp}")

        return ' | '.join(formatted_data)

    @wrap([getopts({'user': 'nick', 'forecast': ''}), additional('text')])
    def weather(self, irc, msg, args, optlist, location=None):
        """[--user <nick>] [--forecast] [<location>]

        Get the current weather for the specified location, or a default location.
        """
        # Not 'enabled' in #channel.
        if not self.registryValue('enabled', msg.channel, irc.network):
            return
        
        optlist = dict(optlist)

        # Handle user-specific location
        if not location:
            try:
                if 'user' in optlist:
                    host = irc.state.nickToHostmask(optlist['user'])
                else:
                    host = msg.prefix
                ident_host = host.split('!')[1]
                location = self.db[ident_host]
            except KeyError:
                irc.error(
                    f'No location for %s is set. Use the \u2018set\u2019 command '
                    f'to set a location for your current hostmask, or call \u2018weather\u2019 '
                    f'with <location> as an argument.'
                    % ircutils.bold('*!' + ident_host),
                    Raise=True,
                )
        location = location.lower()

        async def process_weather():
            try:
                # Fetch location details from Google Maps API
                formatted_address, lat, lon, _, _ = await self.google_maps(location)

                # Fetch weather data from OpenWeather API
                weather_data = await self.openweather(lat, lon)

                # Format the results for output
                forecast = 'forecast' in optlist
                if forecast:
                    return await self.format_forecast_results(formatted_address, weather_data)
                else:
                    return await self.format_weather_results(formatted_address, weather_data)

            except Exception as e:
                handle_error(e, context=f"Processing weather command for location: {location}")

        # Run the async process
        try:
            result = asyncio.run(process_weather())
            if result:
                irc.reply(result, prefixNick=False)
        except Exception as e:
            handle_error(e, context="Executing weather command")

    @wrap(["text"])
    def set(self, irc, msg, args, location):
        """<location>

        Set a default location for your current hostmask.
        """
        ident_host = msg.prefix.split('!')[1]
        self.db[ident_host] = location.lower()
        irc.replySuccess()

    @wrap([])
    def unset(self, irc, msg, args):
        """
        Unset the default location for your current hostmask.
        """
        ident_host = msg.prefix.split('!')[1]
        if ident_host in self.db:
            del self.db[ident_host]
            irc.replySuccess()
        else:
            irc.error("No default location set for your hostmask.")

    @wrap(["text"])
    def google(self, irc, msg, args, location):
        """Look up <location>

        [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] [latitude, longitude]
        <address>
        """
        async def process_google():
            try:
                display_name, lat, lng, postcode, place_id = await self.google_maps(location.lower())
                formatted_txt = f"\x02{display_name}\x02 \x02{postcode}\x02 [ID: {place_id}] \x02{lat}\x02 \x02{lng}\x02"
                irc.reply(f"From Google Maps: {formatted_txt}", prefixNick=False)
            except Exception as e:
                handle_error(e, context=f"Processing Google command for location: {location}")

        asyncio.run(process_google())

    @wrap(['text'])
    def help(self, irc, msg, args):
        """
        [--user <nick>] [--forecast] [<location>]

        [set location] | [unset]

        Get the current weather information for a town, city or address.

        [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] <address>

        I.E. 'weather' Ballarat or Ballarat AU OR 3350 AU or 'weather' 38.9071923 -77.036870

         | 'google' [city <(Alpha-2) country code>] to get latitude and longitude of a city/town.
        """

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
