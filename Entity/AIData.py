from dataclasses import dataclass


@dataclass
class AIData:
    acCurrentL1:float = None
    acCurrentL2:float = None
    acCurrentL3:float = None
    acCurrentLN:float = None
    acLineVoltageL1L2:float = None
    acLineVoltageL2L3:float = None
    acLineVoltageL3L1:float = None
    acActivePower:float = None
    acReactivePower:float = None
    powerFactor:float = None
    frequency:float = None
    acActiveEnergy:float = None
    irradiance:float = None
    windSpeed:float = None


    
if __name__ == "__main__":
    
    data = {
		"type": "dm",
		"objectID": "T7422",
		"acVoltageL1": 39625.2695,
		"acVoltageL2": 39726.9531,
		"acVoltageL3": 39252.9648,
		"acLineVoltageL1L2": 68815.8125,
		"acLineVoltageL2L3": 68476.5703,
		"acLineVoltageL3L1": 68192.7734,
		"acCurrentL1": 193.3008,
		"acCurrentL2": 188.8077,
		"acCurrentL3": 191.3091,
		"frequency": 59.9784,
		"acActivePowerL1": 7579055.7,
		"acActivePowerL2": 7417969.699999999,
		"acActivePowerL3": 7396247.999999999,
		"powerFactor1": -0.9895,
		"powerFactor2": -0.9891,
		"powerFactor3": -0.985,
		"powerFactor": -0.9879,
		"acActiveConsumptionEnergy": 80763488.0,
		"acActiveProductionEnergy": 675522.0,
		"acActiveEnergy": 81439008.0,
		"reactiveConsumptionEnergy": 7489795.0,
		"reactiveProductionEnergy": 10127267.0,
		"reactiveEnergy": 17617062.0,
		"deviceID": 14703,
		"time": 1667360100
	}
    # for key, value in data.items():
    #     if key in aiData.__dict__:
    #         aiData.__dict__[key] = value
    AIData(dict(filter(lambda x:AIData().__dict__, data.items())))
    getValue = list(filter(lambda x:x[0] in AIData().__dict__, data.items()))
    test = dict(filter(lambda x:x[0] in AIData().__dict__, data.items()))
    print("done")