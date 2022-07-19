# ZWaveJS2MQTT Websocket Bridge Plugin
#
# Author: Ittiz
#
"""
<plugin key="ZWaveJS2MQTTBridge" name="ZWaveJS2MQTT Websocket Bridge Plugin" author="Ittiz" version="0.1.1" externallink="https://github.com/Ittiz/ZWaveJSWSBridge">
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
import multiprocessing

config = configparser.ConfigParser()

debug = False#True

def fixtemp(direction,tempInput,newValue):#we need this in multiple places so it might as well be a function.
    if direction == "in":
        if str(tempInput) == "F" or str(tempInput) == "f":
            newValue = float(newValue)*(9/5)+32
        elif str(tempInput) == "K" or str(tempInput) == "k":
            newValue = float(newValue)+273.15
        else:
            newValue = float(newValue)
    else:
        if str(tempInput) == "F" or str(tempInput) == "f":
            newValue = (float(newValue)-32)*(5/9)
        elif str(tempInput) == "K" or str(tempInput) == "k":
            newValue = float(newValue)-273.15
        else:
            newValue = float(newValue)
    return newValue

# The main function that will handle connection and communication 
# with the server
async def listen():
    #Domoticz.Log("Waiting 30 seconds to start Websocket connection!")
    #time.sleep(30)#wait to start.  Onerous things will happen if you don't!  If ZWaveJS2MQTT isn't ready the whole thing hangs.
    # Connect to the server
    while True:#We can never safely leave here without a kill signal, so never let the loop stop even if we can't connect or the plugin will hang onstop
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
                msg = await asyncio.wait_for(ws.send('{"messageId": "start-listening-result", "command": "start_listening"}'),1)#This tells ZwaveJS2MQTT Websocket server we want updates about Zwave device status changes.
                if debug:
                    Domoticz.Log(msg)
                msg = await asyncio.wait_for(ws.recv(),1)#This is the initial state of all the nodes, lets ignore this for now.  TODO:  Check all the states for our devices and fix incorrect things!
                if debug:
                    Domoticz.Log(msg)
                try:
                    config.read("plugins/ZWaveJSWSBridge/devices.ini")#try and get our device info from the ini file.
                except Exception as err:
                    Domoticz.Error(str(err))
                while True:
                    try:#This is for inputting messages back to ZWaveJS2MQTT and also alerting the script the loop and thread need to stop.
                        #Domoticz.Log(str(WebSocketInput.empty()))
                        if WebSocketInput.empty() is False:
                            WSInput = WebSocketInput.get(block=True)
                            if WSInput is None:#kill signal has been issued!
                                if debug:
                                    Domoticz.Log("Exiting input handler")
                                WebSocketInput.task_done()#tell the Webocket server we're done here.
                                loop.stop()#if we're in here the thread is going away so we add a precautionary stop of loop
                                break#Keep in mind that if the loop never gets here the thread never stops. Kills the thread!
                            else:
                                try:
                                    await asyncio.wait_for(ws.send(WSInput),1)#This tells ZwaveJS2MQTT Websocket server we want to update a device.
                                    msg = await asyncio.wait_for(ws.recv(),1)#check to see if ZwaveJS2MQTT has a reply.
                                    if debug:
                                        Domoticz.Log(msg)
                                except Exception as err:
                                    Domoticz.Error(str(err))
                            WebSocketInput.task_done()#tell the Webocket server we're done here.
                    except:
                        if debug:
                            Domoticz.Log("No input for websocket in queue")
                    try:#This is where we get updates from ZwaveJS2MQTT and send them to our devices.
                        data = ""
                        try:
                            #msg = await asyncio.wait_for(ws.recv(),0.1)#ALWAYS put a timeout for "wait_for(..." or a dormant connection will cause the plugin to hang!
                            task = asyncio.create_task(ws.recv())                   #
                            done, pending = await asyncio.wait({task},timeout=0.1)  #We're doing this in a weird way due
                            if task in done:                                        #to a bug in Python that causes the
                                msg = task.result()                                 #plugin to crash on startup in some
                            data = json.loads(str(msg))                             #rare instances!
                        except Exception as err:                                    #See bug: https://github.com/python/cpython/issues/86296
                            pass                                                    #
                            #Domoticz.Error("Connection Error:"+str(err))
                            #await asyncio.sleep(1)
                        if debug:
                            Domoticz.Log(msg)
                        if (len(str(data)) > 0):
                            if debug:
                                Domoticz.Log("Update:"+str(msg))
                            node = data['event']['nodeId']
                            try:
                                commandclassName = data['event']['args']['commandClassName']
                                commandclass = data['event']['args']['commandClass']
                                propertyname = data['event']['args']['property']
                                newValue = data['event']['args']['newValue']
                                newValue2 = 0
                                endpoint = ""
                                try:
                                    endpoint = data['event']['args']['endpoint']
                                except:
                                    endpoint = 0
                                try:
                                    propertykey = int(data['event']['args']['propertyKey'])
                                except:
                                    propertykey = 0
                                try:
                                    isinstance(int(config.get(nodeId, "commandClass")),int)#hackish way to see if the user input the command class number rather than name
                                except:
                                    commandclass = commandclassName#json returned in update seperates the command class name and number but we can use either so lets use the one in the ini.
                            except:
                                #Domoticz.Log("fail!")
                                commandclass = None
                                propertyname = None
                                newValue = None
                            if debug:
                                Domoticz.Log("Node:"+str(node)+" Command Class:"+str(commandclass)+", Endpoint:"+str(endpoint)+", Property Name:"+str(propertyname)+", Property Key:"+str(propertykey))
                            sectionsfound = 1
                            i = 0
                            while sectionsfound == 1 and commandclass != None and propertyname != None and newValue != None:
                                if debug:
                                    Domoticz.Log(str("Update node found in config!"))
                                try:
                                    nodeId = str(node)+"."+str(i)
                                    enabled = int(config.get(nodeId, "enabled"))
                                    pIndex = int(config.get(nodeId, "index"))
                                    DeviceID="ZW2WSB-"+str(node)+"."+str(pIndex)
                                    tempInput = str(config.get(nodeId, "tempInput"))
                                    direction = str(config.get(nodeId, "direction"))
                                    typeId = int(config.get(nodeId, "typeID"))
                                    subTypeId = int(config.get(nodeId, "subTypeID"))
                                    switchTypeId = int(config.get(nodeId, "switchTypeID"))
                                    try:
                                        translation = eval(config.get(nodeId, "translations"))
                                    except:
                                        translation = {}
                                    #Domoticz.Log("Info:"+str(Devices[DeviceID]))
                                    if debug:
                                        Domoticz.Log("Info:"+str(pIndex)+", "+commandclass+", "+config.get(nodeId, "commandClass")+", "+str(endpoint)+", "+config.get(nodeId, "endpoint")+", "+propertyname+", "+config.get(nodeId, "property")+", "+str(propertykey)+", "+config.get(nodeId, "propertyKey"))
                                    if direction == "in":#This is for creating input devices.  We seperate the inputs from the outputs because we may want to send our commands to a seperate property or even command class than we recieved updates from.
                                        if debug:
                                            Domoticz.Log(str(config.get(nodeId, "options")))
                                        try:
                                            Devices[DeviceID]
                                        except:
                                            if enabled == 1:
                                                try:
                                                    Domoticz.Log("Creating new iput device: "+str(config.get(nodeId, "name")))
                                                    try:
                                                        device = Domoticz.Unit(Name=str(config.get(nodeId, "name")), DeviceID=DeviceID, Unit=int(pIndex), Type=int(config.get(nodeId, "typeID")), Subtype=int(config.get(nodeId, "subTypeID")), Switchtype=int(config.get(nodeId, "switchTypeID")), Image=int(config.get(nodeId, "image")), Options=eval(config.get(nodeId, "options")), Used=1, Description=str(config.get(nodeId, "description"))).Create()
                                                    except:
                                                        device = Domoticz.Unit(Name=str(config.get(nodeId, "name")), DeviceID=DeviceID, Unit=int(pIndex), Type=int(config.get(nodeId, "typeID")), Subtype=int(config.get(nodeId, "subTypeID")), Switchtype=int(config.get(nodeId, "switchTypeID")), Image=int(config.get(nodeId, "image")), Used=1, Description=str(config.get(nodeId, "description"))).Create()
                                                except Exception as err:
                                                    Domoticz.Error("Failed to create device! Error: "+str(err)+" node "+nodeId+" will be ignored")
                                                    sectionsfound = 0
                                    else:
                                        if enabled == 1 and commandclass == config.get(nodeId, "commandClass") and int(endpoint) == int(config.get(nodeId, "endpoint")) and str(propertyname) == str(config.get(nodeId, "property")) and (str(propertykey) == str(config.get(nodeId, "propertyKey")) or str(propertykey) == "0"):#if it's not enabled we don't need to do anything.
                                            if debug:
                                                Domoticz.Log(str("Update property found in config!"))
                                            try:
                                                keyType = config.get(nodeId, "value")
                                                try:
                                                    device = Devices[DeviceID].Units[pIndex]
                                                    if typeId == 242 or typeId == 80:#thermostats, thermometers ect
                                                        newValue = fixtemp(direction,tempInput,newValue)
                                                    elif typeId == 17 or typeId == 244:#some kind of switch
                                                        if subTypeId == 62 or switchTypeId == 18:#selector switch
                                                            Domoticz.Log("Update:"+str(msg))
                                                            keyType = "both"
                                                            newValue2 = 1
                                                            try:
                                                                newValue = int(translation[str(newValue)])
                                                            except:
                                                                newValue = str(translation[str(newValue)])
                                                            if newValue == 0:
                                                                newValue2 = 0
                                                    if (keyType == "nValue"):
                                                        Domoticz.Log("Update: "+str(config.get(nodeId, "name"))+", nValue: "+str(newValue))
                                                        device.nValue=int(newValue)
                                                    elif (keyType == "sValue"):
                                                        Domoticz.Log("Update: "+str(config.get(nodeId, "name"))+", sValue: "+str(newValue))
                                                        device.sValue=str(newValue)
                                                    elif (keyType == "both"):
                                                        Domoticz.Log("Update: "+str(config.get(nodeId, "name"))+", sValue: "+str(newValue))
                                                        Domoticz.Log("Update: "+str(config.get(nodeId, "name"))+", nValue: "+str(newValue2))
                                                        device.sValue=str(newValue)
                                                        device.nValue=int(newValue2)
                                                    device.Update(Log=True)
                                                except Exception as err:
                                                    Domoticz.Error(str(err))
                                                    try:
                                                        Domoticz.Log("Failed to update device! Is it new? Creating: "+str(config.get(nodeId, "name")))
                                                        i=i-1#we do this to catch the correct value from this update on creation
                                                        device = Domoticz.Unit(Name=str(config.get(nodeId, "name")), DeviceID=DeviceID, Unit=int(pIndex), Type=int(config.get(nodeId, "typeID")), Subtype=int(config.get(nodeId, "subTypeID")), Switchtype=int(config.get(nodeId, "switchTypeID")), Image=int(config.get(nodeId, "image")), Options=eval(config.get(nodeId, "options")), Used=1, Description=str(config.get(nodeId, "description"))).Create()
                                                    except Exception as err2:
                                                        Domoticz.Error("Failed to create device! Error: "+str(err)+" and "+str(err2)+" node "+nodeId+" will be ignored")
                                                        sectionsfound = 0
                                            except:
                                                if debug:
                                                    Domoticz.Log("Node "+nodeId+" not in Config")
                                except Exception as err:
                                    if debug:
                                        Domoticz.Error(str(err))
                                    sectionsfound = 0
                                    enabled=0
                                    commandclass = 0
                                    propertyname = 0
                                i=i+1
                    except Exception as err:
                        if debug and len(str(err)) > 0:
                            Domoticz.Error("Listening loop: "+str(err))
                        #loop.stop()#if the websocket disconnects we can get stuck in here.  Lets shut this down.
                        #break
        except Exception as err:
            Domoticz.Error("Failed to connect to WebSocket server: "+str(err))
            if WebSocketInput.empty() is False:
                WSInput = WebSocketInput.get(block=True)
                if WSInput is None:#kill signal has been issued!
                    if debug:
                        Domoticz.Log("Exiting input handler")
                    WebSocketInput.task_done()#tell the Webocket server we're done here.
                    loop.stop()#if we're in here the thread is going away so we add a precautionary stop of loop
                    break#Keep in mind that if the loop never gets here the thread never stops. Kills the thread!
                else:
                    Domoticz.Error("Can't accept input unless connected to the websocket.")
            time.sleep(2)#be nice, don't hammer the server if we can't connect
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
t = threading.Thread(name="ZWBWebSocketLoop", target=start_background_loop, args=(loop,), daemon=False)

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
        if (threading.active_count() > 1):
            WebSocketInput.put(None)
            WebSocketInput.join()
            while (threading.active_count() > 1):#if something went wrong with starting the thread trying to kill a non-existant thread will suck the fun out of this plugin.
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
        if debug:
            Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Command '" + str(Command) + "', Level: " + str(Level) + ", Hue: " + str(Hue) + ", Whatever: " + str(Whatever))#Domoticz.Log("onCommand called")#
        node = Unit[7:Unit.find(".",7)]
        try:
            config.read("plugins/ZWaveJSWSBridge/devices.ini")#try and get our device info from the ini file.
        except Exception as err:
            Domoticz.Error(str(err))
        #WebSocketInput.put('{"messageId": "Test_input" ,"command": "node.set_value", "nodeId": 19, "valueId": {"commandClass": 37, "property": "targetValue"}, "value":false}')
        sectionsfound = 1
        i = 0
        while sectionsfound == 1:
            if debug:
                Domoticz.Log(str("Input node found in config!"))
            try:
                nodeId = str(node)+"."+str(i)
                enabled = int(config.get(nodeId, "enabled"))
                pIndex = int(config.get(nodeId, "index"))
                tempInput = str(config.get(nodeId, "tempInput"))
                direction = str(config.get(nodeId, "direction"))
                commandClass = str(config.get(nodeId, "commandClass"))
                prop = str(config.get(nodeId, "property"))
                typeId = int(config.get(nodeId, "typeID"))
                subTypeId = int(config.get(nodeId, "subTypeID"))
                switchTypeId = int(config.get(nodeId, "switchTypeID"))
                try:
                    translation = eval(config.get(nodeId, "translations"))
                except:
                    translation = {}
                #Domoticz.Log("Info:"+str(Devices[DeviceID]))
                OPvalue = ""
                if direction == "in" and enabled == 1 and str(Command) == str(pIndex):
                    try:
                        endpoint = int(config.get(nodeId, "endpoint"))
                    except:
                        endpoint = None
                    try:
                        propertykey = int(config.get(nodeId, "propertyKey"))
                    except:
                        propertykey = None
                    message = '{"messageId": "'+str(Unit)+'_input" ,"command": "node.set_value", "nodeId": '+str(node)+', "valueId": {"commandClass": '
                    try:
                        isinstance(int(commandClass),int)#hackish way to see if the user input the command class number rather than name
                        message = message+str(commandClass)#if a number is input we don't need the quotes in the json.
                    except:
                        message = message+'"'+str(commandClass)+'"'
                    if endpoint != None:
                        message = message + ', "endpoint": '+str(endpoint)
                    try:
                        isinstance(int(prop),int)#hackish way to see if the user input the command class number rather than name
                        message =  message + ', "property": '+str(prop)#if a number is input we don't need the quotes in the json.
                    except:
                        message =  message + ', "property": "'+str(prop)+'"'
                    if propertykey != None:
                        message = message + ', "propertyKey": '+str(propertykey)
                    if typeId == 242:#thermostat
                        OPvalue = int(round(float(Hue)))#Domoticz can do half degrees, some thermostats don't like this.
                    elif typeId == 17 or typeId == 244:#some kind of switch
                        if subTypeId == 62 or switchTypeId == 18:#selector switch
                            try:
                                OPvalue = int(translation[str(Hue)])
                            except:
                                OPvalue = '"'+str(translation[str(Hue)])+'"'
                        elif subTypeId == 73:#Not a selector switch
                            if switchTypeId == 0:#An ordinary on/off type switch
                                if Level == "On":
                                    OPvalue = 1
                                else:
                                    OPvalue = 0
                        else:
                            Domoticz.Error("Unknown switch device subtype: "+subTypeId)
                    else:
                        Domoticz.Error("Unknown input Type: "+str(typeId)+", Sub Type: "+str(subTypeId)+", Switch Type: "+str(switchTypeId))
                    message = message+'}, "value": '+str(OPvalue)+'}'
                    if debug:
                        Domoticz.Log("Message Input: "+message)
                    Domoticz.Log("Updating "+str(Unit)+" to "+str(OPvalue))
                    WebSocketInput.put(message)#send our device update to our websocket thread handle.
                    WebSocketInput.put('{"messageId": "'+str(Unit)+'_refresh" ,"command": "node.refresh_values", "nodeId": '+str(node)+'}')#we need to request an update to the values incase this is set-only and our feed back comes from a read-only property.
            except Exception as err:
                if debug:
                    Domoticz.Error(str(err))
                sectionsfound = 0
                enabled=0
                commandclass = 0
                propertyname = 0
            i=i+1

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification Called")#Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        #try:
        #    config.read("plugins/ZWaveJSWSBridge/devices.ini")
        #    isinstance(int(config.get("6.1", "commandClass")),int)
        #except Exception as err:
        #    Domoticz.Error(str(err))
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