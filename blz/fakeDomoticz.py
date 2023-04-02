#   This plugin is kind of a Domoticz Emulater.
#   It "emulates" Domoticz.Log() and Domoticz.Debug(), Parameters and Devices
#   So it is possible to run tests locally

#   Based on idea from Buienradar.nl Weather Lookup Plugin
#   Frank Fesevur, 2017
#   https://github.com/ffes/domoticz-buienradar
#
#
from typing import Any, Dict
import logging
log = logging.getLogger(__name__)
log.level = logging.DEBUG

Parameters: Dict[str, Any] = {"Mode1": None,
                              "Mode2": None,
                              "Mode3": None,
                              "Mode4": None,
                              "Mode5": None,
                              "Mode6": "Debug",
                              "HomeFolder": "./",
                              "StartupFolder": "wwwtest/"
                              }
Images: Dict[str, Any] = {}
Devices: Dict[str, Any] = {}


class X:
    """
    fake class
    """
    ID: str
    Name: str
    Unit: str
    DeviceID: str
    sValue: str
    descr: str
    level: int
    nValue: int
    LastLevel: int

    def __init__(self, iUnit: int, aID: str) -> None:
        self.ID = aID
        self.Name = str(aID)
        self.Unit = aID
        self.DeviceID = aID
        self.sValue = str(aID)
        self.nValue = iUnit
        self.level = 0
        pass

    def Create(self):
        log.info("create called")
        pass

    def Update(self, nValue: int = 0, sValue: str = None, Name: str = None, descr: str = None):
        '''
        nValue: alarmLevel
        sValue: alarmData
        '''
        self.LastLevel = self.level
        self.level = nValue
        self.Name = Name
        self.descr = descr
        self.sValue = sValue
        log.debug("update called:  alarmLevel: {}, "
                  "alarmData: {} , Name: {}, descr: {} "
                  .format(nValue, sValue, Name, descr))
        pass


def Image(sZip: str):
    log.debug("create image: " + sZip)
    img = X(sZip)
    Images[str] = img
    return img


def Device(Name: str, Unit: str, TypeName: str,
           Used: bool = 1,
           Switchtype: int = 18, Options: str = None):
    log.debug("Device called: Name: {}, Unit: {}, TypeName: {}, "
              "Used: {}, Switchtype: {},Options: {}".format(
                  Name, Unit, TypeName, Used, Switchtype, Options))
    x = X(Unit, str(Unit))
    Devices[Unit] = x
    return x


def Log(s):
    log.info(s)


def Debug(s):
    log.debug(s)


def Error(s):
    log.error(s)


def Debugging(i):
    Log("Debug: turned to: {}".format(i))
