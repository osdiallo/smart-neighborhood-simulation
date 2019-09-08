import os
import csv
from building import Residential


class Neighborhood:
    def __init__(self, i, num_homes, outside_temp, world_clock, logger_=None) -> None:
        """Constructor for neighborhood

        :param i: neighborhood ID
        :type i: int
        :param num_homes: number of homes
        :type num_homes: int
        :param outside_temp: temperature of outside world
        :type outside_temp: multiprocessing integer
        :param world_clock: internal world clock
        :type world_clock: multiprocessing integer
        :param logger_: logging object to write log messages to
        :type logger_: log
        :return: Nothing
        """

        self.id = i
        self.num_homes = num_homes
        self.outside_temp = outside_temp
        self.world_clock = world_clock
        self.logger = logger_

        self.homes = list()
        self.processes = list()
        self.last_write_time = 0

    def generate(self, min_length=None, max_length=None, min_width=None, max_width=None,
                 lower_t_=32, upper_t_=78) -> None:
        """Generate the neighborhood and the houses within it

        :param min_length: minimum length of house
        :type min_length: int
        :param max_length: maximum length of house
        :type max_length: int
        :param min_width: minimum width of house
        :type min_width: int
        :param max_width: maximum width of house
        :type max_width: int
        :param lower_t_: treated as lower temp limit for coloring cells
        :type lower_t_: int
        :param upper_t_: treated as upper temp limit for coloring cells
        :type upper_t_: int
        :return: Nothing
        """

        num_residents = 2

        for i in range(self.num_homes):
            if self.logger is not None:
                self.logger.debug('\tHOME {}:'.format(i))

            home = Residential(self.id, i, num_residents, self.outside_temp, self.world_clock, self.logger)
            home.generate(min_length, max_length, min_width, max_width, lower_t_, upper_t_)

            self.homes.append(home)
            # self.processes.append(mp.Process(target=home.step, args=(step_event, clock_event, )))

        if self.logger is not None:
            self.logger.debug('\tCreated {} homes'.format(self.num_homes))

        abs_path, filename = os.path.split(os.path.realpath(__file__))
        data_log = "{}/data/neighborhood_{}.csv".format(abs_path, self.id)

        with open(data_log, 'w') as data_file:
            file_writer = csv.writer(data_file)
            header = ['House:']
            wall_config = ['Wall Type:']
            temp_config = ['Target Temp:']
            size_config = ['Size (m):']

            for i in range(self.num_homes):
                home = self.homes[i]
                header.append(i)
                wall_config.append(home.get_wall_type())
                temp_config.append("{:.4}".format(home.get_target_temp()))
                size_config.append("{:.2f} x {:.2f} x {:.2f}".format(home.length, home.width, home.height))

            temp_config.append("Outside Temp:")

            file_writer.writerow(header)
            file_writer.writerow(wall_config)
            file_writer.writerow(temp_config)
            file_writer.writerow(size_config)
            file_writer.writerow(list())

    def step(self, log_data=False) -> None:
        """Increment the entire neighborhood by a step. Log the interior temperature
        of each house if asked to

        :param log_data: determines whether values of the homes in the neighborhood should be logged
        :type log_data: bool
        :return: nothing
        """

        if log_data is True:
            abs_path, filename = os.path.split(os.path.realpath(__file__))
            data_dir = "{}/data/neighborhood_{}.csv".format(abs_path, self.id)

            row = list()
            row.append(self.world_clock.value)

            with open(data_dir, 'a') as data_file:
                file_writer = csv.writer(data_file)

                i = 0
                for home in self.homes:
                    if self.logger is not None:
                        self.logger.debug('\tHOME {}:'.format(i))

                    home.step()
                    row.append("{:.3f}".format(home.get_int_temp()))

                    i += 1

                row.append("")
                row.append("{:.5f}".format(self.outside_temp.value))

                file_writer.writerow(row)
                self.last_write_time = self.world_clock.value

        else:
            for home in self.homes:
                if self.logger is not None:
                    self.logger.debug('\tHOME {}:'.format(home.h_id))

                home.step()
