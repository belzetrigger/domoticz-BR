import unittest
import sys
import logging
import codecs

sys.path.insert(0, "..")
from blz.blzHelperInterface import BlzHelperInterface
from plugin import BasePlugin
from blz.fakeDomoticz import Parameters
from blz.fakeDomoticz import Devices

from br.brHelper import Br
import configparser

CONFIG_SECTION_MY = "login_my"
CONFIG_SECTION_STANDARD = "login_fail"

# set up log
# init ROOT logger from my_logger.logger_init()
from test.logger import logger_init
from test.logger import logger_cleanUp
logger_init()  # init root logger
log = logging.getLogger(__name__)  # module logger

import os
# logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
# log.level = logging.DEBUG


class Test_plugin(unittest.TestCase):
    def setUp(self):
        log.info("setUp test plugin")
        self.plugin = BasePlugin()  # plugin()

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/my_config.ini", encoding="utf-8"))
        self.br = self.readAndCreate(config, CONFIG_SECTION_MY)

        self.plugin.br = self.br

    def tearDown(self):
        log.info("# tear down: test for br")
        if self.plugin:
            self.plugin = None

        logger_cleanUp()
        # log.removeHandler(self.stream_handler)

    def test_onStart(self):
        log.info("#fake start of plugin")
        # should run with out fail
        self.plugin.onStart()
        # just init plugin without a run
        self.assertTrue(self.plugin.errorCounter == 0)
        self.assertIsNotNone(self.plugin.nextpoll)
        self.assertIsNotNone(self.plugin.pollinterval)
        # TODO self.assertIsNone(self.plugin.lastUpdate)

    def test_onHeartbeat(self):
        log.info("#fake heart beat")
        self.plugin.onStart()
        self.plugin.onHeartbeat()
        self.assertTrue(self.plugin.errorCounter == 0)
        self.assertIsNotNone(self.plugin.nextpoll)
        self.assertIsNotNone(self.plugin.pollinterval)
        self.assertIsNotNone(self.plugin.lastUpdate)

    def test_onStop(self):
        log.info("#fake stop")
        self.plugin.onStart()
        self.assertTrue(self.plugin.errorCounter == 0)
        self.assertIsNotNone(self.plugin.nextpoll)
        self.assertIsNotNone(self.plugin.pollinterval)
        self.plugin.onStop()
        # self.assertIsNone(self.plugin.br)

    def readAndCreate(
        self,
        aConfig,
        aSection,
        debugResponse: bool = False,
    ):
        """creates a br object based on config

        Args:
            aConfig ([type]): [configuration holding the address]

        Returns:
            [Br]: [br object]
        """
        self.assertTrue(
            aConfig.has_section(aSection),
            "we need this set up:  " + aSection,
        )
        usr = aConfig.get(aSection, "user")
        pw = aConfig.get(aSection, "pw")
        log.info("update Parameters as well for Plugin")
        Parameters['Mode1'] = usr
        Parameters['Mode2'] = pw

        aBr = Br(
            username=usr,
            password=pw
        )
        return aBr


if "__main__" == __name__:
    unittest.main()
