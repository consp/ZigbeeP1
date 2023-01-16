# P1 to Zigbee device

This repository describes an example of what I used to create a zigbee 2 MQTT device.
The reason for doing this is to be able to shut down all normal non-essential networking when I'm gone and since the P1 reader was the last WiFi device reporting to my domoticz instance ...

I could not find any other device publishing P1 port ([See DSMR standard](https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_a727fce1f1.pdf)) data I made it myself.

Initial version (yes it's a mess, resistor values are approximate):

<img src="https://github.com/consp/ZigbeeP1/blob/master/img/breadboard_attempt_1.jpg?raw=true" width="400" alt="Wiring mess with random resistors">


Hooked up, resulting in the second image, ignore the phase B/C values they are dummy values which are stuck in z2mqtt for now (only have 1 phase):

<img src="https://github.com/consp/ZigbeeP1/blob/master/img/attempt_1_hooked_up.jpg?raw=true" width="400" alt="Sketchy setup #1"><img src="https://github.com/consp/ZigbeeP1/blob/master/img/z2mqtt.jpg?raw=true" alt="Z2MQTT values" width="400"> 





## Requirements
* [Sparkfun XBee3 Plus thing](https://www.sparkfun.com/products/15435), this was what was available to me and it does micropython.
* Breadboard or other thing to make some electronics work. As soon as I have my working board printed I'll publish that. Now it's a breadboard mess.
* 6 pin RJ12 cable to connect to the P1 port (You really want that, it's free power on pin 1/6!)
* Some soldering skills
* Patience

## What does it do
The device reads the P1 port, converts the data to something useful and reports it via zigbee to any zigbee2mqtt device (or normal zigbee, but that's untested).

* It does custom ZDO commands where needed.
* It does ZCL commands/data transfers when asked for or when data available

## What does it not do

* Respond to any set zigbee requests from the controller, nothing is configurable at this time (it's a reporting device, I don't see the need)
* Be zigbee complient, some (if not most) messages will be ignored. I did the minimal (plus a tiny bit) to get it to work with zigbee2mqtt

## How does it work

The device enters the zigbee network after which it will report.
It uses two endpoints, endpoint 1 for all electrical data and endpoint 2 for gas data.

* It uses zigbee profile 0x0104 (Home Automation) for both endpoints
* The used clusters are:
  * 0x0702 aka seMetering aka SmartEnergy Metering
  * 0x0B04 aka haElectricalMeasurement aka Electrical Measurement, only for endpoint 1
* For cluster 0x0702 it reports the following:
  * 0x0000, total power used (sum of T1 + T2 from grid)
  * 0x0100, total power used T1 (from grid, endpoint 1&2)
  * 0x0101, total power delivered T1 (to grid, endpoint 1)
  * 0x0102, total power used T2 (from grid, endpoint 1)
  * 0x0103, total power delivered T2 (to grid, endpoint 1)
  * 0x0200, status, always 0x00
  * 0x0300, unit of measure, always 0x00 (kwh for endpoint 1) or 0x01 (m3 for endpoint 2)
  * 0x0301, unit multiplier, always 1
  * 0x0302, unit divisor, always 1000
* For cluster 0xB04:
  * 0x0304, combined power output (only from grid, all phases)
  * 0x0505, Voltage phase A (L1)
  * 0x0905, Voltage phase B (L2)
  * 0x0A05, Voltage phase C (L3)
  * 0x0506, Current phase A (L1)
  * 0x0906, Current phase B (L2)
  * 0x0A06, Current phase C (L3)
  * 0x050B, Active Power phase A (L1)
  * 0x090B, Active Power phase B (L2)
  * 0x0A0B, Active Power phase C (L3)
  * 0x0600, Voltage multiplier, always 1
  * 0x0601, Voltage divider, always 10
  * 0x0602, Current multiplier, always 1
  * 0x0603, Current divider, always 100
  * 0x0402, Power multiplier, always 1
  * 0x0403, Power divider, always 1

# How to

## What's in here
This repository includes the following:

* A main.py micropython file to run on the Sparkfun XBee3 device
* A converter file to allow zigbee2mqtt to publish the data in a somewhat usable format, this includes the svalue string for domoticz
* A domoticz patch file to use the gas/P1 port data (P1 data is in svalue format) to add this as a standard "dummy" p1 power/gas meter.
* Domoticz MQTT thing doesn't really do multi-value things and I wasn't going to change anything complicated so it only works with a very specific topic and the "name" of that topic MUST end in P1 and MUST be recognized as text

## What's not here

* Instruction on how to use this all except for everything already stated. Please do not ask me for "get it work in X" or any question starting with how or why. Knowledgable input will be appreciated but this is a hobby project.

## Configurable variables in main.py
* `NAME` Sets the name of the device
* `DEBUG` Guess what, it pushes data to the TX port to be reported to the uart
* `ALWAYS_PUBLISH` Always publish configuration and data
* `CYCLE_TIME` Time in seconds between reads/publications from P1 port


## Compile the main.py code
Meet the following requirements:
* Python 3.6 or later
* [mpy_cross package: v1.12](https://pypi.org/project/mpy-cross/1.12/), no other will work (properly)

Compile with:
```
python3 -m mpy_cross -msmall-int-bits=31 -o main.mpy -mno-unicode main.py
```
Replace `python3` for `py3`/`py` on windows.

`-msmall-int-bits=31` is required. Not using it might run into either 32bit issues or memory issues.

`-mno-unicode` is required. I don't know why but the micropython implementation sparkfun uses does not include unicode support afaik.

## Modify Zigbee2MQTT
You need to import the P1.js into Zigbee2MQTT, [see the documentation for external converters](https://www.zigbee2mqtt.io/advanced/support-new-devices/01_support_new_devices.html#_2-adding-your-device).

## Modify domoticz
Apply the patch to the source and compile it yourself.

# Other stuff
## Acknowledgements
Telegram test data was used from [@ndokter](https://github.com/ndokter) (https://github.com/ndokter/dsmr_parser/blob/master/test/example_telegrams.py) to validate DSMR telegram parsing.

## Read this if you want to exploit this repository for profit
Any commercial use, in any form for whatever reason, will not be "appreciated", this includes non-profit.
I do not publish complete working packages so most licenses do not apply and all code was written by me. If you want to do this anyway contact me. Failure to contact is equivalent to non complience.
