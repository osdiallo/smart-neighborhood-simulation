from abc import ABC, abstractmethod


class HVAC(ABC):
	# mode == 0 : turned off
	# mode == 1 : turned on
	
	@abstractmethod
	def __init__(self, sizes, shared_info):
		"""Constructor for HVAC System

		:param sizes: list of sizes of home
		:type sizes: list
		:param shared_info: shared information between the House and the devices (internal temperature)
		:type shared_info: multiprocessing list
		"""

		self.sharedInfo = shared_info
		self.sizes = sizes
		
		self.mode = 0
		self.power = 2920 # measured in J/s or Watts

	def is_on(self) -> bool:
		"""Checks if the HVAC system is on

		:return: True if the HVAC system is on, False otherwise"""
		if self.mode == 1:
			return True
		else:
			return False

	def turn_on(self) -> None:
		self.mode = 1

	def turn_off(self) -> None:
		self.mode = 0

	# return number of seconds it takes for a unit to produce a certain amount of energy
	def calc_on_time(self, q) -> int:
		"""Calculate the amount of time it would take to produce a certain amount of heat"""
		time_on = q / self.power
		return round(time_on)

	def compute_q(self, target_temp) -> float:
		"""Compute heat (in Joules) needed to get a space to a temperature

		:param target_temp: target temperature
		:type target_temp: int
		:return: heat added to the space
		"""

		r_constant = 8.314  # universal gas constant

		rm_volume = self.sizes[0] * self.sizes[1] * self.sizes[2]
		# rm_air_density = self.sharedInfo[1] / (287.05 * (self.sharedInfo[0] + 273))
		# rm_air_mass = rm_air_density / rm_volume
		# rm_mols = rm_air_mass / 28.964 # average molar mass of air
		# rm_pressure = (rm_mols * (self.sharedInfo[0] + 273) * r_constant) / rm_volume

		rm_pressure = 101325  # measured in pascals (STP)

		rm_mols = (rm_volume * rm_pressure) / ((self.sharedInfo[0] + 273) * r_constant)
		heat_cap = (5 * r_constant) / 2		# heat capacity of an ideal gas at constant volume (7R/2 for constant pressure)

		if self.mode == 0:
			q = 0
		else:
			q = heat_cap * rm_mols * abs(self.sharedInfo[0] - target_temp)

		return q

	def get_power(self) -> float:
		"""Returns power consumption of HVAC

		:return: energy consumption of machine
		"""
		return self.power / 3600


class AC(HVAC):
	def __init__(self, sizes, shared_info):
		super().__init__(sizes, shared_info)


class Furnace(HVAC):
	def __init__(self, t, sizes, shared_info):
		super().__init__(sizes, shared_info)
		self.energy_source = t		# natural, gas, or electric
