# An alternative to Limnorias' PING function.

![Python versions](https://img.shields.io/badge/Python-version-blue) ![Supported Python versions](https://img.shields.io/badge/3.9%2C%203.10%2C%203.11%2C%203.12%2C%203.13-blue.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black) ![Build Status](https://github.com/Alcheri/My-Limnoria-Plugins/blob/master/img/status.svg) ![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg) [![CodeQL](https://github.com/Alcheri/Weather/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Alcheri/Weather/actions/workflows/github-code-scanning/codeql)

Returns the ping result of <hostname | ip or IPv6> using Python's shlex library.

## Install

Download the plugin:

```plaintext
https://github.com/Alcheri/My-Limnoria-Plugins/tree/master/MyPing
```

Next, load the plugin:

```plaintext
/msg bot load MyPing
```

## Configuring

* **_config channel #channel plugins.MyPing.enable True or False` (On or Off_**

## Setting up

To stop conflict with Limnorias' core 'ping' function do the following:\

\<Barry\> defaultplugin --remove ping Misc\
\<Borg\> defaultplugin ping MyPing

## Using
<!-- LaTeX text formatting (colour) -->
\<Barry\> @ping Mini-Me\
\<Borg\>  ${\texttt{\color{red}its.all.good.in.bazzas.club}}$ is Reachable ~ Time elapsed: ${\texttt{\color{teal}(0.0, 0.0)}}$ seconds/milliseconds Packet Loss: ${\texttt{\color{teal}0%}}$

\<Barry\> @ping 167.88.114.11\
\<Borg\>  ${\texttt{\color{red}167.88.114.11}}$ is Reachable ~ Time elapsed: ${\texttt{\color{teal}(0.0, 362.0)}}$ seconds/milliseconds Packet Loss: ${\texttt{\color{teal}0%}}$

\<Barry\> @ping 2a01:4f9:c011:33a2::20\
\<Borg\>  ${\texttt{\color{red}2a01:4f9:c011:33a2::20}}$ is Reachable ~ Time elapsed: ${\texttt{\color{teal}(0.0, 167.0)}}$ seconds/milliseconds Packet Loss: ${\texttt{\color{teal}0%}}$

<br><br>
<p align="center">Copyright © MMXXV, Barry Suridge</p>
