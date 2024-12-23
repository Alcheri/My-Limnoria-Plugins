###
# Copyright © MMXXIV, Barry Suridge
# All rights reserved.
#
###

import json
import math
try:
    import aiohttp       # asynchronous HTTP client and server framework
    import asyncio       # asynchronous I/O
    import pickle        # Python object serialization
except ImportError as ie:
    raise Exception(f'Cannot import module: {ie}')
import supybot.world as world
import supybot.conf as conf

from datetime import datetime, timezone
from supybot import utils, ircutils, callbacks, log
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
def handle_error(error, context=None):
    log.error(f"Error occurred: {error} | Context: {context if context else 'None'}")
    raise callbacks.Error(f"An error occurred: {error}")

class Weather(callbacks.Plugin):
    """
    A simple Weather plugin for Limnoria
    using the OpenWeather and Google Maps APIs.
    """
    threaded = True

    def __init__(self, irc):
        super().__init__(irc)
        self.db = {}
        self.load_db()
        world.flushers.append(self.flush_db)

    def load_db(self):
        """Load the existing database."""
        try:
            with open(FILENAME, 'rb') as f:
                self.db = pickle.load(f)
        except Exception as err:
            log.debug(f"load_db: Unable to load database: {err}")

    def flush_db(self):
        """Flushes the database to a file."""
        try:
            with open(FILENAME, 'wb') as f:
                pickle.dump(self.db, f, 2)
        except Exception as err:
            log.warning(f"flush_db: Unable to write database: {err}")

    def die(self):
        self.flush_db()
        world.flushers.remove(self.flush_db)
        super().die()

    # adapted from https://en.wikipedia.org/wiki/Ultraviolet_index#Index_usage
    @staticmethod
    def format_uvi_icon(uvi):
        """
        Displays a coloured icon relevant to the UV Index meter.
        Low: Green Moderate: Yellow High: Orange Very High: Red
        Extreme: Violet 🥵
        """
        if uvi < 0:
            icon = '⚪ Neutral'  # Neutral/unknown for invalid values
        elif uvi >= 0 and uvi < 3:
            icon = '🟢 Low'
        elif uvi >= 3 and uvi < 6:
            icon = '🟡 Moderate'
        elif uvi >= 6 and uvi < 8:
            icon = '🟠 High'
        elif uvi >= 8 and uvi <= 10.9:
            icon = '🔴 Very High'
        else:
            icon = '🟣 Extreme'
        return icon

    @staticmethod
    def format_temperature(celsius):
        """Colourise and format temperatures."""
        c = float(celsius)
        if c < 0:
            colour = 'blue'
        elif c == 0:
            colour = 'teal'
        elif c < 10:
            colour = 'light blue'
        elif c < 20:
            colour = 'light green'
        elif c < 30:
            colour = 'yellow'
        elif c < 40:
            colour = 'orange'
        else:
            colour = 'red'
        string = f"{c}{DEGREE_SIGN}C"
        return ircutils.mircColor(string, colour)

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

    async def fetch_data(self, url, params):
        """Fetch data from a given URL using aiohttp."""
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            handle_error(e, context=f"Fetching data from {url} with params {params}")

    async def google_maps(self, address):
        """Get location data from Google Maps API."""
        apikey = self.registryValue('googlemapsAPI')
        if not apikey:
            raise callbacks.Error("Please configure the Google Maps API key via plugins.Weather.googlemapsAPI [your_key_here]")

        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {'address': address, 'key': apikey}
        log.debug(f"Weather: using URL {url} with params {params} (googlemaps)")

        data = await self.fetch_data(url, params)

        if data.get('status') != 'OK':
            handle_error(data.get('status', 'Unknown error'), context=f"Google Maps API for address {address}")

        result_data = data['results'][0]
        lat = result_data['geometry']['location']['lat']
        lng = result_data['geometry']['location']['lng']
        postcode = next((comp['short_name'] for comp in result_data.get('address_components', []) if 'postal_code' in comp.get('types', [])), 'N/A')
        place_id = result_data.get('place_id', 'N/A')
        formatted_address = result_data.get('formatted_address', 'Unknown location')

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

    async def format_weather_results(self, location, weather_data):
        """Format weather data for display."""
        current = weather_data['current']
        formatted_data = []

        # Coordinates
        lat, lon = weather_data['lat'], weather_data['lon']
        (lat_dms, lon_dms) = self.dd2dms(lon, lat)
        formatted_data.append(f"{location} (Lat: {lat_dms}, Lon: {lon_dms})")

        # Current conditions
        temp = self.format_temperature(round(current['temp']))
        feels_like = self.format_temperature(round(current['feels_like']))
        desc = current['weather'][0]['description'].capitalize()
        humidity = f"Humidity: {current['humidity']}{PERCENT_SIGN}"
        wind_speed = f"Wind: {current['wind_speed']} m/s"
        uvicon = self.format_uvi_icon(current['uvi'])
        uvindex = current['uvi']
        uvi_index = f"UVI {uvindex} {uvicon}"

        formatted_data.append(f"{desc}, Temp: {temp}, Feels like: {feels_like}, {humidity}, {wind_speed}, {uvi_index}")

        return ' | '.join(formatted_data)

    async def format_forecast_results(self, location, weather_data):
        """Format multi-day forecast data for display."""
        daily = weather_data['daily']
        formatted_data = [f"Forecast for {location}:"]

        for day in daily[:5]:  # Limit to the next 5 days
            date = datetime.fromtimestamp(day['dt'], tz=timezone.utc).strftime('%A')
            desc = day['weather'][0]['description'].capitalize()
            min_temp = self.format_temperature(round(day['temp']['min']))
            max_temp = self.format_temperature(round(day['temp']['max']))
            formatted_data.append(f"{date}: {desc}, Min: {min_temp}, Max: {max_temp}")

        return ' | '.join(formatted_data)

    @wrap([getopts({'user': 'nick', 'forecast': ''}), additional('text')])
    def weather(self, irc, msg, args, optlist, location=None):
        """[--user <nick>] [--forecast] [<location>]

        Get the current weather for the specified location, or a default location.
        """
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

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
