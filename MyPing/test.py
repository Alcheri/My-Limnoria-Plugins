###
# Copyright (c) 2020, Barry Suridge
# All rights reserved.
#
#
###

from supybot.test import *
import supybot.conf as conf


class MyPingTestCase(PluginTestCase):
    plugins = ("MyPing",)

    def testSimple(self):
        self.assertNotError("myping ping google.com")
        self.assertNotError("myping ping 2a03:2880:f119:8083:face:b00c:0:25de")


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
