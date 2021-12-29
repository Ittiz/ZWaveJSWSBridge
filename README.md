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
The devices.ini file defines the Zwave devices you want to create and how you interact with them.
You can find out which commandClass, endpoint, property and propertyKey values you need from the ZWaveJS2MQTT
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
   
