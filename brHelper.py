# BRHelper class
import re
import json
from datetime import datetime, timedelta
from time import mktime
import time as myTime
# import urllib
from urllib.parse import quote, quote_plus

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

try:
    from bs4 import BeautifulSoup
except Exception as e:
    Domoticz.Error("Error import BeautifulSoup".format(e))

try:
    import requests
except Exception as e:
    Domoticz.Error("Error import requests".format(e))

BR_DATE_FORMAT = "%Y-%m-%d"  # date format we use
BR_NAME = "Papier"          # standard name
BR_HOUR_THRESHOLD = 14      # o'clock when it is time to show next date


class Br(object):
    """simple helper class for parsing content from berlin recycling"""

    BR_URL = "https://kundenportal.berlin-recycling.de/"

    def __init__(self, username: str, password: str, debug: bool = False):
        super(Br, self).__init__()
        self.username = username
        self.password = password
        self.debug = debug
        self.nextpoll: datetime = datetime.now()
        self.reset()

    def reset(self):
        self.needsUpdate = False
        self.dates = []
        self.nearestDate: datetime.date = None
        self.resetError()
        self.lastRead: datetime = None
        self.lastDeviceName: str = None

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

    def dumpConfig(self):
        Domoticz.Debug(
            "BR:{}\t"
            .format(self.username)
        )

    def stop(self):
        self.reset()

    def read(self):
        try:
            Domoticz.Debug('Retrieve waste collection data from ' + self.BR_URL)
            r = requests.get(self.BR_URL)
            if r.status_code != 200:
                raise BaseException("connection problem")
            redirectUlr = r.url
            Domoticz.Debug('Retrieve redirect to ' + redirectUlr)
            s = requests.Session()
            r2 = s.get(redirectUlr)
            Domoticz.Debug('Start Login')

            # data = r2.json()
            Domoticz.Debug('BR: #1 working on Login:\t')
            viewStateValue = None
            eventTargetValue = None
            eventTargetArgValue = None
            viewStateGenValue = None
            eventValidValue = None
            soup: BeautifulSoup = BeautifulSoup(r2.content, "html.parser")
            # soup = BeautifulSoup(r2.content)
            viewStateValue = getInputValue(soup, '__VIEWSTATE')
            # viewStateValue = soup.find('input', {'id': '__VIEWSTATE'}).get('value')
            eventTargetValue = getInputValue(soup, '__EVENTTARGET')
            # eventTargetValue = soup.find('input', {'id': '__EVENTTARGET'}).get('value')
            eventTargetArgValue = getInputValue(soup, '__EVENTARGUMENT')
            # eventTargetArgValue = soup.find('input', {'id': '__EVENTARGUMENT'}).get('value')

            # next block
            viewStateGenValue = getInputValue(soup, '__VIEWSTATEGENERATOR')
            # viewStateGenValue = soup.find('input', {'id': '__VIEWSTATEGENERATOR'}).get('value')
            eventValidValue = getInputValue(soup, '__EVENTVALIDATION')
            # eventValidValue = soup.find('input', {'id': '__EVENTVALIDATION'}).get('value')

            url = redirectUlr
            headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Origin': 'https://kundenportal.berlin-recycling.de',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Referer': redirectUlr,
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            login_data = {
                '__EVENTTARGET': 'btnLog',
                '__EVENTARGUMENT': eventTargetArgValue,
                '__VIEWSTATE': viewStateValue,
                '__VIEWSTATEGENERATOR': viewStateGenValue,
                '__EVENTVALIDATION': eventValidValue,
                'Username': '***REMOVED***',
                'Password': '***REMOVED***'
            }
            r3 = s.post(url, headers=headers, data=login_data)
            # should be redirect 302  to Default and there a 200 code
            if(r3.status_code == 200):
                Domoticz.Debug('logged in Login')
                # https://kundenportal.berlin-recycling.de/(S(wkjgyi0a4lkmtrg3nimurb5k))/Default.aspx/ChangeDatasetTable
                brDefaultUrl = r3.url

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
                    'Referer': brDefaultUrl,
                    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                    # 'Cookie': ' cookieconsent_status=dismiss; _fbp=fb.1.1589755946090.857065657; _ga=GA1.2.657906153.1589755946; _gid=GA1.2.1757598692.1589755946',
                }
                url3b = brDefaultUrl + "/GetDashboard"
                change_data = {'withhtml': 'true'}
                r3b = s.post(url3b, headers=headers2, json=change_data)
                # soup = BeautifulSoup(r3b.content)
                # Domoticz.Debug("soup:{}".format(soup.prettify()))

                url4 = brDefaultUrl + "/ChangeDatasetTable"
                change_data = {'datasettable': 'ENWIS_ABFUHRKALENDER'}
                r4 = s.post(url4, headers=headers2, json=change_data)
                # soup = BeautifulSoup(r4.content)
                # Domoticz.Debug("soup:{}".format(soup.prettify()))

                # # works
                # # GetDatasetTableHead
                url5 = brDefaultUrl + "/GetDatasetTableHead"
                change_data = {
                    "datasettablecode": "ENWIS_ABFUHRKALENDER",
                    "startindex": 0,
                    "searchtext": "",
                    "rangefilter": "",
                    "ordername": "",
                    "orderdir": "",
                    "ClientParameters": "",
                    "headrecid": ""}
                r5 = s.post(url5, headers=headers2, json=change_data)
                self.dates = self.getDates(r5.text)
                self.verify()
                self.lastRead = datetime.now()
        except Exception as e:
            Domoticz.Error("Error reading BR: {} ".format(e))
            self.setError(e)

    def dumpStatus(self):
        Domoticz.Log("Status BR:"
                     "read:\t{}\t"
                     "needsUpdate:\t{}\t"
                     "nearestDate:\t{:%d.%m.%Y}\t"
                     .format(self.lastRead, self.needsUpdate, self.nearestDate))

    def getSummary(self, seperator: str = '<br>'):

        customObjects = []
        summary = ""
        summary = "{}{} {:%d.%m.%Y %a}{}".format(summary, BR_NAME, self.dates[0], seperator)
        summary = "{}{} {:%d.%m.%Y %a}{}".format(summary, BR_NAME, self.dates[1], seperator)
        summary = "{}{} {:%d.%m.%Y %a}{}".format(summary, BR_NAME, self.dates[2], seperator)
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
                    if(self.lastDeviceName != s):
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
        jData = json.loads(txt)
        jData2 = json.loads(jData['d'])  # just load again, as before it might be incomplete json
        ar = jData2['data']
        dates = []
        for e in ar:
            sDate = e['Task Date']
            if sDate:
                d = datetime.strptime(sDate, BR_DATE_FORMAT)
                dates.append(d.date())

        return dates

    def getName(self):
        """just return last calculated device name. More see calculateName

        Returns:
            str: the last name
        """
        return self.lastDeviceName

    def calculateName(self):
        '''calculates a name based on nearest waste element
         form: [image optional] (waste type) (days till collection)

         Returns:
             {str} -- name as string
        '''

        s = "No Data"
        if(self.nearestDate):
            dt = self.nearestDate
            lvl = calculateAlarmLevel(dt)
            days = lvl[1]
            # TODO Image?
            # img = ''
            # if (SHOW_ICON_IN_NAME is True):
            #     img = "{}".format(self.nearest.getImageTag('22', '0', 'top'))
            # s = "{} {} {}".format(img, t, lvl[1])
            s = "Papier{}".format(lvl[1])

        if(self.hasError is True):
            s = "!Error!"
        return s

    def getAlarmLevel(self):
        '''calculates alarm level based on nearest waste element

        Returns:
            {int} -- alarm level
        '''

        alarm = 0
        if(self.hasError is False):
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
    if(wasteDate is not None):
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


def findDivByClass(soup: BeautifulSoup, name: str):
    """just search 

    Arguments:
        soup {BeautifulSoup} -- the soup
        name {str} -- classname attribute of the searched div element

    Returns:
        [soup element] -- the found element
    """
    d = soup.find("div", {"class": name})
    if d is None:
        d = soup.find_all("div", class_=name)
    return d


def findDivByName(soup: BeautifulSoup, name: str):
    return soup.find("div", {"name": name})


def getInputValue(soup: BeautifulSoup, id: str):
    """search input field by Id and return value

    Arguments:
        soup {BeautifulSoup} -- the soup
        id {str} -- id of searched element

    Returns:
        [type] -- value
    """
    inpt = soup.find('input', {'id': id})
    return getValue(inpt)


def getValue(inpt):
    """reads in an input field and extracts the value of it

    Args:
        inpt ([type]): html input field

    Returns:
        str: value of that field
    """
    r: str = None
    if inpt:
        r = inpt.get('value')
    return r
