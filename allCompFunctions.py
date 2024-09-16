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

    if (not readingLen == 3):
        return float(reading[2:-4])
    else:
        return None
