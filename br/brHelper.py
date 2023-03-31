# BRHelper class
import re
import json
from datetime import datetime, timedelta
from time import mktime
import time as myTime
# import urllib
from urllib.parse import quote, quote_plus
# workaround ssl issues
import ssl
import certifi
import pathlib

try:
    import Domoticz
except ImportError:
    from blz import fakeDomoticz as Domoticz

from blz.blzHelperInterface import BlzHelperInterface

import requests

BR_DATE_FORMAT = "%Y-%m-%d"  # date format we use
BR_NAME = "Papier"          # standard name
BR_HOUR_THRESHOLD = 12      # o'clock when it is time to show next date


class Br(BlzHelperInterface):
    """simple helper class for parsing content from berlin recycling"""

    BR_URL = "https://kundenportal.berlin-recycling.de/"
    BR_URL_DEFAULT = BR_URL + "Default.aspx"
    BR_URL_DEF_CHANGE = BR_URL_DEFAULT + "/ChangeDatasetTable"
    BR_URL_DEF_GET = BR_URL_DEFAULT + "/GetDatasetTableHead"

    def __init__(self, username: str, password: str, debug: bool = False):
        super(Br, self).__init__()
        self.username = username
        self.password = password
        self.debug = debug
        self.nextpoll: datetime = datetime.now()
        self.reset()

    def reset(self):
        self.needsUpdate = False
        self.dates = [None] * 2
        self.nearestDate: datetime.date = None
        self.resetError()
        self.lastRead: datetime = None
        self.lastDeviceName: str = None

    def reinitData(self):
        Domoticz.Debug("no internal data class, so no reinit needed")

    def checkError(self, jsn):
        '''checks if response contains error        
        '''
        if 'd' not in jsn:
            raise BaseException("cannot read response" + d)
        d = json.loads(jsn['d'])
        if 'Error' not in d:
            raise BaseException("Unknown feedback - must contain Error attribute")
        elif (d['Error'] is True):
            raise BaseException("Error - Details: " + d['Message'])

    def setError(self, error):
        '''sets the error msg and put error flag to True

        Arguments:
            error {Exception} -- the caught exception
        '''
        self.hasError = True
        self.errorMsg = error

    def resetError(self):
        '''just removes error flag and deletes last error msg
        '''
        self.hasError = False
        self.errorMsg = None

    def hasErrorX(self):
        return self.hasError

    def getErrorMsg(self):
        """
        if there is an error message, this will be delivered
        """
        return self.errorMsg

    def dumpConfig(self):
        Domoticz.Debug(
            "BR:{}\t"
            .format(self.username)
        )

    def stop(self):
        self.reset()

    def testCert(self):
        try:
            # Domoticz.Debug('current working directory: {}'.format(pathlib.Path().resolve()))
            # Domoticz.Debug('directory of the script being run: {}'.format(pathlib.Path(__file__).parent.resolve()))

            Domoticz.Debug('Checking connection to BR...' + self.BR_URL)
            test = requests.get(self.BR_URL)
            Domoticz.Debug('Connection to BR OK.')
        except requests.exceptions.SSLError as err:
            Domoticz.Error('SSL Error. Adding intermediate certs to Certifi store...')
            cafile = certifi.where()
            customCertPath = ("{}/sfig2.crt.pem".format(pathlib.Path(__file__).parent.resolve()))
            with open(customCertPath, 'rb') as infile:
                customca = infile.read()
            with open(cafile, 'ab') as outfile:
                outfile.write(customca)
            print('That might have worked.')

    def read(self):
        try:
            self.testCert()
            Domoticz.Debug('Retrieve waste collection data from ' + self.BR_URL)
            # workaround certs
            # certifi.where()
            Domoticz.Debug('Using root ca:' + certifi.where())
            REQUESTS_CA_BUNDLE = certifi.where()
            SSL_CERT_FILE = certifi.where()

            # conn = urllib3.connection_from_url(self.BR_URL, ca_certs=certifi.where())
            r = requests.get(self.BR_URL, verify=certifi.where())
            if r.status_code != 200:
                raise BaseException("connection problem")
            redirectUlr = r.url
            Domoticz.Debug('Retrieve redirect to ' + redirectUlr)
            s = requests.Session()
            r2 = s.get(redirectUlr)
            Domoticz.Debug('Start Login')

            # data = r2.json()
            Domoticz.Debug('BR: #1 working on Login:\t')

            url = redirectUlr
            headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Origin': 'https://kundenportal.berlin-recycling.de',
                'Content-Type': 'application/json; charset=UTF-8',
                'User-Agent': ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/81.0.4044.138 Safari/537.36"),
                'Accept': '*/*',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Referer': redirectUlr,
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            login_data = {
                'username': self.username,
                'password': self.password,
                'rememberMe': False,
                'encrypted': False
            }
            u = "https://kundenportal.berlin-recycling.de/Login.aspx/Auth"
            r3 = s.post(u, headers=headers, json=login_data)
            self.checkError(r3.json())
            # touch default page to see if works
            r3 = s.get(Br.BR_URL_DEFAULT)

            if (r3.status_code == 200):
                Domoticz.Debug('logged in')
                # https://kundenportal.berlin-recycling.de/(S(wkjgyi0a4lkmtrg3nimurb5k))/Default.aspx/ChangeDatasetTable
                # brDefaultUrl = r3.url
                # Domoticz.Debug('default url#3 {}'.format(brDefaultUrl))
                headers2 = {
                    'Connection': 'keep-alive',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                    'Content-Type': 'application/json; charset=UTF-8',
                    'Origin': 'https://kundenportal.berlin-recycling.de',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Dest': 'empty',
                    'Referer': Br.BR_URL_DEFAULT,
                    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                    # 'Cookie': ' cookieconsent_status=dismiss; _fbp=fb.1.1589755946090.857065657; _ga=GA1.2.657906153.1589755946; _gid=GA1.2.1757598692.1589755946',
                }
                # url3b = brDefaultUrl + "/GetDashboard"
                # change_data = None
                # r3b = s.post(url3b, headers=headers2, json=change_data)
                # soup = BeautifulSoup(r3b.content)
                # Domoticz.Debug("soup:{}".format(soup.prettify()))

                r3b = s.post(Br.BR_URL_DEFAULT + "/GetDashboard", headers=headers2)
                self.checkError(r3b.json())
                # https://kundenportal.berlin-recycling.de/Default.aspx/GetNavigationObject
                r3b = s.post(Br.BR_URL_DEFAULT + "/GetNavigationObject",
                             headers=headers2,
                             json={
                                 "updateUser": False})
                self.checkError(r3b.json())
                url3c = Br.BR_URL_DEFAULT + "/GetDataWithinFilter"
                cd3 = {"datasetTableCode": "ABFUHRKALENDER",
                       "minVal": "2023-02-27", "maxVal": "2023-04-10", "fieldNo": "10"}
                r3c = s.post(url3c, headers=headers2, json=cd3)
                self.checkError(r3c.json())

                url4 = Br.BR_URL_DEF_CHANGE

                # Domoticz.Debug('default url#4 {}'.format(url4))
                change_data = {'datasettable': 'ABFUHRKALENDER'}
                r4 = s.post(url4, headers=headers2, json=change_data)
                self.checkError(r4.json())
                # soup = BeautifulSoup(r4.content)
                # Domoticz.Debug("soup:{}".format(soup.prettify()))

                # # works
                # # GetDatasetTableHead
                url5 = Br.BR_URL_DEF_GET
                # Domoticz.Debug('default url#5 {}'.format(url5))
                change_data = {
                    "datasettablecode": "ABFUHRKALENDER",
                    "startindex": 0,
                    "searchtext": "",
                    "rangefilter": "",
                    "ordername": "",
                    "orderdir": "",
                    "ClientParameters": "",
                    "headrecid": ""}
                r5 = s.post(url5, headers=headers2, json=change_data)
                self.checkError(r5.json())
                # Domoticz.Debug('response {}'.format(r5))
                self.dates = self.getDates(r5.text)
                self.verify()
                self.lastRead = datetime.now()
        except BaseException as e:
            Domoticz.Error("Error reading BR: {} ".format(e))
            self.setError(e)

    def dumpStatus(self):
        s = "On Init"
        if (self.lastRead is not None and self.nearestDate is not None):
            s = ("Status BR: "
                 "read:\t{}\t"
                 "needsUpdate:\t{}\t"
                 "nearestDate:\t{:%d.%m.%Y}\t"
                 .format(self.lastRead, self.needsUpdate, self.nearestDate))

        Domoticz.Log(s)

    def getSummary(self, seperator: str = '<br>'):

        summary = ""
        if (self.dates.__len__ == 0):
            summary = "NO DATA FOUND!"
        elif (self.dates[0] is not None):
            summary = "{}{} {:%d.%m.%Y %a}{}".format(summary, BR_NAME, self.dates[0], seperator)
            summary = "{}{} {:%d.%m.%Y %a}{}".format(summary, BR_NAME, self.dates[1], seperator)
           # summary = "{}{} {:%d.%m.%Y %a}{}".format(summary, BR_NAME, self.dates[2], seperator)
        return summary

    def verify(self):
        """should be called after reading  values from web.
        analyze the dates and calculates the name.
        and marks element as needs update=True if there are changes
        """
        if self.dates:
            d: datetime = self.dates[0]
            # threshold to skip to next date
            if (d == datetime.now().date() and datetime.now().hour > BR_HOUR_THRESHOLD):
                Domoticz.Log("Nearest Date is today and now it is too late.... So switch to next date")
                d: datetime = self.dates[1]

            if not self.nearestDate:
                Domoticz.Log("No old nearest Date so set it to:{} - maybe init?".format(d))
                self.nearestDate = d
                self.lastDeviceName = self.calculateName()
                self.needsUpdate = True
            else:
                Domoticz.Debug("Compare dates")
                if d > self.nearestDate:
                    Domoticz.Log("Found a new Date: {}".format(d))
                    self.nearestDate = d
                    self.needsUpdate = True
                elif d == self.nearestDate:
                    Domoticz.Debug("same date - check name")
                    self.needsUpdate = False
                    s = self.calculateName()
                    if (self.lastDeviceName != s):
                        self.lastDeviceName = s
                        self.needsUpdate = True

                else:
                    Domoticz.Error("Should not happen - re-init?")

    def getDates(self, txt: str):
        """extracts from html response the '\"Task Date\":\"2020-07-15\",'
        and converts it to date array

        Arguments:
            txt {str} -- response.txt

        Returns:
            [date] -- [array of dates]
        """
        # Domoticz.Debug('getDates {}'.format(txt))
        jData = json.loads(txt)
        jData2 = json.loads(jData['d'])  # just get data inside
        objects = (jData2['Object'])  # just extract objects

        if 'data' not in objects:
            Domoticz.Error("UNKNOWN Structure of response json")
        ar = objects['data']
        # Domoticz.Debug('data array: {}'.format(ar))
        dates = []

        for e in ar:
            if (e):
                sDate = e['Task Date']
                # Domoticz.Debug('date: {}'.format(sDate))
                d = toDate(sDate, BR_DATE_FORMAT)
                # Domoticz.Debug('date: {}'.format(d))
                dates.append(d.date())

        Domoticz.Debug('parsed data {}'.format(dates))
        return dates

    def getNearestDate(self):
        d = None
        if self.nearestDate is not None:
            d = self.nearestDate
        return d

    def getName(self):
        """just return last calculated device name. More see calculateName

        Returns:
            str: the last name
        """
        return self.lastDeviceName

    def needsUpdateX(self):
        return self.needsUpdate

    def getDeviceName(self):
        """calculates a name based on nearest waste element


        Returns:
            {str} -- name as string
        """
        return self.calculateName()

    def getAlarmText(self):
        """only returns latest element like: (date) [optional hint]
        if you want more, look at getSummary()

        Returns:
            {str} -- data from nearest text
        """

        s = "No Data"
        if self.hasError is False and self.nearestDate is not None:
            hint = None  # future i
            s = "{}{}".format(self.nearestDate, hint if hint is not None else "")
        if self.hasError is True:
            s = "Error to get data"
        return s

    def calculateName(self):
        '''calculates a name based on nearest waste element
         form: [image optional] (waste type) (days till collection)

         Returns:
             {str} -- name as string
        '''

        s = "No Data"
        if (self.nearestDate):
            dt = self.nearestDate
            lvl = calculateAlarmLevel(dt)
            days = lvl[1]
            # TODO Image?
            # img = ''
            # if (SHOW_ICON_IN_NAME is True):
            #     img = "{}".format(self.nearest.getImageTag('22', '0', 'top'))
            # s = "{} {} {}".format(img, t, lvl[1])
            s = "Papier{}".format(lvl[1])

        if (self.hasError is True):
            s = "!Error!"
        return s

    def getAlarmLevel(self):
        '''calculates alarm level based on nearest waste element

        Returns:
            {int} -- alarm level
        '''

        alarm = 0
        if (self.hasError is False):
            dt = self.nearestDate
            lvl = calculateAlarmLevel(dt)
            alarm = lvl[0]
        else:
            alarm = 5
        return alarm


def calculateAlarmLevel(wasteDate: datetime):
    '''takes an date calculates the domoticz alarm level

    Arguments:
        wasteDate {[datetime]} -- the element to check

    Returns:
        [{int}, text ]-- alarm level and text holding the days till date
    '''

    level = 1
    smallerTxt = ""
    if (wasteDate is not None):
        delta = wasteDate - datetime.now().date()
        # Level = (0=gray, 1=green, 2=yellow, 3=orange, 4=red)
        if delta.days <= 1:
            level = 4
        elif delta.days == 2:
            level = 3
        elif delta.days == 3:
            level = 2
        else:
            level = 0

        if delta.days == 2:
            smallerTxt = '{} ({})'.format(smallerTxt, "Übermorgen")
        elif delta.days == 1:
            smallerTxt = '{} ({}!)'.format(smallerTxt, "Morgen")
        elif delta.days == 0:
            smallerTxt = '{} ({}!!!)'.format(smallerTxt, "Heute")
        else:
            smallerTxt = '{} ({} Tage)'.format(smallerTxt, delta.days)
    return [level, smallerTxt]


def toDate(sDate: str, sformat: str = "%Y-%m-%d"):
    try:
        res = datetime.strptime(sDate, sformat)
    except TypeError:
        res = datetime(*(myTime.strptime(sDate, sformat)[0:6]))
    # Domoticz.Debug("date: ".format(res))  # testcompete print alternation
    return res
