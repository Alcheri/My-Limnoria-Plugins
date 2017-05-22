# pylint: disable=missing-docstring
# pylint: disable=unused-argument
# pylint: disable=invalid-name

###
# Copyright (c) 2016 - 2017, Barry Suridge
# All rights reserved.
#
###
from __future__ import division

# My plugins
import re  # Regular expression operators.
import traceback  # Error traceback
# For Python 3.0 and later
from contextlib import closing  # Utilities for common tasks involving the with statement.
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urlencode
from urllib.error import URLError
import os  # Operating system dependent functionality.
from io import BytesIO  # Images
import math  # Mathematical functions.
from bs4 import BeautifulSoup  # Library for pulling data out of HTML and XML files
import requests  # HTTP library

import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Titlerz')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

# Text colour formatting library
from .local import color
#  Python 3
try:
    from PIL import Image  # Pillow
except ImportError as err:
    raise Exception('ERROR. I did not find PIL installed. I cannot process images w/o this. [%s]', err)

try:
    import magic  # Magic
except ImportError as err:
    raise Exception('ERROR. I did not find Magic installed. I cannot process images w/o this. [%s]', err)

    ###############
    #  FUNCTIONS  #
    ###############

def _cleantitle(msg):
    """Clean up the title of a URL."""

    cleaned = msg.translate(dict.fromkeys(range(32))).strip()
    return re.sub(r'\s+', ' ', cleaned)

def _cleandesc(desc):
    """Tidies up description string."""

    desc = desc.replace('\n', '').replace('\r', '')
    return desc

# Function to convert bytes to Kb, Mb %c
def _bytesto(bytes, to, bsize=1024):
    """Convert bytes to megabytes, etc.
        sample code:
            print('mb= ' + str(_bytesto(314575262000000, 'm')))
        sample output:
            mb= 300002347.946
    """

    a = {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5, 'e': 6}
    r = float(bytes)
    for i in range(a[to]):
        r = r // bsize

    return math.ceil(float(r))

# Expand shortened link
def _longurl(url):
    """Expand shortened URLs."""
    session = requests.Session()  # so connections are recycled
    resp = session.head(url, allow_redirects=True)
    return resp.url

def _getsoup(url):
    """Get web page."""
    req = Request(url)
    # Set language for page
    req.add_header('Accept-Language', 'en-us,en;q=0.5')
    response = urlopen(req, timeout=4)
    page = response.read()
    # Close open file
    response.close()
    soup = BeautifulSoup(page, 'lxml')
    return soup

    ##############
    #    MAIN    #
    ##############

class Titlerz(callbacks.Plugin):  # pylint: disable=too-many-ancestors
    """Titlerz plugin."""

    def __init__(self, irc):
        self.__parent = super().__init__(irc)

        """
        List of domains of known URL shortening services.
        """
        self.shortUrlServices = [
            'adf.ly',
            'bit.do',
            'bit.ly',
            'bitly.com',
            'budurl.com',
            'cli.gs',
            'fa.by',
            'goo.gl',
            'is.gd',
            'j.mp',
            'lurl.no',
            'lnkd.in',
            'moourl.com',
            'ow.ly',
            'smallr.com',
            'snipr.com',
            'snipurl.com',
            'snurl.com',
            'su.pr',
            't.co',
            'tiny.cc',
            'tr.im',
            'tinyurl.com']

    #########################
    # HTTP HELPER FUNCTIONS #
    #########################

    def _openurl(self, url):
        """Generic http fetcher.
           Links/errors are handled here and passed on.
        """

        # Check for MIME type extensions.
        badexts = ['.bmp', '.flv', '.m3u8']
        if __builtins__['any'](url.endswith(x) for x in badexts):
            path = urlparse(url).path
            ext = os.path.splitext(path)[1]
            return "ERROR. Bad extension '%s'" % ext

        # Requests: HTTP for Humans
        req = Request(url)
        # try/except block with error handling.
        try:
            res = urlopen(req, timeout=4)
        except URLError as err:
            if hasattr(err, 'reason'):
                return 'We failed to reach a server. Reason: %s' % err.reason
            elif hasattr(err, 'code'):
                return 'The server couldn\'t fulfill the request: %s' % err.code
        response = res.info()
        res.close()
        if response['content-type'].startswith('audio/') or response['content-type'].startswith('video/'):
            pass
        if response['content-type'].startswith('image/'):
            o = self._getimg(url, response['content-length'])
        elif response['content-type'].startswith('text/'):
            try:
                o = self._gettitle(url)
            except Exception as err:  # pylint: disable=broad-except
                # Non-fatal error traceback information
                self.log.info(traceback.format_exc())
                return 'Error: %s' % err
        else:
            # handle any other filetype using libmagic.
            o = self._filetype(url)
        return o

    def _gettitle(self, url, gd=True, o=None):
        """Generic title fetcher for non-domain-specific titles."""

        desc     = None
        shorturl = None
        longurl  = None

        self.log.info('_gettitle: Trying to open: %s', url)

        soup = _getsoup(url)
        if soup.title is not None:
            title = _cleantitle(soup.title.string)
        else:
            title = None
        # List of domains to not allow displaying of web page descriptions.
        baddomains = ['twitter.com', 'panoramio.com', 'facebook.com', 'kickass.to', 'dailymotion.com',
                      'tinypic.com', 'ebay.com', 'imgur.com', 'dropbox.com']
        urlhostname = urlparse(url).hostname
        if __builtins__['any'](b in urlhostname for b in baddomains):
            gd = False
        # Should we "get description" (GD)?
        if gd:
            # Yes!
            des = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
            if des and des.get('content'):
                desc = _cleandesc(des['content'].strip())
        if title:
            if __builtins__['any'](s in urlhostname for s in self.shortUrlServices):
                longurl = _longurl(url)
            else:
                request_url = ('http://tinyurl.com/api-create.php?' + urlencode({'url': url}))
                with closing(urlopen(request_url)) as response:
                    shorturl = response.read().decode('utf-8')
            o = "%s - (%s)" % (title, longurl if not shorturl else shorturl)
        else:
            o = None
        if desc:
            return {'title': o, 'desc': desc}
        return o

    # Check for other filetypes using libmagic
    def _filetype(self, url):
        """Check for unknown filetypes using libmagic."""

        response = requests.get(url, timeout=4)
        response.close()
        try:
            size = len(response.content)
            typeoffile = magic.from_buffer(response.content)
            return 'Content type: %s - Size: %s' % (typeoffile, str(_bytesto(size, 'k')))
        except Exception as err:  # pylint: disable=broad-except
            self.log.error('Error: _filetype: error trying to parse %s via other (else) :: %s', url, err)
            self.log.error('ERROR: _filetype: no handler for %s at %s', response.headers['content-type'], url)
            return None

    # Process image data from supplied URL.
    def _getimg(self, url, size):
        """Displays image information in channel"""

        self.log.info('_getimg: Trying to open: %s', url)

        response = requests.get(url, timeout=4)
        response.close()

        try:  # try/except because images can be corrupt.
            img = Image.open(BytesIO(response.content))
            img.verify()  # verify that it is, in fact an image
            img = Image.open(BytesIO(response.content))
        except (IOError, SyntaxError) as err:
            return 'ERROR: %s is an invalid image I cannot read. [%s]' % (url, err)
        width, height = img.size
        if img.format == 'GIF':  # check to see if animated.
            try:
                img.seek(1)
                img.seek(0)
                img.format = 'Animated GIF'
            except EOFError:
                pass

        return 'Image type: %s  Dimensions: %sx%s  Mode: %s  Size: %sKb' % \
                    (img.format, width, height, img.mode, str(_bytesto(size, 'k')))

    ############################################
    # MAIN TRIGGER FOR URLS PASTED IN CHANNELS #
    ############################################

    def doPrivmsg(self, irc, msg):
        """Monitor channel for URLs"""

        channel = msg.args[0]  # channel, if any.

        # Check if we should be 'disabled' in this channel.
        # config channel #channel plugins.titlerz.enable True or False (or On or Off)
        if not self.registryValue('enable', channel):
            return
        # don't react to non-ACTION based messages.
        if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
            return
        if irc.isChannel(channel):     # must be in channel.
            if ircmsgs.isAction(msg):  # if in action, remove.
                text = ircmsgs.unAction(msg)
            else:
                text = msg.args[1]
            for url in utils.web.urlRe.findall(text):
                output = self._openurl(url)
                # now, with gd, we must check what output is.
                if output:  # if we did not get None back.
                    if isinstance(output, dict):  # we have a dict.
                        # output.
                        if 'desc' in output and 'title' in output and output['desc'] is not None and output['title'] is not None:
                            irc.sendMsg(ircmsgs.privmsg(channel, color.bold(color.teal('TITLE: ')) + output['title']))
                            irc.sendMsg(ircmsgs.privmsg(channel, color.bold(color.teal('DESC : ')) + output['desc']))
                        elif 'title' in output and output['title'] is not None:
                            irc.sendMsg(ircmsgs.privmsg(channel, color.bold(color.teal('TITLE: ')) + output['title']))
                    else:  # no desc.
                        irc.sendMsg(ircmsgs.privmsg(channel, color.bold(color.italic(('Response: '))) + output))

    def titler(self, irc, msg, args, opturl):
        """<url>

        Public test function for Titler.
        Ex: http://www.google.com
        """

        # main.
        output = self._openurl(opturl)
        # now, with gd, we must check what output is.
        if output:  # if we did not get None back.
            if isinstance(output, dict):  # we have a dict.
                if 'title' in output:  # we got a title back.
                    irc.reply(color.bold('TITLE: ') + output['title'])
                    if 'desc' in output:
                        irc.reply(color.bold('GD: ') + output['desc'])
            else:
                irc.reply('%s' % output)

    titler = wrap(titler, [('text')])

Class = Titlerz

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
