class AIData():
	def __init__(self,
              acCurrentL1:float = None, 
              acCurrentL2:float = None,
              acCurrentL3:float = None,
              acCurrentLN:float = None,
              acLineVoltageL1L2:float = None,
              acLineVoltageL2L3:float = None,
              acLineVoltageL3L1:float = None,
              acActivePower:float = None,
              acReactivePower:float = None,
              powerFactor:float = None,
              frequency:float = None,
              acActiveEnergy:float = None,
              irradiance:float = None,
              windSpeed:float = None):
		self.acCurrentL1 = acCurrentL1 * 10 if acCurrentL1 != None else  None
		self.acCurrentL2 = acCurrentL2 * 10 if acCurrentL2 != None else  None
		self.acCurrentL3 = acCurrentL3 * 10 if acCurrentL3 != None else  None
		self.acCurrentLN = acCurrentLN * 10 if acCurrentLN != None else  None
		self.acLineVoltageL1L2 = acLineVoltageL1L2 * 100 if acLineVoltageL1L2 != None else  None
		self.acLineVoltageL2L3 = acLineVoltageL2L3 * 100 if acLineVoltageL2L3 != None else  None
		self.acLineVoltageL3L1 = acLineVoltageL3L1 * 100 if acLineVoltageL3L1 != None else  None
		self.acActivePower = acActivePower
		self.acReactivePower = acReactivePower
		self.powerFactor = powerFactor * 100 if powerFactor != None else  None
		self.frequency = frequency * 10 if frequency != None else  None
		self.acActiveEnergy = acActiveEnergy * 1000 if acActiveEnergy != None else  None
		self.irradiance = irradiance
		self.windSpeed = windSpeed