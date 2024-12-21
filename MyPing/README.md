# An alternative to Supybots' PING function.

![Python versions](https://img.shields.io/badge/Python-version-blue) ![Supported Python versions](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11-blue.svg)


Returns the ping result of <hostname | ip or IPv6> using Python's shlex library.

## Configuring

* `config channel #channel plugins.MyPing.enable True or False` (On or Off)

## Setting up

To stop conflict with Supybots' core 'ping' function do the following:\
`[prefix] defaultplugin --remove ping Misc`\
`[prefix] defaultplugin ping MyPing`

## Using

[prefix/nick] ping [hostname | Nick | IPv4 or IPv6]

**Note:** [prefix] may be set via `config reply.whenAddressedBy.chars`
