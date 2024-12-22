###
# Copyright (c) 2024, Barry Suridge
# All rights reserved.
#
#
###

from supybot import utils, plugins, ircutils, callbacks, log
from supybot.commands import *
from supybot.i18n import PluginInternationalization


_ = PluginInternationalization('Dictionary')

import json

from builtins import dict  # Ensure the built-in dict is used

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:110.0) Gecko/20100101 Firefox/110.0'
}

class Dictionary(callbacks.Plugin):
    """An English dictionary plugin."""
    threaded = True

    def __init__(self, irc):
        super().__init__(irc)
    
    @wrap(['text'])
    def dict(self, irc, msg, args, input):
        """<word>
        Gives the meaning of the word.
        """
        input = input.lower()
        base_url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{input}'
    
        try:
            # Fetch data from the API
            raw_response = utils.web.getUrl(base_url, headers=headers).decode('utf-8')
            data = json.loads(raw_response, strict=False)
        
            if not isinstance(data, list):  # Valid check
                irc.error("No definitions found for the given word.")
                return

            first_element = data[0]

            if not isinstance(first_element, dict):  # Valid check
                irc.error("Unexpected response format from the API.")
                return

            try:
                meaning = first_element['meanings'][0]
                definition = meaning['definitions'][0]['definition']
                part_of_speech = meaning['partOfSpeech']
                response = f"{input} ({part_of_speech}): {definition}"
                irc.reply(response, prefixNick=False)
            except (KeyError, IndexError) as e:
                irc.error(f"Error extracting definition: {e}", prefixNick=False)
        except json.JSONDecodeError:
            irc.error("Failed to parse the API's JSON response.", prefixNick=False)
        except utils.web.Error as e:
            irc.error(f"An error occurred while contacting the API: {e}", prefixNick=False)
        except Exception as e:
            irc.error(f"An unexpected error occurred: {e}", prefixNick=False)


Class = Dictionary


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
