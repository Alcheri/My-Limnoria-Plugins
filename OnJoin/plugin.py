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

import random
import os.path

import supybot.ircutils as utils
import supybot.callbacks as callbacks


class OnJoin(callbacks.Plugin):  # pylint: disable=too-many-ancestors
    """Send a notice to all users entering a channel."""

    public = False

    def __init__(self, irc):
        self.__parent = super().__init__(irc)

    def doJoin(self, irc, msg):
        """Send a random notice to a user
        when they enter the channel."""

        channel = msg.args[0]

        # Check if in a channel and see if we should be 'disabled' in it.
        # config channel #channel plugins.onjoin.enable True or False (or On or Off)
        if self.registryValue("enable", channel):
            p = os.path.abspath(os.path.dirname(__file__))
            p = p + "/quotes.txt"
            fp = str(p)
            line_num = 0
            selected_line = ""
            try:
                with open(fp) as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line_num += 1
                        if random.uniform(0, line_num) < 1:
                            selected_line = line
                # It's not the bot.
                if utils.strEqual(irc.nick, msg.nick) is False:
                    irc.reply(
                        self._teal(selected_line.strip()),
                        notice=True,
                        private=True,
                        to=msg.nick,
                    )
                else:
                    pass
            except IOError as err:
                # Non-fatal error traceback information
                raise FileError(f"{err}: failed to open")
        else:
            return

    def _teal(self, string):
        """Return a teal coloured string."""
        return utils.bold(utils.mircColor(string, "teal"))


class FileError(Exception):
    """Non-fatal error traceback."""

    pass


Class = OnJoin


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
