![Python versions](https://img.shields.io/badge/Python-version-blue) ![](https://img.shields.io/badge/3.6%2C%203.7%2C%203.8%2C%203.9%2C%203.10%2C%203.11-blue.svg)
# Weather

A plugin for Limnoria that uses the OpenWeather API. All output is in `Metric`.\
This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

Configuring:
===========

This plugin uses OpenWeather One Call 3.0 API to gather data requiring a (fee? )subscription.\
Subscription: [One Call API 3.0](https://openweathermap.org/api/one-call-3)

This plugin uses Google Maps API to gather data requiring a (free?) subscription.\
Subscription: [Google Maps API](https://developers.google.com/maps)

Setting up:
==========

* None required.

Configure your bot:
==================

* /msg yourbot load Weather
* /msg yourbot `config plugins.Weather.openweatherAPI [your_key_here]`
* /msg yourbot `config plugins.Weather.googlemapsAPI [your_key_here]`
* /msg yourbot `config channel #channel plugins.Weather.enable True or False` (On or Off)

Using:
=====

[prefix] weather [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] [latitude, longitude]\
[prefix] google&nbsp; [city <(Alpha-2) country code>] -- To get latitude and longitude of a city/town.


**Note:** [prefix] may be set via `config reply.whenAddressedBy.chars`
