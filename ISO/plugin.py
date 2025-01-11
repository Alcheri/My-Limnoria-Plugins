###
# Copyright (c) 2021, Barry KW Suridge
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

from supybot import callbacks
from supybot.commands import *

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("ISO")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

try:
    from iso3166 import countries
except Exception as ie:
    raise Exception(f"Cannot import module: {ie}")


class ISO(callbacks.Plugin):
    """Convert alpha2 country codes to country name."""

    threaded = True

    @wrap(["text"])
    def country(self, irc, msg, args, code):
        """ "
        Convert alpha2 country codes to country name.
        Convert country name to alpha2 country codes.
        """

        code = code.lower()
        try:
            country = countries.get(code)
            name = country[0]
            alpha2 = country[1]
        except KeyError as error:
            raise callbacks.Error(f"{error} unknown country code.")
        irc.reply(f"{alpha2} {name}", prefixNick=False)


Class = ISO


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
