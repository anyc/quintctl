#!/usr/bin/env python3
#
# Author: Mario Kicherer (dev@kicherer.org)
#

import argparse, sys, time
from datetime import datetime

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus.transaction import ModbusRtuFramer

# from official modbus documentation
# unsign 16
Quint24DCRegisters = {
	"OUT_LX_Remote": {
		"addr": 0x7400,
		"type": "bool",
		"values": {
			0: "on",
			1: "off",
			},
		},
	"OUT_LX_BatteryMode": {
		"addr": 0x7401,
		"type": "bool",
		},
	"OUT_LX_ShutdownEvent": {
		"addr": 0x7402,
		"type": "bool",
		},
	"OUT_LX_BatteryCharging": {
		"addr": 0x7403,
		"type": "bool",
		},
	"OUT_LUI_PowerSourceBoost": {
		"addr": 0x7406,
		"type": "state",
		"values": {
			0: "I > Inominal",
			1: "I < Inominal",
			2: "not connected",
			}
		},
	"OUT_LUI_OutputVoltage": {
		"addr": 0x7431,
		"type": "int",
		"unit": "mV",
		"max": 30000,
		},
	"OUT_LUI_SocStateOfCharge": {
		"addr": 0x7435,
		"type": "int",
		"unit": "%",
		"values": {
			65535: "not initialized",
			}
		},
	"OUT_LUI_SocStateResidualBackupTime": {
		"addr": 0x7436,
		"type": "int",
		"unit": "minutes",
		"values": {
			65535: "not initialized",
			}
		},
	"OUT_LUI_BatteryVoltage": {
		"addr": 0x7460,
		"type": "int",
		"unit": "mV",
		"max": 30000,
		},
	"OUT_LUI_BatteryTemperature": {
		"addr": 0x7461,
		"type": "int",
		"unit": "Kelvin",
		"min": 200,
		"max": 400,
		},
	"OUT_LUI_OutputVoltage2": {
		"addr": 0x7462,
		"type": "int",
		"unit": "mV",
		"max": 3000,
		},
	"OUT_LUI_SocStateResidualBackupTimeS": {
		"addr": 0x7463,
		"type": "int",
		"unit": "seconds",
		"values": {
			65535: "not initialized",
			}
		},
	"OUT_LUDI_BatteryNormCapacityWs": {
		"addr": 0x7464,
		"type": "int",
		"unit": "100Ws",
		"values": {
			65535: "not detected",
			}
		},
	"OUT_LUI_BatteryDischaCurrent": {
		"addr": 0x7466,
		"type": "int",
		"unit": "mA",
		},
	"OUT_LUI_BatteryDetectedUnits": {
		"addr": 0x7467,
		"type": "int",
		"max": 15,
		},
	"OUT_LUDI_BatteryNormCapacitymAh": {
		"addr": 0x7468,
		"type": "int",
		"unit": "100mAh",
		"values": {
			65535: "not detected",
			}
		},
	"OUT_LUI_BatteryInstalledType": {
		"addr": 0x7469,
		"type": "state",
		"values": lambda value: "Capacitor" if value > 18000 else "Lithium battery" if value > 11000 else "Lead battery" if value > 1000 else "unknown"
		},
	"OUT_LUDW_ActualAlarm": {
		"addr": 0x7490,
		"type": "bits",
		"length": 2,
		"bits": {
			0: "end of life (SOH)",
			4: "end of life (Resistance)",
			5: "end of life (Resistance)",
			6: "end of life (Time)",
			7: "end of life (Voltage)",
			9: "no battery",
			10: "inconsistent technology",
			11: "overload cutoff",
			12: "low battery (Voltage)",
			13: "low battery (Charge)",
			14: "low battery (Time)",
			16: "service",
			}
		},
	"OUT_LUDW_ActualWarning": {
		"addr": 0x7494,
		"type": "bits",
		"bits": {
			0: "end of life (SOH)",
			7: "inconsistent capacity",
			8: "notify more batteries",
			8: "less batteries",
			12: "low battery (Voltage)",
			13: "low battery (Charge)",
			14: "low battery (Time)",
			15: "service without battery registration",
			}
		},
	}

# from XML in the driver package
# 0x0000 Vendor
# 0x1000 Konfiguration
# 0x3000 Parametrierung
# 0x6C00 Statusdaten
# 0x7400 I/O-Daten
# 0x7800 Steuerregister
Quint24DCRegisters.update({
	#
	# 0x1000
	#
	
	"FW_VERSION": {
		"addr": 0x1602,
		},
	"BAT_INSTALLED_CAPACITY_NOMINAL": {
		"addr": 0x1611,
		"unit": "100mAh",
		},
	
	#
	# 0x3000
	#
	
	"TIME_LIMIT_MODE_CUSTOM_BUFFER_TIME": {
		"addr": 0x3203,
		"mode": "rw",
		"description": "seconds after power loss until output voltage is turned off (in custom mode only)",
		},
	
	#
	# 0x6000
	#
	
	"COUNTER_BATTERY_MODE_EVENT": {
		"addr": 0x6C00,
		"length": 2,
		},
	"COUNTER_OPERATION_TIME": {
		"addr": 0x6c0c,
		"length": 2,
		},
	"COUNTER_USER_OPERATION_TIME": {
		"addr": 0x6c10,
		"length": 2,
		},
	
	#
	# 0x7400
	#
	
	"STATUS_SERVICE":  {
		"addr": 0x7405,
		"values": {
			0: "not in service mode",
			1: "service mode by key",
			2: "service mode by stick",
			3: "service mode by PC",
			},
		},
	"INPUT_ACTUAL_VOLTAGE": {
		"addr": 0x7430,
		"type": "int",
		"unit": "mV",
		},
	"ACTUAL_CURRENT_CHARGING": {
		"addr": 0x7465,
		"type": "int",
		"unit": "mA",
		},
	"BATTERY_ACTUAL_TEMPERATURE": {
		"addr": 0x7473,
		"type": "int",
		"unit": "Kelvin",
		},
	"BATTERY_ACTUAL_ALL_VOLTAGE": {
		"addr": 0x7472,
		"type": "int",
		"unit": "mV",
		},
	"BATTERY_ACTUAL_INTERNAL_VOLTAGE": {
		"addr": 0x7477,
		"type": "int",
		"unit": "mV",
		},
	"ERROR_CODE_COUNTER": {
		"addr": 0x749A,
		},
	
	#
	# 0x7800
	#
	
	"SET_SERVICE_MODE_BY_PC": {
		"addr": 0x7873,
		},
	})

Quint24DCMonitorRegisters = [
	(0x6c00, 0x6c50),
	(0x7400, 0x74a0),
	(0x7800, 0x78a0),
	]

default_skip = [
	"COUNTER_OPERATION_TIME",
	"COUNTER_USER_OPERATION_TIME",
	"INPUT_ACTUAL_VOLTAGE",
	"BATTERY_ACTUAL_INTERNAL_VOLTAGE",
	"OUT_LUI_OutputVoltage",
	
	# looks like most of them are actual current, voltage or temperature registers
	0x740b,
	0x740c,
	0x740d,
	0x7432,
	0x743c,
	0x743d,
	0x746c,
	0x7478,
	]

class QuintUPS():
	def __init__(self):
		self.slave_id = 192
		self.baudrate = 115200
	
	def connect(self, device):
		self.mbclient = ModbusSerialClient(
				device,
				framer=ModbusRtuFramer,
				baudrate=self.baudrate,
				bytesize=8,
				parity="E",
				stopbits=1,
			)
		
		self.mbclient.connect()
	
	def __del__(self):
		self.mbclient.close()
	
	def readRegister(self, addr, count=1):
		if count == 0:
			#count = 0x7d
			count = 0x10
		
		try:
			resp = self.mbclient.read_input_registers(addr, count, slave=self.slave_id)
		except ModbusException as e:
			print(f"Received ModbusException({e}) from library")
			self.mbclient.close()
			return None

		if resp.isError():
			print(f"Received Modbus library error({resp})")
			self.mbclient.close()
			return None

		if isinstance(resp, ExceptionResponse):
			print(f"Received Modbus library exception ({resp})")
			# THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
			self.mbclient.close()
			return None
		
		return resp.registers
	
	def writeRegister(self, addr, value):
		try:
			# using write_register() results in illegalfunction exception
			resp = self.mbclient.write_registers(addr, [value], slave=self.slave_id)
		except ModbusException as e:
			print(f"Received ModbusException({e}) from library")
			self.mbclient.close()
			return None

		if resp.isError():
			print(f"Received Modbus library error({resp})")
			self.mbclient.close()
			return None

		if isinstance(resp, ExceptionResponse):
			print(f"Received Modbus library exception ({resp})")
			# THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
			self.mbclient.close()
			return None
		
		return True

def print_value(info, values, prefix=""):
	if isinstance(info, dict):
		regdict = info
		
		if isinstance(values, list):
			if len(values) == 1:
				value = values[0]
			else:
				value=0
				for i in range(len(values)):
					value |= (values[i] << (16*i))
		else:
			value = values
		
		if "values" in regdict and isinstance(regdict["values"], dict) and value in regdict["values"]:
			print(prefix+reg+":", regdict["values"][value])
		elif "values" in regdict and callable(regdict["values"]):
			print(prefix+reg+":", regdict["values"](value))
		elif "type" in regdict and regdict["type"] == "bool":
			print(prefix+reg+":", "on" if value else "off")
		elif regdict.get("type", None) == "int":
			print(prefix+reg+":", value, regdict["unit"] if "unit" in regdict else "")
		elif regdict.get("type", None) == "bits":
			print(prefix+reg+":", value)
			
			for bit, descr in regdict["bits"].items():
				if ((value >> bit) & 1) == 1:
					print(" - "+descr)
		else:
			print(prefix+reg+":", value, regdict["unit"] if "unit" in regdict else "")
	else:
		print(prefix+"0x%02x"%info, values)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-D", "--device", default="/dev/ttyUSB0")
	parser.add_argument("--raw", action="store_true")
	parser.add_argument("--min-change-rel", type=float)
	parser.add_argument("--min-change-abs", type=float)
	parser.add_argument("--skip-addr", action="append")
	parser.add_argument("--repeat", type=int)
	
	parser.add_argument("action", default="dump", nargs="?", choices={"dump", "dumpall", "monitor", "get", "set"})
	parser.add_argument("action_params", nargs="*")
	args = parser.parse_args()

	quintups = QuintUPS()
	quintups.connect(args.device)

	if args.action == "dump":
		for reg, regdict in Quint24DCRegisters.items():
			values = quintups.readRegister(regdict["addr"], count=regdict.get("length", 1))
			if values:
				if args.raw:
					print(reg+":", values, regdict["unit"] if "unit" in regdict else "")
					continue
				
				print_value(regdict, values)
	elif args.action == "dumpall":
		i = 0x7400
		while i < 0x7500:
			values = quintups.readRegister(i)
			
			found=False
			for reg, regdict in Quint24DCRegisters.items():
				if regdict["addr"] == i:
					i += regdict.get("length", 1) - 1
					
					print_value(regdict, values)
					
					found=True
					break
			
			if not found and values != [65535]:
				print_value(i, values)
			
			i += 1
	elif args.action == "monitor":
		prior = {}
		first = True
		skip_addr = []
		if args.skip_addr:
			for a in args.skip_addr:
				arr = a.split(",")
				skip_addr.extend(arr)
			skip_addr = [ int(a, 0) for a in skip_addr ]
		
		for entry in default_skip:
			if isinstance(entry, str):
				skip_addr.append(Quint24DCRegisters[entry]["addr"])
			else:
				skip_addr.append(entry)
		
		def rel_change(old, new):
			return abs(new - old)/old
		
		while True:
			for start, end in Quint24DCMonitorRegisters: 
				values = []
				while len(values) < end - start:
					values.extend( quintups.readRegister(start + len(values), count=0) )
				
				# print(values)
				
				idx = 0
				while idx < len(values):
					addr = start + idx
					
					idx_inc = 1
					cur_regdict = None
					for reg, regdict in Quint24DCRegisters.items():
						if regdict["addr"] == addr:
							cur_regdict = regdict
							idx_inc = cur_regdict.get("length", 1)
							break
					
					if addr in skip_addr:
						idx += idx_inc
						continue
					
					now = datetime.now().strftime("%H:%M:%S")
					if cur_regdict:
						vals = values[idx:idx+cur_regdict.get("length", 1)]
						
						if len(vals) == 1:
							value = vals[0]
						else:
							value=0
							for i in range(len(vals)):
								value |= (vals[i] << (16*i))
						
						if not first:
							show = prior.get(addr, None) != value
							if show and args.min_change_rel is not None and prior.get(addr, None):
								show = rel_change(prior.get(addr, None), value) > args.min_change_rel
							
							if show and args.min_change_abs is not None:
								show = abs(prior.get(addr, None) - value) > args.min_change_abs
							
							if show:
								print_value(cur_regdict, value, prefix=now+" ")
								# print("\t", prior.get(addr, None))
					else:
						value = values[idx]
						if not first:
							show = prior.get(addr, None) != value
							if show and args.min_change_rel is not None and prior.get(addr, None):
								show = rel_change(prior.get(addr, None), value) > args.min_change_rel
							
							if show and args.min_change_abs is not None:
								show = abs(prior.get(addr, None) - value) > args.min_change_abs
							
							if show:
								print_value(addr, value, prefix=now+" ")
								# print("\t", prior.get(addr, None))
					
					prior[addr] = value
					idx += idx_inc
			
			time.sleep(1)
			first = False
	elif args.action == "get":
		if len(args.action_params) == 0:
			print("missing parameter", file=sys.stderr)
			sys.exit(1)
		
		if args.repeat is None:
			repeat = 1
		else:
			repeat = args.repeat
		while repeat != 0:
			for param in args.action_params:
				try:
					param_addr = int(param, 0)
				except:
					param_addr = None
				
				values = None
				for reg, regdict in Quint24DCRegisters.items():
					if param == reg or param_addr == regdict["addr"]:
						values = quintups.readRegister(regdict["addr"], count=regdict.get("length", 1))
						
						print_value(regdict, values)
						break
					
				if values is None:
					values = quintups.readRegister(param_addr)
					
					print_value(param_addr, values)
			
			if repeat > 0:
				repeat -= 1
			time.sleep(0.1)
	elif args.action == "set":
		if len(args.action_params) != 2:
			print("wrong parameter", file=sys.stderr)
			sys.exit(1)
		
		try:
			param_addr = int(args.action_params[0], 0)
		except:
			param_addr = None
		
		value = int(args.action_params[1], 0)
		
		found = False
		for reg, regdict in Quint24DCRegisters.items():
			if args.action_params[0] == reg or param_addr == regdict["addr"]:
				quintups.writeRegister(regdict["addr"], value)
				found = True
				break
		
		if not found:
			if param_addr is None:
				print("error, register not found")
				sys.exit(1)
			else:
				quintups.writeRegister(param_addr, value)
	else:
		print("unknown action")
		sys.exit(1)








