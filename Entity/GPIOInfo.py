import sys
systemType = sys.argv[1].split("-")[1]
if systemType != "raspberry":
    import DebugGPIO as GPIO 
else:
    import RPi.GPIO as GPIO 

GPIO.setmode(GPIO.BCM)

class PinInfo():
    def __init__(self, number, mode, init = None):
        self.number = number
        if init != None:
            GPIO.setup(number, mode, initial = init)
        else:
            GPIO.setup(number, mode)

    def Set(self, state):
        GPIO.output(self.number, state)
        
    def Get(self):
        return GPIO.input(self.number)
        
class GPIOInfo():
    def __init__(self, boxType, nodeType):
        if boxType == "dual":
            if nodeType == "master":
                self.pinA = PinInfo(16, GPIO.OUT, GPIO.HIGH)
                self.pinB = PinInfo(12, GPIO.OUT)
                self.pinC = PinInfo(20, GPIO.IN)
            elif nodeType == "slave":
                self.pinA = PinInfo(16, GPIO.IN)
                self.pinB = PinInfo(12, GPIO.IN)
                self.pinC = PinInfo(20, GPIO.OUT, GPIO.HIGH)
        else:
            pass
        