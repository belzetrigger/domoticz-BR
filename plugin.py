# plugin for fetching dates from berlin recycling
#
# Author: belze
#
"""
BerlinRecycling Paper Collection Date Reader Plugin

Author: Belze(2020)


Version:    0.0.1: Initial Version
"""

"""
<plugin key="BerlinRecycling" name="Berlin Recycling" author="belze" version="0.0.1"
externallink="https://github.com/belzetrigger/domoticz-BR" >
    <description>
        <h2>Berlin Recycling - Paper collection</h2><br/>
        Fetch next dates from https://www.berlin-recycling.de
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Fetch the dates online</li>
            <li>Switch alarmlevel according to next collection date</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Alarm - showing the dates</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options, details see github
    </description>
    <params>
        <param field="Mode1" label="username" width="200px"
        required="true"/>
        <param field="Mode2" label="password" width="200px"
        password="true"
        required="true" />

        <param field="Mode4" label="Update every x hours" width="200px"
        required="true" default="3"/>

        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="False" />
            </options>
        </param>
    </params>
</plugin>
"""

from datetime import datetime, timedelta


try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

from brHelper import Br

# config
PARAM_PASS = "Mode2"        # idx for password
MIN_POLL_TIME = 1           # in hours
MAX_POLL_TIME = 24          # in hours
# icons

# units
UNIT_ALARM_IDX = 1
UNIT_ALARM_NAME = "Papier-Entsorung"
UNIT_ALARM_OPTIONS = ""


class BasePlugin:
    enabled = False

    def __init__(self):
        self.debug: bool = False
        self.nextpoll = datetime.now()
        self.pollinterval = 60 * 60  # once a hour
        self.errorCounter = 0
        self.br: brHelper.Br = None
        self.user: str = None
        self.pw: str = None
        return

    def onStart(self):
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)

        Domoticz.Log("onStart called")

        # check polling interval parameter
        try:
            temp = int(Parameters["Mode4"])
        except:
            Domoticz.Error("Invalid polling interval parameter")
            temp = 60

        if temp < MIN_POLL_TIME:
            temp = MIN_POLL_TIME            # minimum polling interval
            Domoticz.Error(
                "Specified polling interval too short: changed to {}} minutes".format(MIN_POLL_TIME))
        elif temp > (MAX_POLL_TIME):
            temp = (MAX_POLL_TIME)          # maximum polling interval is 1 hour
            Domoticz.Error(
                "Specified polling interval too long: changed to {} hour".format(MAX_POLL_TIME))

        self.pollinterval = temp * 60 * 60  # its hour based
        Domoticz.Log("Using polling interval of {} seconds".format(
            str(self.pollinterval)))
        # recipient
        self.user = Parameters["Mode1"]
        # group
        self.pw = Parameters["Mode2"]

        # create devices
        createDevices()
        # switch them to Off state
        Devices[UNIT_ALARM_IDX].Update(0, "Off", Name=UNIT_ALARM_NAME)

        # images

        try:

            self.brHelper = Br(username=self.user,
                               password=self.pw,
                               debug=self.debug)

            if(self.debug):
                self.brHelper.dumpConfig()

            # do first read here or later?
            # self.brHelper.read()
            # Devices[UNIT_ALARM_IDX].Update(self.brHelper.getAlarmLevel(), "On", Name=self.brHelper.getName())

        except Exception as e:
            Domoticz.Error("Init error ....{}".format(e))
            Devices[UNIT_ALARM_IDX].Update(0, "Off", Name=UNIT_ALARM_NAMEs + " << ERROR ")

    def onStop(self):
        if self.brHelper:
            self.brHelper.stop()
        Devices[UNIT_ALARM_IDX].Update(0, "Off", Name=UNIT_ALARM_NAME)
        Domoticz.Log("onStop called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit "
                     + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()
        #params = params.capitalize()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("BLZ Notification: " + Name + "," + Subject + "," + Text + ","
                     + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called")
        myNow = datetime.now()
        if myNow >= self.nextpoll:
            Domoticz.Debug(
                "----------------------------------------------------")
            hasError = False
            self.nextpoll = myNow + timedelta(seconds=self.pollinterval)
            self.brHelper.read()
            # we might still have an internal error
            if (hasError is False and self.brHelper.hasError is True):
                hasError = True
                Domoticz.Error("internal error discovered ..")

            if hasError:
                if self.errorCounter > 5:
                    self.nextpoll = myNow + timedelta(minutes=5)
                    self.brHelper.stop()
                    Domoticz.Error("To much error happend, reset and wait 5min ")
                else:
                    self.errorCounter += 1
                    Domoticz.Error(
                        "Uuups. Something went wrong ... Shouldn't be here.")
                    t = "Error"
                    self.nextpoll = myNow

            else:
                self.errorCounter = 0
                if self.brHelper.needsUpdate is True:
                    alarmLevel = self.brHelper.getAlarmLevel()
                    summary = self.brHelper.getSummary()
                    name = self.brHelper.getName()
                    # TODO as we change name but updateDevice is not checking this, we say alwaysUpdate
                    updateDevice(1, alarmLevel, summary, name, True)
                    self.lastUpdate = myNow
                # only on succees set next poll time, so on error, we run it next heartbeat
                self.nextpoll = myNow + timedelta(seconds=self.pollinterval)

            Domoticz.Debug(
                "----------------------------------------------------")


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


# def onConnect(Connection, Status, Description):
#    global _plugin
# _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


# def onDeviceModified(Unit):
#    global _plugin
#    _plugin.onDeviceModified(Unit)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            value: str = str(Parameters[x])
            if(x == PARAM_PASS):
                value = 'xxx'
            Domoticz.Debug("{}:\t{}".format(x, value))
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


def createDevices():
    if UNIT_ALARM_IDX not in Devices:
        Domoticz.Device(Name=UNIT_ALARM_NAME, Unit=UNIT_ALARM_IDX, TypeName="Alert",
                        Used=1,
                        Options=UNIT_ALARM_OPTIONS
                        ).Create()
        Domoticz.Log("Devices[UNIT_ALARM_IDX={}] created.".format(UNIT_ALARM_IDX))
    #   updateImageByUnit(UNIT_CMD_SWITCH_IDX, ICON_ADMIN)


def updateDevice(Unit, alarmLevel, alarmData, name='', alwaysUpdate=False):
    '''update a device - means today or tomorrow, with given data.
    If there are changes and the device exists.
    Arguments:
        Unit {int} -- index of device, 1 = today, 2 = tomorrow
        highestLevel {[type]} -- the maximum warning level for that day, it is used to set the domoticz alarm level
        alarmData {[str]} -- data to show in that device, aka text

    Optional Arguments:
        name {str} -- optional: to set the name of that device, eg. mor info about  (default: {''})
        alwaysUpdate {bool} -- optional: to ignore current status/needs update (default: {False})
    '''

    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if (alarmData != Devices[Unit].sValue) or (int(alarmLevel) != Devices[Unit].nValue or alwaysUpdate is True):
            if(len(name) <= 0):
                Devices[Unit].Update(int(alarmLevel), alarmData)
            else:
                Devices[Unit].Update(int(alarmLevel), alarmData, Name=name)
            Domoticz.Log("BLZ: Updated to: {} value: {}".format(alarmData, alarmLevel))
        else:
            Domoticz.Log("BLZ: Remains Unchanged")
    else:
        Domoticz.Error("Devices[{}] is unknown. So we cannot update it.".format(Unit))
