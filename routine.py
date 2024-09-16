from pymongo import MongoClient
from bson import ObjectId
import time
from datetime import datetime
import allCompFunctions
from allCompFunctions import *

ser = serial.Serial(
port='COM7',\
baudrate=9600,\
    timeout=0)

def connectToDB(): #TODO: Change to real DB.
    urlString = "mongodb+srv://ito:senhaito@cluster0.2muvzud.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" #TODO: Make it safe! 
    client = MongoClient(urlString)
    db = client["test"]

    return db

def readReactorId(): #TODO: Change! This is a SUPER manual aproach. Can do better.
    return "66df3a313448c96e40c0c8bf"

def checkActive(reactorId, db):

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

    normalInfo = []

    thisReactor = reactorsDB.find_one({"_id": ObjectId(reactorId)})

    activeRoutine = routinesDB.find_one({"_id": thisReactor["activeRoutine"]})

    for eventId in activeRoutine["events"]:
        event = eventsDB.find_one({"_id": eventId})
        auxList = []

        for actionId in event["actions"]:
            action = actionsDB.find_one({"_id": actionId})
            auxList.append(action)
        
        normalInfo.append((event, auxList))

    for eventId in activeRoutine["esporadicEvents"]:
        event = eventsDB.find_one({"_id": eventId})
        auxList = []

        for actionId in event["actions"]:
            action = actionsDB.find_one({"_id": actionId})
            auxList.append(action)
        
        normalInfo.append((event, auxList)) 

    return normalInfo

def calcRoutDuration(info):

    max = 0

    for node in info:

        eventDuration = int(node[0]["end"])

        if (eventDuration > max and node[0]["type"] == "normal"): #TODO: Change this after server fix.

            max = eventDuration

    return max

def fillPool(info, rotuineDuration):
    eventPool = [] #All events that should be checked every routine cycle.
    actionPool = [] #All actions that should be checked every routine cycle.

    for node in info:

        event = node[0]
        actionList = node[1] #Actions of node[0] event.

        if (event['type'] == "esporadic"):
            
            event["status"] = "suspended"

            for action in actionList:
                action["status"] = 'suspended'
        elif (event["start"] == 0 and event["end"] == rotuineDuration):
            
            event["status"] = "permanent"

            for action in actionList:

                if (action["start"] == 0 and action["end"] == rotuineDuration):
                    action["status"] = "permanent"
                else:
                    action["status"] = 'on'
        else:
            event["status"] = "on"

            for action in actionList:
                action["status"] = "on"

    return info

def startRun(reactorId, db):
    reactors = db["reactors"]
    runs = db["runs"]

    newRun = {"log": [], "startDate": datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}

    _id = runs.insert_one(newRun)

    query = {"_id": ObjectId(reactorId)}
    update = {"$push": {"runs": _id.inserted_id}, "$set": {"activeRun": _id.inserted_id}}

    x = reactors.update_one(query, update)

    db.create_collection("z_runTS[" + str(_id.inserted_id) + "]", timeseries={ 'timeField': 'whenTaken', 'metaField': "sensorId"})

    return _id.inserted_id

def logReacActivation(db, activeRunId, thisReactorId):
    runs = db["runs"]
    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(thisReactorId)})

    now = datetime.now()
    query = {"_id": ObjectId(activeRunId)}

    update = {"$push": {"log": f"[Reactor] {thisReactor['name']} activated. [Real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
    runs.update_one(query, update)
    return

def logReacDesactivation(db, activeRunId, thisReactorId, sec):
    runs = db["runs"]
    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(thisReactorId)})

    now = datetime.now()
    query = {"_id": ObjectId(activeRunId)}

    update = {"$push": {"log": f"[Reactor] {thisReactor['name']} desactivated. [Routine time: {sec} / real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
    runs.update_one(query, update)
    return

def logReacPause(db, activeRunId, thisReactorId, sec):
    runs = db["runs"]
    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(thisReactorId)})

    now = datetime.now()
    query = {"_id": ObjectId(activeRunId)}

    update = {"$push": {"log": f"[Reactor] {thisReactor['name']} paused. [Routine time: {sec} / real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
    runs.update_one(query, update)
    return

def logReacResume(db, activeRunId, thisReactorId):
    runs = db["runs"]
    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(thisReactorId)})

    now = datetime.now()
    query = {"_id": ObjectId(activeRunId)}

    update = {"$push": {"log": f"[Reactor] {thisReactor['name']} resumed. [Real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
    runs.update_one(query, update)
    return

def startRoutine(checkPool, db, activeRunId):

    for node in checkPool:

        event = node[0]
        actions = node[1]
            
        if (event['status'] == "permanent"):

            logEventChange(event['name'], "start", 0, db, activeRunId)

        for action in actions:

            if (action['status'] == "permanent"):

                # callAction() TODO

                logActionChange(action['name'], "start", 0, event['name'], db, activeRunId)

def callAction(funcId, varList, db, mode):

    functionsDB = db["functions"]

    thisFunction = functionsDB.find_one({"_id": funcId})

    func = getattr(allCompFunctions, thisFunction['name'])

    if (mode == "start"):
        ret = func(varList, ser)
    else:
        endVars = thisFunction["endVars"]
        ret = func(endVars)

    return ret
    
def logEventChange(name, mode, sec, db, activeRunId):
    runs = db["runs"]

    now = datetime.now()
    query = {"_id": ObjectId(activeRunId)}

    match mode:
        case "start":
            update = {"$push": {"log": f"[Event] {name} started. [Routine time: {sec} / real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
            runs.update_one(query, update)
            return
        case "end":
            update = {"$push": {"log": f"[Event] {name} ended. [Routine time: {sec} / real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
            runs.update_one(query, update)
            return

def logActionChange(name, mode, sec, event, db, activeRunId):
    runs = db["runs"]

    now = datetime.now()
    query = {"_id": ObjectId(activeRunId)}

    match mode:
        case "start":
            update = {"$push": {"log": f"[Action] {name} started (From [Event] {event}). [Routine time: {sec} / real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
            runs.update_one(query, update)
            return
        case "end":
            update = {"$push": {"log": f"[Action] {name} ended (From [Event] {event}). [Routine time: {sec} / real time: {now.strftime('%m/%d/%Y, %H:%M:%S')}]"}}
            runs.update_one(query, update)
            return

def checkPause(reactorId, db):

    reactorsDB = db["reactors"]

    thisReactor = reactorsDB.find_one({"_id": ObjectId(reactorId)})

    if (bool(thisReactor["isPaused"])):
        return True
    else:
        return False

def isRegularCall(action, db):

    functions = db["functions"]

    function = functions.find_one({"_id": ObjectId(action["function"])})

    return function["isRegular"]

def followRoutine(checkPool, cycleStartTime, routineDuration, db, activeRunId):

    timeSeries = db["z_runTS[" + str(activeRunId) + "]"]

    timePassed = (datetime.now() - cycleStartTime).seconds

    for node in checkPool:
        event = node[0]
        actions = node[1]

        if (not (event['status'] == "suspended")): 
            if (event['status'] == "on" and timePassed == event['end']):
                logEventChange(event['name'], "end", timePassed, db, activeRunId)

            for action in actions:
                if (action['status'] == "on" and timePassed == action['end']):
                    logActionChange(action['name'], "end", timePassed, event['name'], db, activeRunId)
                    callAction(action["function"], action["varList"], db, "end")

    if (timePassed >= routineDuration):
        cycleStartTime = datetime.now()
        timePassed = 0

    for node in checkPool:
        event = node[0]
        actions = node[1]

        if (not (event['status'] == "suspended")): 
            if (event['status'] == "on" and timePassed == event['start']):
                logEventChange(event['name'], "start", timePassed, db, activeRunId)

            for action in actions:
                if (action['status'] == "on" and timePassed == action['start']):
                    logActionChange(action['name'], "start", timePassed, event['name'], db, activeRunId)
                    callAction(action["function"], action["varList"], db, "start")

    for node in checkPool:
        event = node[0]
        actions = node[1]

        if (not (event['status'] == "suspended")): 
            for action in actions:
                if (timePassed > action['start'] and timePassed < action['end']):
                    if (isRegularCall(action, db) and timePassed%action["frequency"] == 0):
                        readValue = callAction(action["function"], action["varList"], db, "start")
                        if (action["type"] == "sensor"):
                            if (readValue != None):
                                timeSeries.insert_one({"whenTaken": datetime.now(), "sensorId": action["component"], "value": readValue})
                            else:
                                query = timeSeries.find({}, {"sort": {"timestamp": -1}, "limit": 1})
                                for doc in query:
                                    resolvedDoc = timeSeries.find_one({"_id": doc['_id']})
                                    print(resolvedDoc["value"])
                                    timeSeries.insert_one({"whenTaken": datetime.now(), "sensorId": action["component"], "value": resolvedDoc["value"]})

    return cycleStartTime, timePassed






def checkEsporadics(info, espCheckPool):
    return








def main():

    db = connectToDB()

    while (True): #Once started, runs forever until Rasp is turned off or the app is shut down.

        firstRoutCycle = True
        desactivationFlag = False
        pauseFlag = False
        cycleRelativeTime = 0 #Counts whole seconds after last routine cycle start.
        cycleStartTime = datetime.now() #Last routine cycle start time.

        thisReactorId = readReactorId() #Every unactive cycle reads possible new reac Id.

        while (checkActive(thisReactorId, db)):

            if (firstRoutCycle):

                eventsList = getActiveRoutInfo(thisReactorId, db) #Only updates routine info after activation.
                rotuineDuration = calcRoutDuration(eventsList)
                checkPool = fillPool(eventsList, rotuineDuration)

                activeRunId = startRun(thisReactorId, db)

                logReacActivation(db, activeRunId, thisReactorId) #Logs reactor activation.
                desactivationFlag = True

                startRoutine(checkPool, db, activeRunId)

                firstRoutCycle = False

            while (not checkPause(thisReactorId, db) and checkActive(thisReactorId, db)):

                if (pauseFlag): #Logs reactor resume if it happened.
                    pauseFlag = False
                    logReacResume(db, activeRunId, thisReactorId)

                # checkEsporadics(checkPool)

                cycleStartTime, cycleRelativeTime = followRoutine(checkPool, cycleStartTime, rotuineDuration, db, activeRunId)

                time.sleep(1)

            if (checkPause(thisReactorId, db) and not (pauseFlag)): #Logs reactor pause if it happened.
                pauseFlag = True
                logReacPause(db, activeRunId, thisReactorId, cycleRelativeTime)

        if (desactivationFlag): #Logs reactor desactivation if it happened.
            desactivationFlag = False
            logReacDesactivation(db, activeRunId, thisReactorId, cycleRelativeTime)


main()