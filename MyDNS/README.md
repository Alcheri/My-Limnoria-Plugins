# An alternative to Supybot's DNS function.

![Python versions](https://img.shields.io/badge/Python-version-blue) ![Supported Python versions](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11-blue.svg)

Returns the ip of <hostname | URL | nick | IPv4 or IPv6> or the reverse DNS hostname of \<ip\> using Python's socket library.

This plugin uses ipstack to get data. An API (free) key is required.\
Get an API key: [ipstack](https://ipstack.com/)

Unload the Internet plugin as it conflicts with this plugin:

## Configure your bot

* /msg yourbot load mydns
* /msg yourbot `config plugins.MyDNS.ipstackAPI [your_key_here]`
* /msg yourbot unload Internet
* /msg yourbot `config channel #channel plugins.MyDNS.enable True or False` (On or Off)

## Setting up

* This plugin uses Python's HTTP client. If not already installed run the following from the plugins/MyDNS folder.
* `pip install --upgrade -r requirements.txt`

Using

[prefix/nick] dns [hostname | URL | nick | IPv4 or IPv6]

**Note:** [prefix] may be set via `config reply.whenAddressedBy.chars`

## Example

`@dns crawl-203-208-60-1.googlebot.com`\
`DNS: crawl-203-208-60-1.googlebot.com resolves to [203.208.60.1] LOC: City:Beijing State:Beijing Long:116.37922668457031 Lat:39.91175842285156 Country Code:CN Country:China 🇨🇳 Post/Zip Code:100000`
