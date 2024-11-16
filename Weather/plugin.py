###
# Copyright (c) 2024, Barry Suridge
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
import json, time
import math, re

from datetime import datetime
from functools import lru_cache #Simple lightweight unbounded function cache.
from supybot import utils, plugins, ircutils, callbacks, log
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weather')
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

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:110.0) Gecko/20100101 Firefox/110.0'
}
    
cache = dict()

def _contact_server_(uri):
    response = utils.web.getUrl(uri)

    return response

def find_numbers_and_text(s):
    # Find all numbers (integers and decimals)
    numbers = re.findall(r'\d+\.\d+|\d+', s)
    # Find all text (words)
    text = re.findall(r'[a-zA-Z]+', s)
    if numbers and text:
        return numbers, text
    else:
        return 0, 0
    
# Function based on: https://stackoverflow.com/questions/50225907/google-maps-api-geocoding-get-address-components/50236084#50236084
def extract_address_details(address_components):
    """
    extract_address_details extracts address parts from the details of the google maps api response

    :param address_components: a dict representing the details['address_components'] response from the google maps api
    :return: a dict of the address components
    """
    # set up the loop parameters for each component
    count = len(address_components)
    looplist = range(0, count)

    postal_code = '-1'
    city = ''

    #loop through the indices of the address components
    for i in looplist:

        #set up the loop parameters for the component types
        tcount = len(address_components[i]['types'])
        tlooplist = range(0, tcount)
        
        #loop through the indices of the address component types
        for t in tlooplist:

            #match the type, pull the short_name from the appropriate component as a string
            match address_components[i]['types'][t]:
                case 'postal_town':
                    city = str(address_components[i]['short_name'])
                case "locality":
                    city = str(address_components[i]['short_name'])
                case 'administrative_area_level_1':
                    political = str(address_components[i]['long_name'])
                case 'country':
                    country = str(address_components[i]['long_name'])
                case 'postal_code':
                    postal_code = str(address_components[i]['short_name'])

    # Assemble and format the data
    address = city + ', ' + political + ', ' + country

    # Return formatted data.
    return address, postal_code

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
@lru_cache(maxsize=64)    #XXX LRU caching
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
    using the OpenWeather and Google Maps API's   
    """
    threaded = True

    def __init__(self, irc):

        self.__parent = super(Weather, self)
        self.__parent.__init__(irc)

    def format_weather_output(self, location, data):
        """
        Gather all the data - format it
        """
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
        #day2        = data['daily'][2]
        #day2name    = datetime.fromtimestamp(day2['dt']).strftime('%A')
        #day2weather = day2['weather'][0].get('description')
        #day2highC   = round(day2['temp'].get('max'))
        #day2lowC    = round(day2['temp'].get('min'))

        # Formatted output
        a = f'🏠 {location} :: UTC {utc} :: Lat {LAT} Lon {LON} :: {staticon} {desc} '
        b = f'| 🌡 Barometric {atmos}hPa | Dew Point {dp}°C | ☁ Cloud cover {cloud}{percent_sign} '
        c = f'| {precipico} Precip {precip}mm/h | 💦 Humidity {humid}{percent_sign} | Current {colour(temp)} '
        d = f'| Feels like {colour(feelslike)} | 🍃 Wind {wind}Km/H {arrow} '
        e = f'| 💨 Gust {gust}m/s | 👁 Visibility {vis}Km | UVI {uvi} {uvicon} '
        #f = f'| {day1name}: {day1weather} Max {colour(day1highC)} Min {colour(day1lowC)} '
        #g = f'| {day2name}: {day2weather} Max {colour(day2highC)} Min {colour(day2lowC)}.'

        s = ''

        seq = [a, b, c, d, e]

        return((s.join(seq)))

    def _format_uvi_icon(self, uvi):
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

    @lru_cache(maxsize=64, typed=False)    #XXX LRU caching
    def google_maps(self, address, delay=3):
        address = address.lower()
        apikey = self.registryValue('googlemapsAPI')
        # Missing Google Maps API Key.
        if not apikey:
            raise callbacks.Error( \
                'Please configure the Google Maps API key via config plugins.Weather.googlemapsAPI [your_key_here]')
        # Adapted from James Lu's NuWeather plugin https://github.com/jlu5/
        #Base URI
        uri = 'https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'.format(utils.web.urlquote(address), apikey)
        self.log.debug('Weather: using url %s (google)', uri)    

        # Check if the URL is cashed
        if uri not in cache:
            cache[uri] = _contact_server_(uri)
    
        get = utils.web.getUrl(uri, headers=headers).decode('utf-8')

        data = json.loads(get, strict=False)
        if data['status'] != "OK":
            raise callbacks.Error("{0} from Google Maps for location {1}".format(data['status'], address))
    
        data         = data['results'][0]
        lat          = data['geometry']['location']['lat']
        lng          = data['geometry']['location']['lng']
        place_id     = data['place_id']

        display_name = ''

        # Extract data from 'address_components' section of Google Maps response.
        (display_name, postcode) = extract_address_details(data['address_components'])
          
        result = (display_name, lat, lng, postcode, place_id)
        
        # Delay
        time.sleep(delay) #in seconds

        return result

    # Adapted from https://stackoverflow.com/a/7490772
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

    @wrap(['text'])
    def google(self, irc, msg, args, location):
        """Looks up <location>
        
        [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] [latitude, longitude]
        <address>
        """
        location = location.lower()
     
        (display_name, lat, lng, postcode, place_id) = self.google_maps(location, delay=0)

        formatted_txt = '\x02%s\x02 \x02%s\x02 [ID: %s] \x02%s\x02 \x02%s' % (display_name, postcode, place_id, lat, lng)

        irc.reply(f'From Google Maps: {formatted_txt}')

    @wrap(['text'])
    def weather(self, irc, msg, args, location):
        """
        Get weather information for a town or city for the current day.

        [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] [latitude, longitude]

        I.E. `weather` Ballarat or Ballarat AU OR 3350 AU or `weather` -37.5303188, 143.8297033

         | `google` [city <(Alpha-2) country code>] to get latitude and longitude of a city/town.
        """
        # Not 'enabled' in #channel.
        if not self.registryValue('enable', msg.channel, irc.network):
            return

        apikey = self.registryValue('openweatherAPI')
        # Missing OpenWeatherMap API Key.
        if not apikey:
            raise callbacks.Error( \
                'Please configure the OpenWeatherMap API key via config plugins.Weather.openweatherAPI [your_key_here]')
                 
        location = location.lower()

        # Get co-ordinates from a postcode and send to Google Maps.
        (numbers, text) = find_numbers_and_text(location)
        if numbers and text:
           data = self.google_maps(location, delay=0)
        else: #Get location from Google Maps.
            data = self.google_maps(location, delay=0)
            if not data:
                raise callbacks.Error("Unknown location: %s." % location)
        
        # Google Maps results - formatted for readability
        results = {
            'address'  : data[0],
            'latitude' : data[1],
            'longitude': data[2],
            'postcode' : data[3]
        }

        # Base URI for Openweathermap
        uri = 'https://api.openweathermap.org/data/3.0/onecall?' + utils.web.urlencode({
            'lat':     results['latitude'],
            'lon':     results['longitude'],
            'appid':   apikey,
            'units':   'metric',
        })
        self.log.debug('Weather: using url %s (openweathermap)', uri)

        try:
            get = utils.web.getUrl(uri, headers=headers).decode('utf-8')
            data = json.loads(get, strict=False)
        except Exception as err:
            raise callbacks.Error(f'Weather: an error occurred: {err}')

        weather_output = self.format_weather_output(results['address'], data)

        irc.reply(f'{weather_output}')

    @wrap(['something'])
    def help(self, irc):
        """418: I\'m a teapot"""
                   
Class = Weather


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
