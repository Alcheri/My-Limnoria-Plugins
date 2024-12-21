# WeatherStack

![Python versions](https://img.shields.io/badge/Python-version-blue) ![](https://img.shields.io/badge/3.6%2C%203.7%2C%203.8%2C%203.9-blue.svg)

A plugin for Limnoria that uses the WeatherStack API. All output is in Metric.\
The weather output is for the current date in a location ONLY!\
This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

## Configuring

This plugin uses WeatherStack to get data. A free API key is required.
Get an API key: [WeatherStack](https://weatherstack.com//)

This plugin uses positionstack to get data. A free API key is required.
Get an API key: [positionstack](https://positionstack.com/)

## Setting up

* The following libraries are required. Run the command (below) from the Weatherstack folder to install.
* pgeocode: Python library for high performance off-line querying of GPS coordinates.
* ephem: Python package for performing high-precision astronomy computations.
* `pip3 install -r requirements.txt`

## Configure your bot

* /msg yourbot load Weatherstack
* /msg yourbot `config plugins.Weatherstack.weatherstackAPI 99024af53ccea7605e269764abe7d557`
* /msg yourbot `config plugins.Weatherstack.positionstackAPI e7226bdca330b77866a4f90fb7af824b`
* /msg yourbot `config channel #channel plugins.Weatherstack.enable True or False` (On or Off)