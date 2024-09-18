import random
import serial

def other(varList, compDict, mode):
    print("other")
    return random.randint(0, 10)

def test(varList):
    print("test")
    return random.randint(0, 10)

def readMLimaFlow(varList, compDict, mode):
    
    if (mode == "start"):
        #MLima Flow does not need start function.
        return None
    elif (mode == "end"):
        #MLima Flow does not need end function.
        return None
    else:

        reading = str(compDict["test"].readline())
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
