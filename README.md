# domoticz-BR
<!---
[![GitHub license](https://img.shields.io/github/license/belzetrigger/domoticz-BR.svg)](https://github.com/belzetrigger/domoticz-BR/blob/master/LICENSE)
-->

[![PyPI pyversions](https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8-blue.svg)]() 
[![Plugin version](https://img.shields.io/badge/version-0.0.2-red.svg)](https://github.com/belzetrigger/domoticz-BR/branches/)

A simple alarm device that shows next collection dates from (Berlin Recycling)[https://www.berlin-recycling.de/] and turns alarm level according to this date.
| Device       | Image                                                                                                         | Comment                            |
| ------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Alarm Device | ![BR Device](https://raw.githubusercontent.com/belzetrigger/domoticz-BR/master/resources/BR_Alarm_Device.png) | show next date of waste collection |

This plugin is open source.


## Installation and Setup Plugin
- a running Domoticz: tested with 2020.1 with Python 3.7
- needed python modules, install via `sudo pip3 install requirements`
- clone project
    - go to `domoticz/plugins` directory 
    - clone the project
        ```bash
        cd domoticz/plugins
        git clone https://github.com/belzetrigger/domoticz-BR.git
        ```
- or just download, unzip and copy to `domoticz/plugins`

### Settings
<!-- prettier-ignore -->

| Parameter  | Information                                     |
| ---------- | ----------------------------------------------- |
| name       | Domoticz standard hardware name                 |
| user       | Account on BR web page                          |
| password   | Password fot that account                       |
| updatetime | time to poll new data 6h = 360 should be enough |
| debug      | if true some debug output                       |



## Bugs and ToDos
* optimize alarm level


## Versions
| Version | Note                                       |
| ------- | ------------------------------------------ |
| 0.0.2   | Inject intermediate certificate for https. |
| 0.0.1   | First version of this plugin.              |


Under development


