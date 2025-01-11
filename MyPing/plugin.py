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

###
import shlex
import subprocess

###
from supybot.commands import *
import supybot.ircutils as utils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("MyPing")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x
from .local.colour import red, teal

###############
#  FUNCTIONS  #
###############

special_chars = ("-", "[", "]", "\\", "`", "^", "{", "}", "_")


def is_nick(nick):
    """Checks to see if a nickname `nick` is valid.
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


def _elapsed_loss(loss):
    """
    :rtype: dict or None
    """
    lines = loss.split("\n")
    loss = lines[-2].split(",")[2].split()[0]
    timing = lines[-1].split()[3].split("/")
    elapsed = int(float(timing[1]))
    time = divmod(elapsed, 1000.0)

    return f"Time elapsed: {teal(time)} seconds/milliseconds Packet Loss: {teal(loss)}"


class MyPing(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(MyPing, self)
        self.__parent.__init__(irc)

    threaded = True

    @wrap(["something"])
    def ping(self, irc, msg, args, host):
        """<hostmask> | Nick | IPv4 or IPv6>
        An alternative to Supybot's PING function.
        """
        channel = msg.args[0]

        # Check if we should be 'disabled' in a channel.
        # config channel #channel plugins.myping.enable True or False (or On or Off)
        if not self.registryValue("enable", channel):
            return
        if is_nick(host):  # Valid nick?
            nick = host
            try:
                userHostmask = irc.state.nickToHostmask(nick)
                # Returns the nick and host of a user hostmask.
                (nick, _, host) = utils.splitHostmask(userHostmask)
            except KeyError:
                pass
        cmd = shlex.split(f"ping -c 1 -W 1 {host}")
        try:
            reply = subprocess.check_output(cmd).decode().strip()
            elapsed_loss = _elapsed_loss(reply)
        except subprocess.CalledProcessError:
            # Will print the command failed
            irc.reply(f"{red(cmd[-1])} is Not Reachable", prefixNick=False)
        else:
            irc.reply(f"{red(cmd[-1])} is Reachable ~ {elapsed_loss}", prefixNick=False)


Class = MyPing
