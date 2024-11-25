![Python versions](https://img.shields.io/badge/Python-version-blue) ![](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11-blue.svg)
# Weather

A plugin for Limnoria that uses the OpenWeather and Google Maps API's. All output is in `Metric`.\
This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

Setting up:
==========

OpenWeather One Call 3.0 API gathers data requiring a (free? )subscription.\
Subscription: [One Call API 3.0](https://openweathermap.org/api/one-call-3)

Google Maps API gathers data requiring a (free?) subscription.\
Subscription: [Google Maps API](https://developers.google.com/maps)

**Google** gives each Google Maps account $200/month of free credit, equivalent to 40,000 addresses geocoded per month.

Configure your bot:
==================

* /msg yourbot load Weather
* /msg yourbot `config plugins.Weather.openweatherAPI [your_key_here]`
* /msg yourbot `config plugins.Weather.googlemapsAPI [your_key_here]`
* /msg yourbot `config channel #channel plugins.Weather.enable True or False` (On or Off)

**Note:** [prefix] may be set via `config reply.whenAddressedBy.chars`

Using:
=====

[prefix] weather [city <(Alpha-2) country code>] [<postcode, (Alpha-2) country code>] \<address\>\
[prefix] google&nbsp; [city <(Alpha-2) country code>] [latitude, longitude] -- To get latitude and longitude of a city/town.\
[prefix] set&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\<location\> -- Sets the location for your current ident@host to \<location\>\
[prefix] help -- Plugin help. Accepts no arguments.



