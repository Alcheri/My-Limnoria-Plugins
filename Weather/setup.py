###
# Copyright (c) 2024, Barry Suridge
# All rights reserved.
#
#
###

from supybot.setup import plugin_setup

plugin_setup(
    'Weather',
    install_requires=[
        'asyncio',
        'aiohttp',
  ]
)
