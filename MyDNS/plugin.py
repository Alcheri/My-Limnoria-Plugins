###
# Copyright (c) 2016 - 2021, Barry Suridge
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

import json    # JavaScript Object Notation
import socket  # Low-level networking interface

#XXX For Python 3.4 and later
# HTTP client for Python
try:
    import urllib3
except ImportError as e:
    raise Exception(f'Cannot import module: {e}')

from urllib3.exceptions import HTTPError

# URL handling module for python
from urllib.parse import urlparse

# Validate and categorize the IP address according to their types
# (IPv4 or IPv6)
import ipaddress

# mIRC colour codes
from .local.colour import bold, teal

from supybot.commands import *
from supybot import callbacks
import supybot.ircutils as utils

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('MyDNS')
except ImportError:
    _ = lambda x: x

    ###############
    #  FUNCTIONS  #
    ###############

#XXX https://datatracker.ietf.org/doc/html/rfc2812#section-2.3.1
special_chars = (
    '-',
    '[',
    ']',
    '\\',
    '`',
    '^',
    '{',
    '}',
    '_')

def is_nick(nick):
    """ Checks to see if a nickname `nick` is valid.
    According to :rfc:`2812 #section-2.3.1`, section 2.3.1, a nickname must start
    with either a letter or one of the allowed special characters, and after
    that it may consist of any combination of letters, numbers, or allowed
    special characters.
    """
    if not nick[0].isalpha() and nick[0] not in special_chars:
        return False
    for char in nick[1:]:
        if not char.isalnum() and char not in special_chars:
            return False
    return True

def is_ip(s):
    """Returns whether or not a given string is a
       valid IPv4 or IPv6 address.
    """
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False

class MyDNS(callbacks.Plugin):
    """An alternative to Supybot's DNS function.
    """

    def __init__(self, irc):
        super().__init__(irc)

    threaded = True

    ##############
    #    MAIN    #
    ##############

    @wrap(['text'])
    def dns(self, irc, msg, args, address):
        """<hostname | Nick | URL | IPv4 or IPv6>
        An alternative to Supybot's DNS function.
        Returns the ip of <hostname | Nick | URL | ip or IPv6> or the reverse
        DNS hostname of <ip> using Python's socket library
        """
        # Check if we should be 'enabled' in a channel.
        # config channel #channel supybot.plugins.MyDNS.enable True or False (On or Off)
        if not self.registryValue('enable', msg.channel, irc.network):
            return

        self.log.info('MyDNS: running on %s/%s', irc.network, msg.channel)

        if is_ip(address):
            irc.reply(self.gethostbyaddr(address), prefixNick=False)
        elif is_nick(address):  # Valid nick?
            nick = address
            try:
                userHostmask = irc.state.nickToHostmask(nick)
                (nick, _, host) = utils.splitHostmask(userHostmask)  # Returns the nick and host of a user hostmask.
                irc.reply(self.gethostbyaddr(host), prefixNick=False)
            except KeyError:
                irc.reply(f"[{nick}] is unknown.", prefixNick=False)
        else:  # Neither IP or IRC user nick.
            irc.reply(self.getaddrinfo(address), prefixNick=False)

    def getaddrinfo(self, host):
        """Get host information. Use returned IP address
        to find the (approximate) geolocation of the host.
        """
        host = host.lower()
        d = urlparse(host)

        if d.scheme:
            host = d.netloc

        try:
            result = socket.getaddrinfo(host, None)
        except socket.error as err:  # Catch failed address lookup.
            self.log.error('MyDNS: Could not resolve  %s: %s', host, err)
            return (f'Could not resolve {host}: {err}')

        ipaddress = result[0][4][0]
        geoip = self.geoip(ipaddress)

        dns = bold(teal('DNS: '))
        loc = bold(teal('LOC: '))

        return (f'{dns}{host} resolves to [{ipaddress}] {loc}{geoip}')

    def gethostbyaddr(self, ip):
        """Do a reverse lookup for ip.
        """
        try:
            (hostname, _, address) = socket.gethostbyaddr(ip)
            hostname = hostname + ' <> ' + address[0]
            geoip = self.geoip(address[0])
            shortname = hostname.split('.')[0]
            dns = bold(teal('DNS: '))
            loc = bold(teal('LOC: '))
            return (f'{dns} <{shortname}> [{hostname}] {loc} {geoip}')
        except socket.error as err:  # Catch failed address lookup.
            self.log.error('MyDNS: Could not resolve  %s: %s', ip, err)
            return (f'Could not resolve {ip}: {err}')

    def geoip(self, address):
        """Search for the geolocation of IP addresses.
        Accuracy not guaranteed.
        """
        apikey = self.registryValue('ipstackAPI')

        if not apikey:
            raise callbacks.Error( \
                'Please configure the ipstack API key in config plugins.MyDNS.ipstackAPI')

        # Creating a PoolManager instance for sending requests.
        http = urllib3.PoolManager()

        # Set the URI
        uri = 'http://api.ipstack.com/' + address + '?access_key=' + apikey

        # Sending a GET request and getting back response as HTTPResponse object
        response = http.request("GET", uri, timeout=1)

        # 'OK', 'Request fulfilled, document follows'
        if response.status != 200:
            raise HTTPError(
                'Request failed with status {0}'.format(response.status),
            )
        else:
            data = json.loads(response.data.decode("utf-8"))

        city    = 'City:%s ' % data['city'] if data['city'] else ''
        state   = 'State:%s ' % data['region_name'] if data['region_name'] else ''
        long    = 'Long:%s ' % data['longitude'] if data['longitude'] else ''
        lat     = 'Lat:%s ' % data['latitude'] if data['latitude'] else ''
        code    = 'Country Code:%s ' % data['country_code'] if data['country_code'] else ''
        country = 'Country:%s ' % data['country_name'] if data['country_name'] else ''
        flag    = data['location']['country_flag_emoji']
        zip     = ' Post/Zip Code:%s' % data['zip'] if data['zip'] else ''

        try:
            s = ''
            seq = [city, state, long, lat, code, country, flag, zip]
            return (s.join( seq ))
        except TypeError:
            self.log.error('MyDNS: Could not resolve %s', address)
            raise callbacks.Error(f'Could not resolve {address}')

Class = MyDNS

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
