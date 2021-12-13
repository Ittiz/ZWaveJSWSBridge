# Domoticz-ZWaveJS2MQTT-Websocket-Bridge-Plugin
This project is to create a bridge for ZWaveJS2MQTT to Domoticz, for updates Domoticz doesn't know how to handle.

This project uses the Websockets server of ZWaveJS2MQTT to monitor updates from ZWaveJS2MQTT and transfer them to
devices in Domoticz.  The devices are set up in the devices.ini file and the plugin creates them when it receives
the request.  This is useful for cases where you have updates that domoticz doesn't understand by turning them
into a domoticz device through the ini file. See the devices.ini file for instructions on use. You can take 
something like Thermostat State, which is not handled in Domoticz, and turn it into a device which tells you that
your furnace is off or on.

Why'd I use Websocket instead of MQTT?  Two reasons: Websockets don't need a mosquitto server and I have more
experience with web sockets.

# Installation
If you don't know how already, wait for this plugin to be more developed!

# TODO
1: I'd like to add a way to translate inputs to different outputs using the ini file.  So a device changing its
   status to 1 equals a different input to the Domoticz device like to "Danny" for instance when you get a number
   in an update that represents a particular user who has logged into an external hardware.
2: Create a way to add and edit devices from the web UI.
3: Any other ideas people have to make this plugin more useful!  It could replace MQTT all together given enough
   input.
4: Communication is currently ONE way! From the device to the server only.  Out bound needs to be added as well.

# Lastly
	This plugin is in early developement.  If it doesn't work come back later. Also provide feed back if it
	doesn't work so maybe it will next time!
   
