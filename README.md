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
First off! Turn on the websockets server in you ZWaveJS2MQTRT instance!  Make sure the plugin points to the
correct address and port number!  No Websockets equals no workie... :^( 
The devices.ini file defines the Zwave devices you want to create and how you interact with them.
You can find out which commandClass, endpoint, property and propertyKey values you need from the ZWaveJS2MQTT
control panel usually found at http://127.0.0.1:8091/control-panel on your server.  Devices are automatically
created once they're first seen by the Zwave hub.  Devices which are not enabled will be ignored and not
created until they are enabled.

![This is how you tell the plugin which device/property you want to target](/ZWJS2MQTTWB.png)

This is how you tell the plugin which device/property you want to target.

# TODO
1: Make translating inputs and outputs easier.  So if your input is not the same as your output it's easeir to
   convert between the two.

2: Create a way to add and edit devices from the web UI.

3: Any other ideas people have to make this plugin more useful!  It could replace MQTT all together given enough
   input.

4: More kinds of input devices.

# You Have Been Warned!
This plugin uses ASYNCIO and Threads.  Not only do these two libararies not play well with Domoticz, they don't
play well with each other either!  It works well with my setup when I follow the rules below.  Your setup IS
different than mine!  This may cause issues that I haven't encountered yet!  Issues equals Domoticz hanging up
the phone like an angry X.  You have been warned!

Issues:

1: ALWAYS STOP THIS PLUGIN BEFORE STOPPING YOUR ZWAVEJS2MQTT SERVER!

2: Stopping this plugin before restarting domoticz will help things restart faster.

3: So when adding a new device to ZWaveJS2MQTT, stop your Zwave hub, STOP THIS PLUGIN, add your new device to
ZWaveJS2MQTT, give the device the name you want in the ZWaveJS2MQTT control panel, restart your ZWaveJS2MQTT
server, identify any properties you want to add through this plugin from the new hardware and add them to the
devices.ini, restart your Zwave hub in Domoticz and FINALLY restart the plugin!

# Lastly
This plugin is in early developement.  If it doesn't work come back later. Also provide feed back if it
doesn't work so maybe it will next time!  If you want to issue a pull request please don't add you're
version of the devices.ini.  Leave the default one and add keys to it if your changes require new keys.
   
