![Python versions](https://img.shields.io/badge/Python-version-blue) ![](https://img.shields.io/badge/3.6%2C%203.7%2C%203.8%2C%203.9-blue.svg)
# Weather

A plugin for Limnoria that uses the OpenWeather API. All output is in `Metric`.\
This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

Configuring:
===========

This plugin uses OpenWeather One Call API 3.0 to gather data requiring a subscription.\
Subscription: [One Call API 3.0](https://openweathermap.org/api/one-call-3)

Setting up:
==========

* None required.

Configure your bot:
==================

* /msg yourbot load Weather
* /msg yourbot `config plugins.Weather.openweatherAPI [your_key_here]`
* /msg yourbot `config channel #channel plugins.Weather.enable True or False` (On or Off)

Using:
=====

[prefix] weather [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] [latitude, longitude]\
[prefix] lookup&nbsp; [city <(Alpha-2) country code>] -- To get latitude and longitude of a city/town.


**Note:** [prefix] may be set via `config reply.whenAddressedBy.chars`
