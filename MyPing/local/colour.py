##############
# FORMATTING #
##############

## mIRC colour codes
#
# Number 	Name
# 00 	    white
# 01 	    black
# 02 	    blue (navy)
# 03 	    green
# 04 	    red
# 05 	    brown (maroon)
# 06 	    purple
# 07 	    orange (olive)
# 08 	    yellow
# 09 	    light green (lime)
# 10 	    teal (a green/blue cyan)
# 11 	    light cyan (cyan / aqua)
# 12 	    light blue (royal)
# 13 	    pink (light purple / fuchsia)
# 14 	    grey/gray
# 15 	    light grey/gray (silver)

import supybot.ircutils as utils


def white(s):
    """Returns a white string."""
    return utils.mircColor(s, "white")


def black(s):
    """Returns a black string."""
    return utils.mircColor(s, "black")


def blue(s):
    """Returns a blue string."""
    return utils.mircColor(s, "blue")


def green(s):
    """Returns a green string."""
    return utils.mircColor(s, "green")


def red(s):
    """Returns a red string."""
    return utils.mircColor(s, "red")


def brown(s):
    """Returns a brown string."""
    return utils.mircColor(s, "brown")


def purple(s):
    """Returns a purple string."""
    return utils.mircColor(s, "purple")


def orange(s):
    """Returns a orange string."""
    return utils.mircColor(s, "orange")


def yellow(s):
    """Returns a yellow string."""
    return utils.mircColor(s, "yellow")


def light_green(s):
    """Returns a light green string."""
    return utils.mircColor(s, "light green")


def teal(s):
    """Returns a teal string."""
    return utils.mircColor(s, "teal")


def light_blue(s):
    """Returns a teal string."""
    return utils.mircColor(s, "blue")


def dark_blue(s):
    """Returns a dark blue string."""
    return utils.mircColor(s, "dark blue")


def pink(s):
    """Returns a pink string."""
    return utils.mircColor(s, "pink")


def dark_grey(s):
    """Returns a dark grey string."""
    return utils.mircColor(s, "dark grey")


def dark_gray(s):
    """Returns a dark grey string."""
    return utils.mircColor(s, "dark gray")


def light_grey(s):
    """Returns a light gray string."""
    return utils.mircColor(s, "light grey")


def light_gray(s):
    """Returns a light gray string."""
    return utils.mircColor(s, "light gray")


# Non-mIRC
def bold(s):
    """Returns the string s, bolded."""
    return f"\x02{s}\x02"


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
