###
# Copyright © 2021, Barry Suridge
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import json
import math
import re
import requests

# PyEphem astronomy library for Python
try:
    import ephem
except ImportError as ie:
    raise Exception(f'Cannot import module: {ie}')

# Python library for high performance off-line querying of GPS coordinates, region name and municipality name from postal codes
try:
    import pgeocode
except ImportError as ie:
    raise Exception(f'Cannot import module: {ie}')

from datetime import datetime
from functools import lru_cache
from requests.exceptions import HTTPError

from supybot import callbacks, ircutils
import supybot.log as log
from supybot.commands import *

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weatherstack')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

#XXX Unicode symbol (https://en.wikipedia.org/wiki/List_of_Unicode_characters#Latin-1_Supplement)
apostrophe     = u'\N{APOSTROPHE}'
degree_sign    = u'\N{DEGREE SIGN}'
#XXX micro_sign     = u'\N{MICRO SIGN}'
percent_sign   = u'\N{PERCENT SIGN}'
quotation_mark = u'\N{QUOTATION MARK}'

def contains_number(value):
    numbers = re.findall("[0-9]+", value)
    return True if numbers else False

def colour(celsius):
    """Colourise temperatures"""
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
    string = (f'{c}{degree_sign}C')

    return ircutils.mircColor(string, colour)

def day(lat, lon):
    """
    Compute the position of the sun. Is it daytime or nighttime?
    """
    home      = ephem.Observer()
    home.lat  = ephem.degrees(lat)           # str() Latitude
    home.lon  = ephem.degrees(lon)           # str() Longitude

    sun = ephem.Sun()

    log.info(f'Weatherstack [day]: lat: {home.lat} lon: {home.lon}')

    day = ''

    try:
        next_sunrise = home.next_rising(sun).datetime()
        next_sunset  = home.next_setting(sun).datetime()
        if next_sunset < next_sunrise:
          day = True
        else:
          day = False
    except ephem.NeverUpError:
        day = False
    return day

# XXX Converts decimal degrees to degrees, minutes, and seconds
@lru_cache(maxsize=4)  # XXX LRU caching
def dd2dms(longitude, latitude):
    # math.modf() splits whole number and decimal into tuple
    # eg 53.3478 becomes (0.3478, 53)
    split_degx = math.modf(longitude)

    # the whole number [index 1] is the degrees
    degrees_x = int(split_degx[1])

    # multiply the decimal part by 60: 0.3478 * 60 = 20.868
    # split the whole number part of the total as the minutes: 20
    # abs() absolute value - no negative
    minutes_x = abs(int(math.modf(split_degx[0] * 60)[1]))

    # multiply the decimal part of the split above by 60 to get the seconds
    # 0.868 x 60 = 52.08, round excess decimal places to 2 places
    # abs() absolute value - no negative
    seconds_x = abs(round(math.modf(split_degx[0] * 60)[0] * 60, 2))

    # repeat for latitude
    split_degy = math.modf(latitude)
    degrees_y  = int(split_degy[1])
    minutes_y  = abs(int(math.modf(split_degy[0] * 60)[1]))
    seconds_y  = abs(round(math.modf(split_degy[0] * 60)[0] * 60, 2))

    # account for E/W & N/S
    if degrees_x < 0:
        EorW = 'W'
    else:
        EorW = 'E'

    if degrees_y < 0:
        NorS = 'S'
    else:
        NorS = 'N'

    # abs() remove negative from degrees, was only needed for if-else above
    x = (
        str(abs(degrees_x))
        + f'{degree_sign}'
        + str(minutes_x)
        + f'{apostrophe} '
        + str(seconds_x)
        + f'{quotation_mark} '
        + EorW
    )
    y = (
        str(abs(degrees_y))
        + f'{degree_sign}'
        + str(minutes_y)
        + f'{apostrophe} '
        + str(seconds_y)
        + f'{quotation_mark} '
        + NorS
    )
    return (x, y)

class Weatherstack(callbacks.Plugin):
    """
    A simple Weather plugin for Limnoria
    using the WeatherStack API
    """

    threaded = True

    def __init__(self, irc):

        self.__parent = super(Weatherstack, self)
        self.__parent.__init__(irc)

    def format_weather_output(self, response):
        """
        Gather all the data - format it
        """
        try:
            location = response['location']
        except KeyError as e:
            raise callbacks.Error(f'{e} : city not found')

        current   = response['current']

        city_name = location['name']
        region    = location['region']
        country   = location['country']

        cr_date   = location['localtime']
        cr_date   = datetime.strptime(cr_date, '%Y-%m-%d %H:%M')
        cr_date   = cr_date.strftime('%d-%m-%Y %H:%M')

        # Convert lat, lon data into Degrees Minutes Seconds
        (lon, lat)   = dd2dms(int(float(location['lon'])), int(float(location['lat'])))

        description  = current['weather_descriptions']
        atmos        = current['pressure']
        weather_code = current['weather_code']
        # Get the cloud cover percentage
        cloud        = current['cloudcover']
        # Calculate the direction of the positional arrows
        arrow        = self._get_wind_direction(current['wind_degree'])
        precip       = current['precip']
        humidity     = current['humidity']
        temp         = current['temperature']
        feelslike    = current['feelslike']
        wind         = current['wind_speed']
        uvi          = current['uv_index']
        utc          = location['utc_offset']
        visibility   = response['current']['visibility']

        uvi_icon     = self._format_uvi_icon(uvi)

        self.log.info(f'Weatherstack[format_weather_output]: {city_name} lat {lat} lon {lon}')

        # Get weather_code from Weatherstack
        if not day(location['lat'], location['lon']):
            status_icon = '🌚'
        else:
            status_icon = self._get_status_icon(weather_code)

        if precip:
            precipico = '☔'
        else:
            precipico = ''

        # Remove unwanted characters from 'weather_descriptions'
        description = re.sub('[]\'[]', '', str(description))

        # Format output
        a = f'🏠 {city_name} {region} {country} :: Lat {lat} Lon {lon} :: UTC {utc} :: {cr_date} :: {status_icon} {description} '
        b = f'| 🌡 Barometric {atmos}hPa | ☁ Cloud cover {cloud}{percent_sign} | {precipico} Precip {precip}mm/h '
        c = f'| 💦 Humidity {humidity}{percent_sign} | Current {colour(temp)} '
        d = f'| Feels like {colour(feelslike)} | 🍃 Wind {wind}Km/H {arrow} '
        e = f'| 👁 Visibility {visibility}Km | UVI {uvi} {uvi_icon}'

        s = ""
        seq = [a, b, c, d, e]
        return s.join(seq)

    @staticmethod
    def _format_uvi_icon(uvi):
        """
        Diplays a coloured icon relevant to the UV Index meter.
        Low: Green Moderate: Yellow High: Orange Very High: Red
        Extreme: Violet 🥵
        """
        ico = float(uvi)
        if ico >= 0 and ico <= 2.9:
            icon = '🟢'
        elif ico >= 2 and ico <= 5.9:
            icon = '🟡'
        elif ico >= 5 and ico <= 7.9:
            icon = '🟠'
        elif ico >= 7 and ico <= 10.9:
            icon = '🔴'
        else:
            icon = '🟣'
        return icon

    @lru_cache(maxsize=4)  # XXX LRU caching
    def get_location_by_location(self, latitude, longitude):
        """
        This function returns a location from a reverse lookup.
        """
        apikey = self.registryValue("positionstackAPI")
        # Missing API Key.
        if not apikey:
            raise callbacks.Error(
                'Please configure the positionstack API key in config plugins.Weatherstack.positionstackAPI'
            )
        coordinates = f'{latitude}, {longitude}'
        params      = {'access_key': apikey, 'query': coordinates, 'limit': '1'}

        r = requests.get('http://api.positionstack.com/v1/reverse', params)
        responses = r.json()

        try:
            locality = responses['data'][0].get('locality')
        except KeyError:
            raise callbacks.Error('404: city not found')

        self.log.info(
            f'WeatherStack: get_location_by_location {locality}: {latitude},{longitude}'
        )

        return locality

    # Select the appropriate weather status icon
    @staticmethod
    def _get_status_icon(code):
        """
        Use the given code to attach appropriate
        weather status icon
        """
        code = str(code)
        switcher = {
            '113': '☀️',
            '116': '🌤',
            '119': '☁',
            '122': '☁',
            '143': '🌫️',
            '176': '🌧',
            '179': '🌨️',
            '182': '🌨️',
            '185': '☔',
            '200': '⛈️',
            '227': '💨',
            '230': '🌬️',
            '248': '🌫️',
            '260': '🌫️',
            '263': '🌧️',
            '266': '🌦',
            '281': '🌧️',
            '284': '🌧️',
            '293': '🌧',
            '296': '🌧',
            '299': '🌧',
            '302': '🌧',
            '305': '🌧️',
            '326': '🌨',
            '329': '❄',
            '353': '🌧',
            '356': '🌧',
            '371': '❄',
            '389': '⛈'
        }
        return switcher.get(code, "🤷")

    @staticmethod
    def _get_wind_direction(degrees):
        """Calculate wind direction"""
        num = degrees
        val = int((num/22.5)+.5)
        # Decorated output
        arr = [
            '↑ N',
            'NNE',
            '↗ NE',
            'ENE',
            '→ E',
            'ESE',
            '↘ SE',
            'SSE',
            '↓ S',
            'SSW',
            '↙ SW',
            'WSW',
            '← W',
            'WNW',
            '↖ NW',
            'NNW'
        ]
        return arr[(val % 16)]

    @lru_cache(maxsize=4)  # XXX LRU caching
    def query_postal_code(self, code):
        """
        This function returns longitude and latitude from
        a postcode."""
        postcode = code.split(',', 1)[0]
        try:
            countrycode = re.sub('[ ]', '', code.split(',', 1)[1])
        except IndexError:
            raise callbacks.Error('postcode, country code>')
        try:
            nomi = pgeocode.Nominatim(countrycode)
        except ValueError:
            raise callbacks.Error(f'{countrycode} is not a known country code.')
        zip = nomi.query_postal_code(postcode)

        self.log.info(f'Weatherstack: query_postal_code: {zip.latitude} {zip.longitude}')

        return [zip.latitude, zip.longitude]

    @wrap(["text"])
    def weather(self, irc, msg, args, location):
        """
        Get weather information for a town or city.

        [<city> <country code or country>] ][<postcode, country code>]

        I.E. weather Ballarat or Ballarat, AU/Australia OR 3350, AU
        """
        location = location.lower()

        apikey = self.registryValue('weatherstackAPI')
        # Missing API Key.
        if not apikey:
            raise callbacks.Error(
                'Please configure the Weatherstack API key in config plugins.Weatherstack.weatherstackAPI'
            )

        # Not 'enabled' in #channel.
        if not self.registryValue('enable', msg.channel, irc.network):
            return

        self.log.info(f'WeatherStack: running on {irc.network}/{msg.channel}')

        # Check if 'location' is a postcode.
        if contains_number(location):
            (lat, lon) = self.query_postal_code(location)
            location = self.get_location_by_location(lat, lon)

        # Initialise API data
        params = {'access_key': apikey, 'query': location, 'units': 'm'}

        try:
            api_result = requests.get('http://api.weatherstack.com/current', params)

            # If the response was successful, no Exception will be raised
            api_result.raise_for_status()
        except HTTPError as http_err:
            self.log.error(f'Weather: HTTP error occurred: {http_err}', exc_info=True)
            raise callbacks.Error(f'Weather: HTTP error occurred: {http_err}')
        except Exception as err:
            self.log.error(f'Weather: an error occurred: {err}', exc_info=True)
            raise callbacks.Error(f'Weather: an error occurred: {err}')
        else:
            api_response = api_result.json()  # Data collection

            # Print the weather output
            irc.reply(self.format_weather_output(api_response), prefixNick=False)

    @wrap(["something"])
    def help(self, irc):
        """418: I\'m a teapot"""


Class = Weatherstack

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
