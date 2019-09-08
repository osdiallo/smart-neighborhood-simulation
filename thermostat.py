from hvac import AC, Furnace


# mode == 0 : off
# mode == 1 : cooling
# mode == 2 : heating
class Thermostat:
	"""Thermostat object.

	Created by homes when they are generated to manage their internal temperatures.
	"""

	def __init__(self, sizes, shared_info, world_clock_, logger_=None) -> None:
		"""Constructor for thermostat object

		:param sizes: list of sizes of the house [width, length, height]
		:type sizes: list()
		:param shared_info: information shared between the home and the thermostat (temperature)
		:type shared_info: multiprocessing data list
		:param world_clock_: object containing current step of the world
		:type world_clock_: multiprocessing data variable
		:param logger_: log object to write log messages to
		:type logger_: log

		:return: Nothing
		"""

		self.world_clock = world_clock_
		self.target_temp = 0
		self.sharedInfo = shared_info
		self.logger = logger_
		self.log_msg = list()

		self.start_temp = None
		self.start_time = None
		self.end_time = None
		self.mode = 0

		self.sizes = sizes
		self.airCon = AC(self.sizes, self.sharedInfo)
		self.furnace = Furnace("gas", sizes, self.sharedInfo)

	def set_target_temp(self, target_temp_) -> None:
		"""Sets the target temperature

		:param target_temp_: target temperature of thermostat
		:type target_temp_: int
		:return: Nothing
		"""

		if self.logger is not None:
			self.log_msg.append(["\t\tSETTING THERMOMETER TO {}".format(target_temp_), "d"])

		self.target_temp = target_temp_

	def get_target_temp(self) -> int:
		"""Returns the current target temperature

		:return: target temperature
		"""

		return self.target_temp
	
	def set_mode(self, mode) -> None:
		"""Sets the thermostat to either cooling or heating, depending on specified mode


		:param mode: Refers to cooling (1), heating (2), or off (0)
		:type mode: int
		:return: Nothing
		"""

		if mode > 2 or mode < 0:
			if self.logger is not None:
				self.logger.critical("Invalid mode")
			exit(0)

		if self.logger is not None:
			if mode == 0:
				self.log_msg.append(["\t\tSETTING HVAC MODE TO OFF", "w"])
			elif mode == 1:
				self.log_msg.append(["\t\tSETTING HVAC MODE TO COOLING", "d"])
			elif mode == 2:
				self.log_msg.append(["\t\tSETTING HVAC MODE TO HEATING", "d"])

		self.fan_off()
		self.mode = mode

	def get_mode(self) -> int:
		"""Returns mode of the thermostat

		:return: current HVAC mode
		"""

		return self.mode

	def get_end_time(self) -> int:
		"""Returns the calculated time that the fan should turn off

		:return: Calculated off time of the HVAC system. -1 If one has not been calculated yet
		"""

		if self.end_time is None:
			return -1

		return self.end_time

	def get_start_time(self) -> int:
		"""Returns the time that the fan was last turned on

		:return: Last time that the HVAC fan was turned on
		"""

		if self.start_time is None:
			return -1

		return self.start_time

	def get_start_temp(self) -> int:
		"""Returns the temperature at which the HVAC fan turned on

		:return: Starting temperature of the HVAC system. -1 if the fan has not yet been started
		"""

		if self.start_temp is None:
			return -1

		return self.start_temp

	def get_power(self) -> int:
		""" Returns the energy consumption of the system

		:return: The energy consumption of the current HVAC system that is turned on
		"""
		power = 0

		if self.mode == 1:
			power = self.airCon.get_power()
		elif self.mode == 2:
			power = self.furnace.get_power()

		return power

	def fan_on(self) -> None:
		"""Turns on the HVAC Fan

		:return: Nothing
		"""

		if self.mode == 0:
			if self.logger is not None:
				self.log_msg.append(["\t\tThermometer is not set to any mode", "w"])

		elif self.mode == 1:
			self.airCon.turn_on()

		else:
			self.furnace.turn_on()

		self.start_time = self.world_clock.value
		self.start_temp = self.sharedInfo[0]
		self.end_time = self.start_time + self.calc_run_time()

		if self.logger is not None:
			self.log_msg.append(["\t\tFan turned ON ({} --> {}) until {}".format(self.start_temp,
																		   self.target_temp, self.end_time), "d"])

	def fan_off(self) -> None:
		"""Turns off the HVAC Fan. Sets the end time to the current time

		:return: Nothing
		"""

		if self.mode == 0:
			if self.logger is not None:
				self.log_msg.append(["\t\tThermometer is not set to any mode", "w"])

		elif self.mode == 1:
			self.airCon.turn_off()

		else:
			self.furnace.turn_off()
		
		self.end_time = self.world_clock.value
		if self.logger is not None:
			self.log_msg.append(["\t\tFan turned OFF @ {}".format(self.end_time), "d"])

	def calc_run_time(self) -> int:
		"""Calculates the amount of time the HVAC system needs to stay on to get the space of the house to the
		target temperature

		:return: Calculated amount of time of the HVAC Fan will stay on
		"""

		time_on = 0

		if self.mode == 0:
			if self.logger is not None:
				self.log_msg.append(["\t\tThermometer is not set to any mode", "w"])

		elif self.mode == 1:
			time_on = self.airCon.calc_on_time(self.airCon.compute_q(self.target_temp))

		else:
			time_on = self.furnace.calc_on_time(self.furnace.compute_q(self.target_temp))

		return time_on

	def calc_temp_delta(self) -> float:
		"""Calculate and return the rate at which temperature would have to change to get to the target temperature
		from the starting temperature

		:return: Temperature change rate
		"""
		temp_delta = abs(self.start_temp - self.target_temp) / (self.get_end_time() - self.get_start_time())
		return temp_delta

	def calc_int_pressure(self):
		r_constant = 8.314
		rm_volume = self.sizes[0] * self.sizes[1] * self.sizes[2]
		rm_air_density = self.sharedInfo[1] / (287.058 * (self.sharedInfo[0] + 273))
		rm_air_mass = rm_air_density / rm_volume
		rm_mols = rm_air_mass / 28.964 # average molar mass of air
		rm_pressure = (rm_mols * (self.sharedInfo[0] + 273) * r_constant) / rm_volume

		self.sharedInfo[1] = rm_pressure

	def running(self) -> bool:
		"""Determine if the HVAC fan is on

		:return: True if the HVAC fan is currently running. False otherwise
		"""

		if self.mode == 0:
			return False

		elif self.mode == 1:
			if self.airCon.is_on():
				return True
			else:
				return False

		elif self.mode == 2:
			if self.furnace.is_on():
				return True
			else:
				return False

	def step(self, temp_diff) -> None:
		"""Changes the temperature reading of a house by temp_diff

		:param temp_diff: amount at which temperature changes per step
		:return: Nothing
		"""

		if len(self.log_msg) >= 1:
			for msg in self.log_msg:
				if msg[1] == "d":
					self.logger.debug(msg[0])
				elif msg[1] == "w":
					self.logger.warning(msg[0])
				else:
					self.logger.critical(msg[0])

			del self.log_msg[:]

		if self.running():
			if self.mode == 0:
				if self.logger is not None:
					self.logger.warning("\t\tThermostat is OFF")

			if self.mode == 1:
				self.sharedInfo[0] -= temp_diff

			if self.mode == 2:
				self.sharedInfo[0] += temp_diff
		else:
			if self.logger is not None:
				self.logger.warning("This thermometer ain't running")
