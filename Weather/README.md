# Weather

![Python versions](https://img.shields.io/badge/Python-version-blue) ![Supported Python versions](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11%2C%203.12-blue.svg) ![Build Status](../img/status.svg) ![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)

A fully asynchronous Weather plugin for Limnoria using the OpenWeather and Google Maps APIs.

All output is in [Metric](https://www.bipm.org/en/)

This plugin uses Alpha-2 Code for country code [iso.org](https://www.iso.org/obp/ui#iso:pub:PUB500001:en)

## Setting up

OpenWeather One Call 3.0 API gathers data requiring a (free? )subscription.\
Subscription: [One Call API 3.0](https://openweathermap.org/api/one-call-3)

Google Maps API gathers data requiring a (free?) subscription.\
Subscription: [Google Maps API](https://developers.google.com/maps)

**Google** gives each Google Maps account $200/month of free credit, equivalent to 40,000 addresses geocoded per month.

## Install

Go into your Limnoria plugin dir, usually ~/runbot/plugins and run:

```plaintext
git clone https://github.com/Alcheri/My-Limnoria-Plugins.git
```

To install additional requirements, run from /plugins/Weather folder:

```plaintext
pip install --upgrade -r requirements.txt 
```

Next, load the plugin:

```plaintext
/msg bot load Weather
```

## Configure your bot

* **_config plugins.Weather.openweatherAPI [your_key_here]_**
* **_config plugins.Weather.googlemapsAPI [your_key_here]_**
* **_config channel #channel plugins.Weather.enable True or False (On or Off)_**

**Note:** For all Southern Hemisphere latitudes prefix the argument with '--' i.e.:
<pre>   -- -37.5621587 143.8502556</pre>

## Using

```plaintext
<Barry> @weather 1600 Amphitheatre Pkwy, Mountain View, CA
<Borg>  1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA (Lat: 122°5' 4.92" W, Lon: 37°25' 21.0" N) | Clear sky, Temp: 8.0°C, Feels like: 6.0°C, Humidity: 91%, Clouds: 0%, Wind: 7 Km/h NW, UVI 0 (Low)

<Barry> @weather -- -37.5621587 143.8502556
<Borg>  Ballarat Central VIC 3350, Australia (Lat: 143°51' 1.08" E, Lon: 37°33' 43.92" S) | Clear sky, Temp: 10.0°C, Feels like: 10.0°C, Humidity: 99%, Clouds: 9%, Wind: 5 Km/h SSE, UVI 0 (Low)

<Barry> @google -37.5283674, 143.8164991
<Borg>  From Google Maps: 1275 Grevillea Rd, Wendouree VIC 3355, Australia 3355 [ID: ChIJcSzC6YxD0WoRWtgRRJh8D2U] -37.5283674 143.8164991

<Barry> @google Ballarat VIC AU
<Borg>  From Google Maps: Ballarat VIC, Australia N/A [ID: ChIJeRiTMFRE0WoRILegMKR5BQQ] -37.5621587 143.8502556

@weather set [location] -- Sets your current ident@host to [location]

@weather help -- Plugin help - accepts no arguments.
```
<br/><br/>
<p align="center">Copyright © MMXXIV, Barry Suridge</p>
