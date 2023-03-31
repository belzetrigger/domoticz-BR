import unittest
import sys
import logging
import codecs


sys.path.insert(0, "..")
from br.brHelper import Br
import configparser

CONFIG_SECTION_MY = "login_my"
CONFIG_SECTION_STANDARD = "login_fail"

# set up logger
logger = logging.getLogger()
logger.level = logging.DEBUG


class Test_br(unittest.TestCase):
    def setUp(self):
        # work around logger
        self.stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(self.stream_handler)
        logging.getLogger().info("# set up test for br")

    def tearDown(self):
        logging.getLogger().info("# tear down: test for br")
        if self.br:
            self.br.reset()
            self.br = None

        # remove logger
        logger.removeHandler(self.stream_handler)

    def test_myLogin(self):
        """
        takes config from **my** config and tests it
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/my_config.ini", encoding="utf-8"))

        self.br = self.readAndCreate(config, CONFIG_SECTION_MY)
        self.doWork(self.br)

    def test_fail_throws_exception(self):
        """
        takes fail login from common config and tests it
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.br = self.readAndCreate(
            aConfig=config,
            aSection=CONFIG_SECTION_STANDARD
        )
        # we catching now internally
        # self.assertRaises(BaseException, self.br.read())
        self.br.read()
        self.assertTrue(self.br.hasErrorX())
        self.assertIsNotNone(self.br.getErrorMsg)

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

        aBr = Br(
            username=usr, password=pw, debug=debugResponse
        )
        return aBr

    def doWork(self, aBr: Br):
        """quickly reads content from internet

        Args:
            aBr (Br): the object to test
        """
        self.assertIsNotNone(
            aBr, "We do not an object of br, otherwise no tests are possible"
        )
        aBr.dumpConfig()
        self.assertIsNone(aBr.getNearestDate(), "obj is fresh, so should be empty")
        self.assertFalse(aBr.hasErrorX(), "obj is fresh, so should stay with null")
        aBr.read()
        aBr.dumpStatus()
        self.assertIsNotNone(aBr.getSummary())
        self.assertIsNotNone(aBr.getNearestDate())
        self.assertIsNotNone(aBr.getAlarmLevel())
        self.assertTrue(aBr.needsUpdateX())
        logging.getLogger().info("summary: {}".format(aBr.getSummary()))
        logging.getLogger().info(
            "date: {} \nlevel:{} \ntxt: {} \nname: {}".format(
                aBr.getNearestDate(),
                aBr.getAlarmLevel(),
                aBr.getAlarmText(),
                aBr.getDeviceName(),
            )
        )


if "__main__" == __name__:
    unittest.main()
