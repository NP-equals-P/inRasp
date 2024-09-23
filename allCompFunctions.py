import random
import serial

def dummyIni(iniVars, componentsDict):
    print("DummyIni")

    thisComp = "DummyData"

    componentsDict[iniVars[0]] = thisComp

    return

def randomRead(varList, compDict, mode, compId):
    if (mode == "start"):
        print("randomStart!")
        return 0
    elif (mode == "end"):
        print("randomEnd!")
        return 0
    else:
        print("randomRead!")
        return random.randint(0, 10)

def dummyKill(killVars, componentsDict):

    del componentsDict[killVars[0]]

    print(str(killVars[0]) + " morto!")

    return

# Medidor de Vazão de Gás, MFlow (M Lima Engenharia)

def iniMLimaFlow(iniVars, componentsDict):

    ser = serial.Serial(
    port=iniVars[1],\
    baudrate=9600,\
        timeout=0)
    
    componentsDict[iniVars[0]] = ser

    return 0

def readMLimaFlow(varList, compDict, mode, compId):
    
    if (mode == "start"):
        #MLima Flow does not need start function.
        return None
    elif (mode == "end"):
        #MLima Flow does not need end function.
        return None
    else:

        reading = str(compDict[compId].readline())
        readingLen = len(reading)

        count = -5
        lastReading = ""

        if (not readingLen == 3):
            while (reading[count] != "'" and reading[count] != ";"):
                lastReading = reading[count] + lastReading
                count -= 1

            print(float(lastReading))

            return float(lastReading)
        else:
            return None

def killMLimaFlow(killVars, componentsDict):

    componentsDict[killVars[0]].close()

    return

# -------------------------------------------------