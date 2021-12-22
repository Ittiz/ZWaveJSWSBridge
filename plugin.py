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
import time
import queue

config = configparser.ConfigParser()

debug = True
# The main function that will handle connection and communication 
# with the server
async def listen():
    Domoticz.Log("Waiting 2 minutes to start Websocket connection!")
    time.sleep(120)#wait to start.  Onerous things will happen if you don't!  If ZWaveJS2MQTT isn't ready the whole thing hangs.
    # Connect to the server/
    if debug:
        Domoticz.Log("Connecting to address: ws://"+str(Parameters["Address"]+":"+str(Parameters["Port"])))
    try:
        wsurl = "ws://"+str(Parameters["Address"]+":"+str(Parameters["Port"]))
        async with websockets.connect(wsurl) as ws:
            #async with connection as ws:
            msg = await asyncio.wait_for(ws.recv(),1)#we're not going to show this info
            if debug:
                Domoticz.Log(msg)
            # Send a greeting message
            await asyncio.wait_for(ws.send('{"messageId": "start-listening-result", "command": "start_listening"}'),1)#This tells ZwaveJS2MQTT Websocket server we want updates about Zwave device status changes.
            msg = await asyncio.wait_for(ws.recv(),1)#This is the initial state of all the nodes, lets ignore this for now.  TODO:  Check all the states for our devices and fix incorrect things!
            #Domoticz.Log(msg)
            config.read("plugins/ZWaveJSWSBridge/devices.ini")
            while True:
                try:
                    #Domoticz.Log(str(WebSocketInput.empty()))
                    if WebSocketInput.empty() is False:
                        WSInput = WebSocketInput.get(block=True)
                        if WSInput is None:
                            if debug:
                                Domoticz.Log("Exiting input handler")
                            WebSocketInput.task_done()
                            loop.stop()#if we're in here the thread is going away so we add a precautionary stop of loop
                            break#Keep in mind that if the loop never gets here the thread never stops.
                        WebSocketInput.task_done()
                except:
                    if debug:
                        Domoticz.Log("No input for websocket in queue")
                try:
                    #Domoticz.Log("out")
                    msg = await asyncio.wait_for(ws.recv(),1)#ALWAYS put a timeout for "wait_for(..." or a dormant connection will cause the plugin to hang!
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
                                        i=i-1#we do this to catch the correct value from this update on creation
                                    except Exception as err:
                                        Domoticz.Error("Failed to create device! Error: "+str(err))
                            except:
                                if debug:
                                    Domoticz.Log("Node ID not in Config")
                        i=i+1
                except Exception as err:
                    if debug and len(str(err)) > 0:
                        Domoticz.Error("Listening loop: "+str(err))
                    #loop.stop()#if the websocket disconnects we can get stuck in here.  Lets shut this down.
                    #break
    except:
        if debug:
            Domoticz.Log("Failed to connect to WebSocket server!")
    #while loop.is_running() == False and BasePlugin.notStopping:#If anything at all causes this function to finish we need to stop the loop or Domoticz gets an upset tummy.
    #    try:   #So we wait for the kill signal that should come on the next heartbeat.
    #        if WebSocketInput.empty() is False:
    #            WSInput = WebSocketInput.get(block=True)
    #            if WSInput is None:
    #                if debug:
    #                    Domoticz.Log("Exiting input handler")
    #                WebSocketInput.task_done()
    #                loop.stop()#if we're in here the thread is going away so we add a precautionary stop of loop
    #                break#Keep in mind that if the loop never gets here the thread never stops.
    #            WebSocketInput.task_done()
    #    except:
    #        if debug:
    #            Domoticz.Log("No input for websocket in queue")

loop = asyncio.new_event_loop()#this stuff needs to be global because asyncio and threads don't play nice in Domoticz.  Maybe someone whos know more than me can figure this out?

def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen())

WebSocketInput = queue.Queue()    
t = threading.Thread(name="WebSocketLoop", target=start_background_loop, args=(loop,), daemon=False)

class BasePlugin:
    
    def __init__(self):
        #self.var = 123
        self.notStopping = True

    def onStart(self):
        t.start()#We spawn this in a different thread, otherwise Domoticz complains the plugin is hung when it's not.

    def onStop(self):
        self.notStopping = False
        if debug:
            Domoticz.Log("onStop called")
        WebSocketInput.put(None)
        WebSocketInput.join()
        while (threading.active_count() > 1):
            for thread in threading.enumerate():
                if (thread.name != threading.current_thread().name) and debug:
                    Domoticz.Log("'"+thread.name+"' is still running, waiting otherwise Domoticz will abort on plugin exit.")
            time.sleep(0.1)
        loop.stop()#IMPORTANT! async must stop after threads or they never get the stop command because the loop stops!
        #Domoticz.Log(str(loop.is_running())+" is running.")


    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue, Whatever):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + ", Hue: " + str(Hue) + ", Whatever: " + str(Whatever))#Domoticz.Log("onCommand called")#

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification Called")#Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        #Domoticz.Log(str(loop.running())+" is running.")
        #if loop.is_running() == False and self.notStopping: #Something happened. Attempt a restart!
        #    Domoticz.Log("Something disconnected the Websocket.  Attempting to reconnect!")
        #    WebSocketInput.put(None)#We need to send a kill signal to the thread.
        #    WebSocketInput.join()
        #    while (threading.active_count() > 1 and loop.is_running() == False and self.notStopping):
        #        for thread in threading.enumerate():
        #            if (thread.name != threading.current_thread().name) and debug:
        #                Domoticz.Log("'"+thread.name+"' is still running, waiting otherwise Domoticz will abort on plugin exit.")
        #        time.sleep(0.1)
        #    loop.stop()#IMPORTANT! async must stop after threads or they never get the stop command because the loop stops!
        #    t.start()#Attempt to restart the thread.
        if debug:
            Domoticz.Log(str(threading.active_count())+" threads running.")
            for thread in threading.enumerate():
                Domoticz.Log("'"+thread.name+"' is running.")


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

def onCommand(Unit, Command, Level, Hue, Whatever):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue, Whatever)

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