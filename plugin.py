# ZWaveJS2MQTT Websocket Bridge Plugin
#
# Author: Ittiz
#
"""
<plugin key="ZWaveJS2MQTTBridge" name="ZWaveJS2MQTT Websocket Bridge Plugin" author="Ittiz" version="0.1.0" externallink="https://github.com/Ittiz/ZWaveJSWSBridge">
    <description>
        <h2>ZWaveJS2MQTT Websocket Bridge Plugin</h2><br/>
        Websocket bridge between ZWaveJS2MQTT and Domoticz.
    </description>
    <params>
        <param field="Address" label="ZWaveJS2MQTT Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="ZWaveJS2MQTT Port" width="100px" required="true" default="3000"/>
    </params>
</plugin>
"""
import site

site.main()

import DomoticzEx as Domoticz

import importlib
import subprocess
from os.path import exists

# Importing the relevant libraries
import websockets
import asyncio
import threading
import json
import configparser

config = configparser.ConfigParser()
keepgoing=True
debug = False
# The main function that will handle connection and communication 
# with the server
async def listen():
    # Connect to the server/
    if debug:
        Domoticz.Log("Address: ws://"+str(Parameters["Address"]+":"+str(Parameters["Port"])))
    wsurl = "ws://"+str(Parameters["Address"]+":"+str(Parameters["Port"]))
    async with websockets.connect(wsurl) as ws:
        #async with connection as ws:
        msg = await asyncio.wait_for(ws.recv(),1)#we're not going to show this info
        #Domoticz.Log(msg)
        # Send a greeting message
        await asyncio.wait_for(ws.send('{"messageId": "start-listening-result", "command": "start_listening"}'),1)#This tells ZwaveJS2MQTT Websocket server we want updates about Zwave device status changes.
        #msg = await asyncio.wait_for(ws.recv(),1)#we're not going to show this info
        msg = await asyncio.wait_for(ws.recv(),1)#This is the initial state of all the nodes, lets ignore this for now.  TODO:  Check all the states for our devices and fix incorrect things!
        #Domoticz.Log(msg)
        config.read("plugins/ZWaveJSWSBridge/devices.ini")
        while keepgoing:
            try:
                msg = await asyncio.wait_for(ws.recv(),1)#this determines how long was wait for each request to time out. Last number is a timeout in seconds. This number*timer is how long the thread runs.  Should be less than heartbeat time which is 10 seconds.
                data = json.loads(msg)
                if debug:
                    Domoticz.Log("Update:"+str(msg))
                node = data['event']['nodeId']
                try:
                    commandclass = data['event']['args']['commandClassName']
                    propertyname = data['event']['args']['propertyName']
                except:
                    #Domoticz.Log("fail!")
                    commandclass = 0
                    propertyname = 0
                if debug:
                    Domoticz.Log("Node:"+str(node)+" Command Class:"+str(commandclass)+", "+" Property Name:"+str(propertyname))
                sectionsfound = 1
                i = 0
                while sectionsfound == 1 and commandclass != 0 and propertyname != 0:
                    if debug:
                        Domoticz.Log(str("Update node found in config!"))
                    nodeId = str(node)+"."+str(i)
                    enabled = int(config.get(nodeId, "enabled"))
                    pIndex = int(config.get(nodeId, "index"))
                    DeviceID="ZW2WSB-"+str(node)+"."+str(pIndex)
                    if debug:
                        Domoticz.Log("Info:"+str(pIndex)+", "+commandclass+", "+config.get(nodeId, "commandClass")+", "+propertyname+", "+config.get(nodeId, "property"))
                    if enabled == 1 and commandclass == config.get(nodeId, "commandClass") and propertyname == config.get(nodeId, "property"):#if it's not enabled we don't need to do anything.
                        if debug:
                            Domoticz.Log(str("Update property found in config!"))
                        try:
                            keyType = config.get(nodeId, "value")
                            try:
                                device = Devices[DeviceID].Units[pIndex]
                                if (keyType == "nValue"):
                                    Domoticz.Log("Update: "+str(config.get(nodeId, "name"))+", nValue: "+str(data['event']['args']['newValue']))
                                    device.nValue=int(data['event']['args']['newValue'])
                                elif (keyType == "sValue"):
                                    Domoticz.Log("Update: "+str(config.get(nodeId, "name"))+", sValue: "+str(data['event']['args']['newValue']))
                                    device.sValue=str(data['event']['args']['newValue'])
                                device.Update(Log=True)
                            except:
                                try:
                                    Domoticz.Log("Failed to update device! Is it new? Creating: "+str(config.get(nodeId, "name")))
                                    if (keyType == "nValue"):
                                        device = Domoticz.Unit(Name=str(config.get(nodeId, "name")), DeviceID=DeviceID, Unit=int(pIndex), Type=int(config.get(nodeId, "typeID")), Subtype=int(config.get(nodeId, "subTypeID")), Switchtype=int(config.get(nodeId, "switchTypeID")), Image=int(config.get(nodeId, "image")), Options=str(config.get(nodeId, "options")), Used=1, Description=str(config.get(nodeId, "description"))).Create()
                                    elif (keyType == "sValue"):
                                        device = Domoticz.Unit(Name=str(config.get(nodeId, "name")), DeviceID=DeviceID, Unit=int(pIndex), Type=int(config.get(nodeId, "typeID")), Subtype=int(config.get(nodeId, "subTypeID")), Switchtype=int(config.get(nodeId, "switchTypeID")), Image=int(config.get(nodeId, "image")), Options=str(config.get(nodeId, "options")), Used=1, Description=str(config.get(nodeId, "description"))).Create()
                                    i=i-1#we do this to catch the correct value on creation
                                except:
                                    Domoticz.Log("Failed to create device!")
                        except:
                            #Domoticz.Log(str(node)+"."+str(i))
                            sectionsfound = 0
                    i=i+1
                #Domoticz.Log(str(timer)+"-1")
            except:
                #Domoticz.Log(str(timer)+"-2")
                donothing=1
            loop.stop()

loop = asyncio.new_event_loop()
stop = False
def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen())
t = threading.Thread(target=start_background_loop, args=(loop,), daemon=False)

class BasePlugin:
    enabled = False

    def __init__(self):
        #self.var = 123
        return
    def onStart(self):
        t.start()#We spawn this in a different thread, otherwise Domoticz complains the thread is hung.
        #Once  the thread completes, hopefully in less than 10 seconds, we need to renew it on heartbeat.

    def onStop(self):
        #Domoticz.Log("onStop called")
        keepgoing=False

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called")#Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification Called")#Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        donothing=1
        #loop.run_until_complete(listen())


# Start the connection


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

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

#    # Generic helper functions
#def DumpConfigToLog():
#    for x in Parameters:
#        if Parameters[x] != "":
#            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
#    return