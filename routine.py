from pymongo import MongoClient
from bson import ObjectId
import time
from datetime import datetime
from allCompFunctions import *

def connectToDB(): #TODO: Change to real DB.
    urlString = "mongodb+srv://ito:senhaito@cluster0.2muvzud.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" #TODO: Make it safe! 
    client = MongoClient(urlString)
    db = client["test"]

    return db

def readReactorId(): #TODO: Change! This is a SUPER manual aproach. Can do better.
    return "66a29f2ba0652cc21393044f"

def checkActive(reactorId, db): #TODO: Explore new alternatives. Communication through DB is kinda bad.

    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(reactorId)})

    if (bool(thisReactor["isActive"])):
        return True
    else:
        return False

def getActiveRoutInfo(reactorId, db):

    reactorsDB = db["reactors"]
    routinesDB = db["routines"]
    eventsDB = db["events"]
    actionsDB = db["actions"]

    info = []

    thisReactor = reactorsDB.find_one({"_id": ObjectId(reactorId)})

    activeRoutine = routinesDB.find_one({"_id": thisReactor["activeRoutine"]})

    for eventId in activeRoutine["events"]:
        event = eventsDB.find_one({"_id": eventId})
        auxList = []

        for actionId in event["actions"]:
            action = actionsDB.find_one({"_id": actionId})
            auxList.append(action)
        
        info.append((event, auxList))

    return info

def calcRoutDuration(info):

    max = 0

    for node in info:

        eventDuration = int(node[0]["start"]) + int(node[0]["duration"])

        if (eventDuration > max and node[0]["type"] == "normal"): #TODO: Change this after server fix.

            max = eventDuration

    return max

def fillPool(info, rotuineDuration):
    eventPool = [] #All events that should be checked every routine cycle.
    actionPool = [] #All actions that should be checked every routine cycle.

    for node in info:

        event = node[0]
        actionList = node[1] #Actions of node[0] event.

        print(event["duration"], event["start"])

        if (event['type'] == "esporadic"): #TODO: Put this whole If statement in server side.
            
            event["callType"] = "esporadic"

            for action in actionList:

                action["absoluteStart"] = action["start"] + event["start"]
                action["absoluteEnd"] = action["absoluteStart"] + action["duration"]
                action["callType"] = 'esporadic'
                actionPool.append(action)
        elif (event["start"] == 0 and event["duration"] == rotuineDuration):
            
            event["callType"] = "permanent"

            for action in actionList:

                if (action["start"] == 0 and action["duration"] == rotuineDuration):
                    
                    action["callType"] = "permanent"
                else:
                    action["callType"] = 'normal'
                    action["absoluteStart"] = action["start"] + event["start"]
                    action["absoluteEnd"] = action["absoluteStart"] + action["duration"]

                actionPool.append(action)
        else:
            event["callType"] = "normal"

            for action in actionList:

                action["absoluteStart"] = action["start"] + event["start"]
                action["absoluteEnd"] = action["absoluteStart"] + action["duration"]
                action["callType"] = "normal"
                actionPool.append(action)

        eventPool.append(event)

    return (eventPool, actionPool)

def startRoutine(checkPool):

    events = checkPool[0]
    actions = checkPool[1]

    for event in events:
        
        if (event['callType'] == "permanent"):

            logEventChange(event['name'], "start", 0)

    for action in actions:

        if (action['callType'] == "permanent"):

            # callAction() TODO

            logActionChange(action['name'], "start", 0)

def callAction(): #TODO: Call action function.
    return
    
def logEventChange(name, mode, sec): #TODO: True log in DB. Also log real time.

    match mode:
        case "start":
            print(f"[Event] {name} started. (In routine: {sec} / real time:)")
            return
        case "end":
            print(f"[Event] {name} ended. (In routine: {sec} / real time:)")
            return

def logActionChange(name, mode, sec, event): #TODO: True log in DB. Also log real time.
    match mode:
        case "start":
            print(f"[Action] {name} started (From [Event] {event}). [In routine: {sec} / real time:]")
            return
        case "end":
            print(f"[Action] {name} ended (From [Event] {event}). [In routine: {sec} / real time:]")
            return

def checkPause(reactorId, db): #TODO: Change this just like checkActive

    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(reactorId)})

    if (bool(thisReactor["isPaused"])):
        return True
    else:
        return False







def checkEsporadics(info, espCheckPool):
    return

def followRoutine(checkPool, espCheckPool, moduloSec):
    return







def main():

    db = connectToDB()

    while (True): #Once started, runs forever until Rasp is turned off or the app is shut down.

        firstRoutCycle = True
        moduloSec = 0 #Seconds in routine modulo routine's full duration.

        thisReactorId = readReactorId() #Every unactive cycle reads possible new reac Id.

        while (checkActive(thisReactorId, db)):

            if (firstRoutCycle):

                activeRoutInfo = getActiveRoutInfo(thisReactorId, db) #Only updates routine info after activation.
                rotuineDuration = calcRoutDuration(activeRoutInfo)
                checkPool = fillPool(activeRoutInfo, rotuineDuration)

                startRoutine(checkPool)

                firstRoutCycle = False

            while (not checkPause(thisReactorId, db) and checkActive(thisReactorId, db)):

                checkEsporadics(checkPool)

                # moduloSec = followRoutine(checkPool, moduloSec)

                print() #TODO: TEST ONLY. REMOVE THIS

                time.sleep(1) #TODO: Change! Routine functions can desincronize everything.
                moduloSec += 1

main()