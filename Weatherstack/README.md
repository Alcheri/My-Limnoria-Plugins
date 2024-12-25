# WeatherStack

![Python versions](https://img.shields.io/badge/Python-version-blue) ![Supported Python versions](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11%2C%203.12%2C%203.13-blue.svg)

A plugin for Limnoria that uses the WeatherStack API. All output is in [Metric](https://www.bipm.org/en/).\
The weather output is for the current date in a location ONLY!\
This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

## Configuring

This plugin uses WeatherStack to get data. A free API key is required. Limited to 100 calls per month.\
Get an API key: [WeatherStack](https://weatherstack.com//)

This plugin uses positionstack to get data. A free API key is required. Limited to 100 Requests per month.\
Get an API key: [positionstack](https://positionstack.com/)

This plugin uses OpenWeatherMap as a fallback. A free API key is required.\
Get an API key: [OpenWeatherMap](https://openweathermap.org/api/)

## Setting up

* The following library is required. Run the command (below) from the Weatherstack folder to install.
* pgeocode: Python library for high performance off-line querying of GPS coordinates.

* `pip install --upgrade -r requirements.txt`

## Configure your bot

* /msg yourbot load Weatherstack
* /msg yourbot `config plugins.Weatherstack.weatherstackAPI  [Your_API_KEY]`
* /msg yourbot `config plugins.Weatherstack.positionstackAPI [Your_API_KEY]`
* /msg yourbot `config plugins.Weatherstack.openweatherAPI   [Your_API_KEY]`
* /msg yourbot `config channel #channel plugins.Weatherstack.enable True or False` (On or Off)
<br><br>
<p align="center">Copyright © MMXXIV, Barry Suridge</p>
