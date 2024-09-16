import random
import serial

def other(varList):
    print("other")
    return random.randint(0, 10)

def test(varList):
    print("test")
    return random.randint(0, 10)

def readMLimaFlow(varList, ser):
    
    reading = str(ser.readline())
    readingLen = len(reading)

    count = -5
    lastReading = ""

    if (not readingLen == 3):
        while (reading[count] != "'" and reading[count] != ";"):
            lastReading = reading[count] + lastReading
            count -= 1

        return float(lastReading)
    else:
        return None
