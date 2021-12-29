# Domoticz-ZWaveJS2MQTT-Websocket-Bridge-Plugin
This project is to create a bridge for ZWaveJS2MQTT to Domoticz, for updates Domoticz doesn't know how to handle.

This project uses the Websockets server of ZWaveJS2MQTT to monitor updates from ZWaveJS2MQTT and transfer them to
devices in Domoticz.  The devices are set up in the devices.ini file and the plugin creates them when it receives
the request.  This is useful for cases where you have updates that domoticz doesn't understand by turning them
into a domoticz device through the ini file. You can take  something like Thermostat State, which is not handled
in Domoticz, and turn it into a device which tells you that your furnace is off or on.

Why'd I use Websocket instead of MQTT?  Two reasons: Websockets don't need a mosquitto server and I have more
experience with web sockets.

# Installation
Goto your plugin folder and clone this repo.

# How to set up new devices
The devices.ini file defines the Zwave devices you want to creat and how youy interact with them. This is an
example device:

[2.0]                           ;Device node ID in ZWaveJS2MQTT the period followed by a number is for adding more than one Domoticz device per ZWaveJS2MQTT node
name=2nd Floor Fire Alarm State ;Name of the domoticz device to change.      /|If two Domoticz devices have the same name the index should be same too.
index=1                         ;Plugin hardware ID #. You decide what it is.\|Example: Using two ZWaveJS2MQTT updates to change the s and n values of 1 device.
typeID=243                      ;The device type ID #. See Domoticz device types: https://www.domoticz.com/wiki/Developing_a_Python_plugin#Available_Device_Types
subTypeID=31                    ;The subtype # ID of device.  See Domoticz device subtypes: https://www.domoticz.com/wiki/Developing_a_Python_plugin#Available_Device_Types
switchTypeID=0                  ;Switch type ID #.  See Domoticz device switchtypes: https://www.domoticz.com/wiki/Developing_a_Python_plugin#Available_Device_Types
commandClass=Notification       ;What Zwave command class this device is.(Str/Int)<--ALWAYS NEEDED
endpoint=0                      ;When there are multple properties of the same name. 0 if not needed. (Int)<--Not always needed
property=alarmType              ;Property name of event in ZWaveJS2MQTT to change in Domoticz.(Str/Int)<--ALWAYS NEEDED
propertyKey=0                   ;When there are multple properties of the same name. 0 if not needed. (Int)<--Not always needed
value=sValue                    ;What property of the device in Domoticz we want to change
image=0                         ;Image you'd like for the device. Differs for each set up. Check http://127.0.0.1/json.htm?type=custom_light_icons on your server.
options=                        ;Python Dictionary contaning options. Depends on your device. Advanced stuff look up Domoticz documentation.
description=                    ;self explanatory.
tempInput=                      ;Temperature devices need input units. Domoticz ALWAYS stores values as Celcius. Use: C, F, K and Blank for not temp device.
direction=out                   ;Are we getting putting data? For in & out on one device make 2 sections with the same index.
enabled=1                       ;set to zero for the plugin to ignore this device.

You can findou which CommandClass, endpoint, property and propertyKey values you need from the ZWaveJS2MQTT
control panel usually found at http://127.0.0.1:8091/control-panel on your server.

![This is how you tell the plugin which device/property you want to target](/ZWJS2MQTTWB.png)

# TODO
1: I'd like to add a way to translate inputs to different outputs using the ini file.  So a device changing its
   status to 1 equals a different input to the Domoticz device like to "Danny" for instance when you get a number
   in an update that represents a particular user who has logged into an external hardware.

2: Create a way to add and edit devices from the web UI.

3: Any other ideas people have to make this plugin more useful!  It could replace MQTT all together given enough
   input.

4: More kinds of input devices.

# Lastly
This plugin is in early developement.  If it doesn't work come back later. Also provide feed back if it
doesn't work so maybe it will next time!
   
