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
import math
import re
import requests
from datetime import datetime
from functools import lru_cache
from requests.exceptions import HTTPError

import supybot.log as log
from supybot.commands import *
from supybot import callbacks, ircutils

#XXX Unicode symbol (https://en.wikipedia.org/wiki/List_of_Unicode_characters#Latin-1_Supplement)
apostrophe     = u'\N{APOSTROPHE}'
degree_sign    = u'\N{DEGREE SIGN}'
#XXX micro_sign     = u'\N{MICRO SIGN}'
percent_sign   = u'\N{PERCENT SIGN}'
quotation_mark = u'\N{QUOTATION MARK}'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Debian; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0'
}

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

#XXX Converts decimal degrees to degrees, minutes, and seconds
@lru_cache(maxsize=4)    #XXX LRU caching
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
        + f"{degree_sign}"
        + str(minutes_x)
        + f"{apostrophe} "
        + str(seconds_x)
        + f"{quotation_mark} "
        + EorW
    )
    y = (
        str(abs(degrees_y))
        + f"{degree_sign}"
        + str(minutes_y)
        + f"{apostrophe} "
        + str(seconds_y)
        + f"{quotation_mark} "
        + NorS
    )
    return (x, y)

class Weather(callbacks.Plugin):
    """
    A simple Weather plugin for Limnoria
    using the OpenWeatherMap API
    """
    threaded = True

    def __init__(self, irc):

        self.__parent = super(Weather, self)
        self.__parent.__init__(irc)

    def format_weather_output(self, location, data):
        """
        Gather all the data - format it
        """
        log.info(f'Weather: format_weather_output {location}')

        current    = data['current']
        icon       = current['weather'][0].get('icon')
        staticon   = self._get_status_icon(icon)
        (LON, LAT) = dd2dms(data['lon'], data['lat'])
        # current
        cloud      = current['clouds']
        arrow      = self._get_wind_direction(current['wind_deg'])
        feelslike  = round(current['feels_like'])
        humid      = current['humidity']
        atmos      = current['pressure']
        dp         = round(current['dew_point'])
        try:
            precip = data['hourly'][0]['rain'].get('1h')
            precipico = '☔'
        except KeyError:
            precip = 0
            precipico = '☂'
        temp   = round(current['temp'])
        vis    = round((current['visibility'] / 1000))
        uvi    = round(current['uvi'])
        uvicon = self._format_uvi_icon(uvi)
        utc    = (data['timezone_offset']/3600)
        # weather
        desc   = current['weather'][0].get('description')
        wind   = round(current['wind_speed'])

        try:
            gust = round(current['wind_gust'])
        except KeyError:
            gust = 0

        # Forecast day one
        day1        = data['daily'][1]
        day1name    = datetime.fromtimestamp(day1['dt']).strftime('%A')
        day1weather = day1['weather'][0].get('description')
        day1highC   = round(day1['temp'].get('max'))
        day1lowC    = round(day1['temp'].get('min'))

        # Forecast day two
        day2        = data['daily'][2]
        day2name    = datetime.fromtimestamp(day2['dt']).strftime('%A')
        day2weather = day2['weather'][0].get('description')
        day2highC   = round(day2['temp'].get('max'))
        day2lowC    = round(day2['temp'].get('min'))

        # Formatted output
        a = f'🏠 {location} :: UTC {utc} :: Lat {LAT} Lon {LON} :: {staticon} {desc} '
        b = f'| 🌡 Barometric {atmos}hPa | Dew Point {dp}°C | ☁ Cloud cover {cloud}{percent_sign} '
        c = f'| {precipico} Precip {precip}mm/h | 💦 Humidity {humid}{percent_sign} | Current {colour(temp)} '
        d = f'| Feels like {colour(feelslike)} | 🍃 Wind {wind}Km/H {arrow} '
        e = f'| 💨 Gust {gust}m/s | 👁 Visibility {vis}Km | UVI {uvi} {uvicon} '
        f = f'| {day1name}: {day1weather} Max {colour(day1highC)} Min {colour(day1lowC)} '
        g = f'| {day2name}: {day2weather} Max {colour(day2highC)} Min {colour(day2lowC)}.'

        s = ''
        seq = [a, b, c, d, e, f, g]
        return((s.join(seq)))

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

    @staticmethod
    def _get_status_icon(code):
        """
        Use the given code to display appropriate
        weather status icon
        """
        switcher = {
            '01d': '☀',
            '01n': '🌚',
            '02d': '🌤',
            '02n': '🌚',
            '03d': '☁',
            '03n': '🌚',
            '04d': '☁',
            '04n': '🌚',
            '09d': '🌦',
            '09n': '🌚',
            '10d': '🌦',
            '10n': '🌚',
            '11d': '⛈',
            '11n': '⛈',
            '13d': '❄',
            '13n': '❄',
            '50d': '🌫',
            '50n': '🌫',
        }
        return switcher.get(code, '🤷')

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

    # Credit: https://github.com/jlu5/SupyPlugins/blob/7fdf95074c415bfd92488c2a1177306cd22f10eb/NuWeather/plugin.py#L261
    @lru_cache(maxsize=4)    #XXX LRU caching
    def osm_geocode(self, location):
        location = location.lower()
        uri = f'https://nominatim.openstreetmap.org/search/{location}?format=jsonv2&accept-language="en"'
        log.info(f'Weather: using url {uri} (OSM/Nominatim)')
        # User agent is required
        try:
            req = requests.get(uri, headers=headers)

            # If the response was successful, no Exception will be raised
            req.raise_for_status()

            data = req.json()
        except HTTPError as http_err:
            self.log.debug(f'Weather: error {http_err} searching for {location} from OSM/Nominatim:',
                      exc_info=True)
            data = None
        if not data:
            raise callbacks.Error(f'Unknown location {location} from OSM/Nominatim')
        data = data[0]
        # Limit location verbosity to 3 divisions (e.g. City, Province/State, Country)
        display_name = data['display_name']
        display_name_parts = display_name.split(', ')
        if len(display_name_parts) > 3:
            # Try to remove ZIP code-like divisions
            if display_name_parts[-2].isdigit():
                display_name_parts.pop(-2)
            display_name = ', '.join(
                [display_name_parts[0]] + display_name_parts[-2:])

        lat = data['lat']
        lon = data['lon']

        try:
            osm_id = data['osm_id']
        except KeyError:
            osm_id = ''
        return (lat, lon, display_name, osm_id, 'OSM/Nominatim')

    @staticmethod
    def _query_location(location):
        numbers = re.findall('[0-9]+', location)
        # return True if numbers else False
        if numbers:
            code = location.split(',', 1)[0]
            try:
                country = re.sub('[ ]', '', location.split(',', 1)[1])
            except IndexError:
                raise callbacks.Error('<postcode, country code>')
        return

    @wrap(['text'])
    def weather(self, irc, msg, args, location):
        """
        Get weather information for a town or city for the current day.

        [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] [latitude, longitude]

        I.E. `weather` Ballarat or Ballarat AU OR 3350, AU or `weather` -37.5303188, 143.8297033

         | `lookup` [city <(Alpha-2) country code>] to get latitude and longitude of a city/town.
        """
        location = location.lower()

        apikey = self.registryValue('openweatherAPI')
        # Missing API Key.
        if not apikey:
            raise callbacks.Error( \
                'Please configure the OpenWeatherMap API key in config plugins.Weather.openweatherAPI')

        # Not 'enabled' in #channel.
        if not self.registryValue('enable', msg.channel, irc.network):
            return

        log.info(f'Weather: running on {irc.network}/{msg.channel}')

        # Check for a postcode
        self._query_location(location)

        # Get details from OSM/Nominatim
        (latitude, longitude, location, id, text) = self.osm_geocode(location)

        # Get the weather data
        params = {
            'lat':     latitude,
            'lon':     longitude,
            'appid':   apikey,
            'units':   'metric',
            'exclude': 'minutely'
        }
        # Base URI for Openweathermap
        base_uri = ('http://api.openweathermap.org')
        url = f'{base_uri}/data/2.5/onecall?'

        try:
            Weather = requests.get(url, params, headers=headers)

            # If the response was successful, no Exception will be raised
            Weather.raise_for_status()
        except HTTPError as http_err:
            self.log.error(f'Weather: HTTP error occurred: {http_err}',
                    exc_info=True)
            raise callbacks.Error(f'Weather: HTTP error occurred: {http_err}')
        except Exception as err:
            self.log.error(f'Weather: an error occurred: {err}',
                    exc_info=True)
            raise callbacks.Error(f'Weather: an error occurred: {err}')
        else:
            weather = Weather.json()

            # Print weather details and forecast(s)
            irc.reply(self.format_weather_output(location, weather))

    @wrap(['text'])
    def lookup(self, irc, msg, args, location):
        """<location>"""
        location = location.lower()
        (lat, lon, display_name, osm_id, text) = self.osm_geocode(location)
        irc.reply(f'{text}: {display_name} [ID: {osm_id}] {lat},{lon}')

    @wrap(['something'])
    def help(self, irc):
        """418: I\'m a teapot"""

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
