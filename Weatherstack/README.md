# WeatherStack

![Python versions](https://img.shields.io/badge/Python-version-blue) ![Supported Python versions](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11%2C%203.12%2C%203.13-blue.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black) ![Build Status](https://github.com/Alcheri/My-Limnoria-Plugins/blob/master/img/status.svg) ![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg) [![CodeQL](https://github.com/Alcheri/Weather/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Alcheri/Weather/actions/workflows/github-code-scanning/codeql)\

A plugin for Limnoria that uses the WeatherStack API. All output is in [Metric](https://www.bipm.org/en/).

The weather output is for the current date in a location ONLY!

This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

## Setting up

This plugin uses WeatherStack to get data. A free API key is required. Limited to 100 calls per month.\
Get an API key: [WeatherStack](https://weatherstack.com//)

This plugin uses positionstack to get data. A free API key is required. Limited to 100 Requests per month.\
Get an API key: [positionstack](https://positionstack.com/)

This plugin uses OpenWeatherMap as a fallback. A free API key is required.\
Get an API key: [OpenWeatherMap](https://openweathermap.org/api/)

## Install

Download the plugin:

```plaintext
https://github.com/Alcheri/My-Limnoria-Plugins/tree/master/Weatherstack
```

To install additional requirements, run from /plugins/Weatherstack folder:

```plaintext
pip install --upgrade -r requirements.txt 
```

Next, load the plugin:

```plaintext
/msg bot load Weatherstack
```

## Configure your bot

* **_config plugins.Weatherstack.weatherstackAPI  [Your_API_KEY]_**
* **_config plugins.Weatherstack.positionstackAPI [Your_API_KEY]_**
* **_config plugins.Weatherstack.openweatherAPI   [Your_API_KEY]_**

    Enable in #channel? Default: False

* **_config channel #channel plugins.Weatherstack.enabled True or False` (On or Off)_**

## Using

<!-- LaTeX text formatting (colour) -->
>\<Barry\> @weather 3355, au\
>\<Borg\>  Ballarat, Victoria, Australia | Lat: 37°34' 1.2" S, Lon: 143°51' 0.0" E | 08-01-2025 12:05 | Sunny, Humidity 33%, Precip: 0 mm/h, Temp: ${\texttt{\color{yellow}27.0°C}}$, Feels like: ${\texttt{\color{yellow}26.0°C}}$, Wind: 12 Km/h N, ${\texttt{\color{purple}UVI 11 (Extreme)}}$
>
>\<Barry\> @weather Ballarat, AU\
>\<Borg\>  Ballarat, Victoria, Australia | Lat: 37°34' 1.2" S, Lon: 143°51' 0.0" E | 08-01-2025 12:53 | Sunny, Humidity 33%, Precip: 0 mm/h, Temp: ${\texttt{\color{yellow}27.0°C}}$, Feels like: ${\texttt{\color{yellow}26.0°C}}$, Wind: 12 Km/h N, ${\texttt{\color{purple}UVI 11 (Extreme)}}$

<br><br>
<p align="center">Copyright © MMXXIV, Barry Suridge</p>
