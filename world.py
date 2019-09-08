import sys
import time
import os
import signal
import multiprocessing as mp
import json
import math
import logging
from neighborhood import Neighborhood as ngh


# fahrenheit -> celsius
def f2c(temp):
	f_temp = (temp - 32.0) * 5.0 / 9.0
	return f_temp


class World:
	"""World class object that contains a specified number of neighborhoods and homes.

	This module can be used to simulate an easily scalable world of homes in different
	smart neighborhoods.
	"""

	def __init__(self, num_neighborhoods_, num_homes_, simulation_time_, log=False) -> None:
		"""Constructor for world

		:param num_neighborhoods_: number of neighborhoods to create
		:type num_neighborhoods_: int
		:param num_homes_: number of homes per neighborhood
		:type num_homes_: int
		:param simulation_time_: total amount of time to run simulation
		:type simulation_time_: int
		:param log: keeps track of when to log information about the world
		:type log: bool
		"""

		self.num_neighborhoods = num_neighborhoods_
		self.num_homes = num_homes_
		self.num_steps = simulation_time_
		self.data_log_time = 0

		if log is True:
			logging.basicConfig(filename="world.log", filemode='w', level=logging.DEBUG,
								format='%(name)s - %(levelname)s - %(message)s')
			self.logger = logging.getLogger(__name__)

			with open("world.log", 'w'):
				pass

		else:
			self.logger = None

		self.season = None
		self.weather = None
		self.lo_temp = None
		self.hi_temp = None

		self.outside_temp = mp.Value('d', 0.0)
		self.world_clock = mp.Value('i', 0)
		self.temp_history = list()
		self.neighborhoods = list()
		
		self.step_event = mp.Event()
		self.clock_event = mp.Event()

		self.processes = list()

	def get_time(self):
		"""Returns current time of the world

		:return: current world clock time
		"""
		return self.world_clock.value

	def get_temp(self, step_num=None) -> float:
		"""Get temperature of the world at a certain time step

		:param step_num: time step to find
		:type step_num: int
		:return: world temperature at a time step
		"""
		if step_num is not None:
			return self.temp_history[step_num]
		else:
			return self.temp_history[self.world_clock.value]
	
	def make_world(self, season_, weather_, min_length=None, max_length=None, min_width=None, max_width=None,
					lower_t_=32, upper_t_=78) -> None:
		"""Generates world based on specified weather conditions

		:param min_length: minimum length of house
        :type min_length: int
        :param max_length: maximum length of house
        :type max_length: int
        :param min_width: minimum width of house
        :type min_width: int
        :param max_width: maximum width of house
        :type max_width: int
        :param season_: current world season condition
        :type season_: string
        :param weather_: current world climate condition
		:type weather_: string
		:param lower_t_: treated as lower temp limit for coloring cells
		:type lower_t_: int
		:param upper_t_: treated as upper temp limit for coloring cells
		:type upper_t_: int
		:return: nothing
		"""

		# temperatures derived from average outdoor temperature
		# of the continental US in 2017

		if self.logger is not None:
			self.logger.info('Creating World\n\tSEASON: {}\tWEATHER: {}'.format(season_, weather_))

		self.season = season_
		if self.season == "fall":
			# september -> november
			self.lo_temp = 43.5
			self.hi_temp = 67.8

		if self.season == "winter":
			# december -> february
			self.lo_temp = 25.9
			self.hi_temp = 43.8

		if self.season == "spring":
			# march -> may
			self.lo_temp = 41.3
			self.hi_temp = 65.6

		if self.season == "summer":
			# june -> august
			self.lo_temp = 60.0
			self.hi_temp = 85.3

		# this assumes day starts at average temperature (around 10 am?)
		self.weather = weather_
		if self.weather == "cloudy":
			self.lo_temp -= 3
			self.hi_temp -= 3
		elif self.weather == "sunny":
			self.lo_temp += 3
			self.hi_temp += 3
		elif self.weather == "rainy":
			self.lo_temp -= 5
			self.hi_temp -= 5
		elif self.weather == "snowy":
			self.lo_temp -= 7
			self.hi_temp -= 7

		self.lo_temp = f2c(self.lo_temp)
		self.hi_temp = f2c(self.hi_temp)
		self.outside_temp.value = (self.hi_temp + self.lo_temp) / 2
		self.outside_temp.value = self.temp_change()
		self.temp_history.append(self.outside_temp.value)

		with open("config", 'w') as config_file:
			config = dict()

			config['season'] = self.season
			config['weather'] = self.weather
			config['num_steps'] = self.num_steps
			json.dump(config, config_file)

		# set up neighborhoods
		for i in range(self.num_neighborhoods):
			if self.logger is not None:
				self.logger.debug('NEIGHBORHOOD {} SET-UP:'.format(i))

			neighborhood = ngh(i, self.num_homes, self.outside_temp, self.world_clock, self.logger)
			neighborhood.generate(min_length, max_length, min_width, max_width, lower_t_, upper_t_)

			self.neighborhoods.append(neighborhood)

	# NO LONGER USED
	def run_world(self):
		num_events = 0

		for process in self.processes:
			process.start()

		# waits for all the houses in each neighborhood to be created
		while num_events < self.num_neighborhoods:
			self.step_event.wait()
			num_events += 1

		# signal that all neighborhoods have finished being created and
		# that the world clock has begun counting
		#print("Beginning world clock...")
		self.clock_event.set()
		while self.world_clock.value < self.num_steps:
			time.sleep(0.001)

			self.outside_temp.value = self.temp_change()
			self.temp_history.append(self.outside_temp.value)
			self.world_clock.value += 1

			num_events = 0
			while num_events < (self.num_homes * self.num_neighborhoods):
				self.step_event.wait()
				num_events += 1

			self.clock_event.set()

	def step(self) -> None:
		"""Steps every neighborhood in the world forward by one

		:return: nothing
		"""
		self.world_clock.value += 1

		log_data = False
		if self.data_log_time == (self.world_clock.value - 15):
			self.data_log_time = self.world_clock.value
			log_data = True

		i = 0

		for neighborhood in self.neighborhoods:
			if self.logger is not None:
				self.logger.debug('NEIGHBORHOOD {} @ {}:'.format(i, self.world_clock.value))

			neighborhood.step(log_data)
			i += 1

		self.outside_temp.value = self.temp_change()
		self.temp_history.append(self.outside_temp.value)

	def temp_change(self) -> float:
		"""Return the temperature of the world at the next time step

		:return: next world temperature
		"""
		temp_avg = (self.hi_temp + self.lo_temp) / 2
		temp_amp = self.hi_temp - temp_avg

		new_temp = temp_amp * math.sin((((2 * math.pi) / (24 * 60 * 60)) * self.world_clock.value)) + temp_avg
		return new_temp


if __name__ == "__main__":
	if len(sys.argv) < 4:
		print("Usage: python3 world.py num_neighborhoods num_homes run_time...")
		quit()

	abs_path, filename = os.path.split(os.path.realpath(__file__))

	data_dir = "{}/data/".format(abs_path)
	if not os.path.isdir(data_dir):
		os.makedirs(data_dir)

	num_neighborhoods = int(float(sys.argv[1]))
	num_homes = int(float(sys.argv[2]))
	run_time = int(float(sys.argv[3]))

	world = World(num_neighborhoods, num_homes, run_time)
	world.make_world("spring", "sunny")

	os.setpgrp()
	try:
		world.run_world()

	finally:
		final_time = world.get_time()
		print("Final RunTime: {} minutes ({} s)".format(final_time/60, final_time))
		os.killpg(0, signal.SIGKILL)
