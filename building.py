from abc import ABC, abstractmethod
from thermostat import Thermostat
import multiprocessing as mp
import materials as material
import devices
import es
import random
import math


# converts celsius to fahrenheit
def c2f(temp):
    c_temp = temp * 9.0 / 5.0 + 32.0
    return c_temp


# converts fahrenheit to celsius
def f2c(temp):
    f_temp = (temp - 32.0) * 5.0 / 9.0
    return f_temp


# converts feet to meters
def ft2m(ft):
    m = ft / 3.2808
    return m


class Building(ABC):
    """Abstract Class for Building Types"""

    @abstractmethod
    def __init__(self, n_id_, i, amb_t, world_clock_, logger_=None) -> None:
        """Constructor for homes

        :param n_id_: ID of neighborhood containing home
        :type n_id_: int
        :param i: ID of home
        :type i: int
        :param amb_t: Ambient temperature
        :type amb_t: multiprocessing variable
        :param world_clock_: World Clock
        :type world_clock_: multiprocessing variable
        :param logger_: log file to write log messages to
        :type: logger_: log object
        :return: Nothing
        """

        self._length = -1
        self._width = -1
        self._height = -1
        self._num_floors = -1
        self._n_id = n_id_
        self._h_id = i

        self._lower_temp_grad = None
        self._upper_temp_grad = None

        self.outside_temp = amb_t
        self.world_clock = world_clock_
        self.logger = logger_

        self.thermostat = None
        self.walls = None
        self.battery = None
        self.pv = None

        self.devices = dict()
        self.temp_history = list()

        self.sharedInfo = mp.Array('d', range(4))

    @property
    def n_id(self):
        """Get neighborhood ID"""
        return self._n_id

    @n_id.setter
    def n_id(self, value):
        """Set neighborhood ID"""
        self._n_id = value

    @property
    def h_id(self):
        """Get house ID"""
        return self._h_id

    @h_id.setter
    def h_id(self, value):
        """Set house ID"""
        self._h_id = value

    @property
    def length(self):
        """Get house length"""
        return self._length

    @length.setter
    def length(self, value):
        """Set house length"""
        self._length = value

    @property
    def width(self):
        """Get house width"""
        return self._width

    @width.setter
    def width(self, value):
        """Set house width"""
        self._width = value

    @property
    def height(self):
        """Get house height"""
        return self._height

    @height.setter
    def height(self, value):
        """Set house height"""
        self._height = value

    @property
    def num_floors(self):
        """Get number of floors in house"""
        return self._num_floors

    @num_floors.setter
    def num_floors(self, value):
        """Set number of floors in house"""
        self._num_floors = value

    @abstractmethod
    def generate(self, lower_t, upper_t) -> None:
        """Randomly generates home

        :param lower_t: lower temperature gradient (used for determining temperature color of home)
        :type lower_t: int
        :param upper_t: higher temperature gradient (used for determining temperature color of home)
        :type upper_t: int
        :return: Nothing
        """

        # convert sizes to m
        self.length = ft2m(self.length)
        self.width = ft2m(self.width)
        self.height = ft2m(self.height)

        self._lower_temp_grad = lower_t
        self._upper_temp_grad = upper_t

        # select wall material properties
        wall_type = random.randint(1, 3)
        if wall_type == 1:
            self.walls = material.LowEfficiency()
        elif wall_type == 2:
            self.walls = material.MedEfficiency()
        elif wall_type == 3:
            self.walls = material.HighEfficiency()
        else:
            self.walls = material.BrickWall()

        self.sharedInfo[0] = self.outside_temp.value
        self.sharedInfo[1] = 101325  # internal pressure, PA
        self.temp_history.append(self.sharedInfo[0])

        sizes = [self.length, self.width, self.height]
        self.thermostat = Thermostat(sizes, self.sharedInfo, self.world_clock, self.logger)

    @abstractmethod
    def step(self) -> None:
        """Proceeds the house a single step.

        Calculates next temperature and energy consumption of all devices.

        :return: Nothing
        """

        self.battery.charge(self.pv.produce())

        # approach ambient temperature if HVAC is off
        if not self.thermostat.running():
            self.approach_amb()

        else:
            # determine if the HVAC should be turned off
            if self.world_clock.value > self.thermostat.get_end_time():
                self.thermostat.fan_off()
                self.approach_amb()

            else:
                self.thermostat.step(self.thermostat.calc_temp_delta())

                if self.logger is not None:
                    self.logger.debug("\t\tInner Temperature: {:.3f}, end_time: {}".format(self.sharedInfo[0],
                                                                                        self.thermostat.get_end_time()))

        self.consume_energy()
        self.temp_history.append(self.sharedInfo[0])

    def consume_energy(self) -> int:
        """Calculates consumption of all devices and systems within a house

        :return: Energy consumption
        """

        hvac_consumption = 0
        device_consumption = 0

        if self.thermostat.running():
            hvac_consumption = self.thermostat.get_power()

        for key, device in self.devices.items():
            if device.check_run_time(self.world_clock.value) is True:
                device.turn_off(self.world_clock.value)

            device_consumption += device.consumption

        total_consumption = device_consumption + hvac_consumption

        # if the total consumption is greater than the current charge
        # held by the house's battery, then fully discharge the battery and
        # return the amount of energy needed from the grid. Else, return 0
        if total_consumption > self.battery.current_charge():
            energy_needed = total_consumption - self.battery.current_charge()

            self.battery.discharge(total_consumption - energy_needed)
            return energy_needed

        else:
            self.battery.discharge(total_consumption)
            return 0

    # TO-DO: Calculate heat loss through roof conduction
    def approach_amb(self) -> None:
        """Approach the ambient temperature.

        If the HVAC fan is off, approach the ambient world temperature at a rate dependent on the wall materials.

        :return: Nothing
        """

        if self.logger is not None:
            self.logger.debug("\t\tApproaching Ambient Temperature ({:.3f}) (off since {})".format(
                self.outside_temp.value, self.thermostat.get_end_time()))

        air_specific_r = 287.058  # J/(kg * K) based on mean molar mass for dry air (28.96 g/mol)
        air_heat_cap = 0.718  # J/(kg * K) based on c_v value for dry air @ 300 K
        air_density = self.sharedInfo[1] / (air_specific_r * (self.sharedInfo[0] + 273))  # kg/m^3

        w_area = 2 * ((self.length * self.height) + (self.width * self.height))
        r_volume = self.length * self.width * self.height

        # constants
        sun_temp = 5800  # K
        sun_radius = 6.96 * (10 ** 5)  # km
        o = (5.6703 * (10 ** -8))  # W/(m^2 * K^-4)
        distance_sun2earth = 1.496 * (10 ** 8)  # km

        # calculate radiation from sun to outside of wall
        solar_rad = o * (4 * math.pi * sun_radius ** 2) * (sun_temp ** 4)  # W
        solar_i = solar_rad / (4 * math.pi * (distance_sun2earth ** 2))  # W/m^2

        # calculate amount of heat conducted through a single uniform wall (no layers)
        w_conducted_heat = (w_area * (self.outside_temp.value - self.sharedInfo[0])) / self.walls.R

        # calculate amount that internal temperature raises by after adding the
        # heat conducted through the walls into the room
        temp_change = w_conducted_heat / (air_density * r_volume * air_heat_cap)
        self.sharedInfo[0] += temp_change

    def color_gradient(self, step_num=None) -> str:
        """Determine color of house depending on temperature

        :param step_num: Step to go to
        :type step_num: int
        :return: String containing hex color code of the house
        """

        if step_num is not None:
            internal_temp = self.get_int_temp(step_num)
        else:
            internal_temp = self.get_int_temp()

        r = 255
        g = 255
        b = 255

        t_c = int(round((c2f(internal_temp) - self._lower_temp_grad)))
        diff = int(math.ceil((self._upper_temp_grad - self._lower_temp_grad) / 4))

        if t_c >= (diff * 4):
            g = 0
            b = 0

        elif t_c >= (diff * 3):
            g = int(round(g * (1 - ((t_c % diff) * (1 / diff)))))
            b = 0

        elif t_c >= (diff * 2):
            r = int(round(r * ((t_c % diff) * (1 / diff))))
            b = 0

        elif t_c >= diff:
            r = 0
            b = int(round(b * (1 - ((t_c % diff) * (1 / diff)))))

        elif t_c >= 0:
            r = 0
            g = int(g * round((t_c % diff) * (1 / diff), 2))

        else:
            r = 0
            g = 0

        color_code = '%02x%02x%02x' % (r, g, b)
        hex_int = int(color_code, 16)

        if t_c < 0:
            hex_int -= abs(t_c) * 4
        elif t_c > (diff * 4):
            t_c -= (diff * 4)
            hex_int -= t_c * (131072 * 2)

        return str.format('#{:06x}', hex_int)

    def get_int_temp(self, step_num=None) -> float:
        """Returns internal temperature of a house at a specified time

        :param step_num: Step to retrieve temperature from. Default is None, which means the current step
        :type step_num: int
        :return: temperature at step
        """

        if step_num is not None:
            return self.temp_history[step_num]
        else:
            return self.temp_history[self.world_clock.value]

    def get_target_temp(self) -> int:
        """Returns the current target temperature of the house"""

        return self.thermostat.get_target_temp()

    def get_wall_type(self) -> str:
        """Returns the type of the materials making up the walls"""

        return self.walls.type


class Residential(Building):
    """Residential Building Concrete Object"""

    def __init__(self, n_id, i, inhabitants, amb_t, world_clock, logger_) -> None:
        """Constructor for residential buildings

        :param n_id: ID of neighborhood containing home
        :type n_id: int
        :param i: ID of home
        :type i: int
        :param inhabitants: number of people living in a house
        :type inhabitants: int
        :param amb_t: Ambient temperature
        :type amb_t: multiprocessing variable
        :param world_clock: World Clock
        :type world_clock: multiprocessing variable
        :param logger_: log file to write log messages to
        :type: logger_: log object
        """

        super().__init__(n_id, i, amb_t, world_clock, logger_)
        self.num_residents = inhabitants
        self.has_basement = bool(random.getrandbits(1))
        self.has_pool = 1
        self.num_windows = 0

    def generate(self, min_length=None, max_length=None, min_width=None, max_width=None,
                 lower_t_=32, upper_t_=78) -> None:
        """Generates a residential building and its devices

        :param min_length: minimum length of house
        :type min_length: int
        :param max_length: maximum length of house
        :type max_length: int
        :param min_width: minimum width of house
        :type min_width: int
        :param max_width: maximum width of house
        :type max_width: int
        :param lower_t_: lower temperature gradient (used for determining temperature color of home)
        :type lower_t_: int
        :param upper_t_: higher temperature gradient (used for determining temperature color of home)
        :type upper_t_: int
        :return: Nothing
        """

        # sizes taken approximated from average size of middle income home (40x40 ft) in the United States
        self.num_floors = random.randint(1, 3)
        self.length = 40 + random.randint(-10, 10)
        self.width = 40 + random.randint(-10, 10)
        self.height = 8
        if min_length is not None:
            min_length = int(min_length)
            if self.length < min_length:
                self.length = min_length
        if max_length is not None:
            max_length = int(max_length)
            if self.length > max_length:
                self.length = max_length

        if min_width is not None:
            min_width = int(min_width)
            if self.width < min_width:
                self.width = min_width
        if max_width is not None:
            max_width = int(max_width)
            if self.width > max_width:
                self.width = max_width

        if self.has_pool == 1:
            self.devices["pool_pump"] = devices.PoolPump(2, 8)

        self.devices["evcs"] = devices.EVCS(1, 200)
        self.battery = es.ElectricalStorage()
        self.pv = es.SolarPanel(5, 300)  # typical wattage of a solar panel

        super().generate(lower_t_, upper_t_)

        self.thermostat.set_target_temp(f2c(72))
        self.thermostat.set_mode(1)

        for key, device in self.devices.items():
            device.turn_on(self.world_clock.value)

        # Total window area is estimated to be 15% of total floor space by the EPA
        # Window area is divided by window dimensions (3ftx5ft) to get num_windows
        f_area = self.length * self.width
        self.num_windows = round((f_area * 0.15) / 15)

    def step(self) -> None:
        """Step the house forward"""

        super().step()
