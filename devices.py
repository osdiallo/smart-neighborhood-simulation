from abc import ABC, abstractmethod


class Devices(ABC):
    @abstractmethod
    def __init__(self, consumption_):
        self._consumption = consumption_  # in watts
        self._state = 1
        self._amps = 0
        self._on_time = None
        self._off_time = None

    @property
    def consumption(self):
        if self._state == 1:
            return self._consumption
        else:
            return 0

    @consumption.setter
    def consumption(self, value):
        self._consumption = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def on_time(self):
        return self._on_time

    @on_time.setter
    def on_time(self, value):
        self._on_time = value

    @property
    def off_time(self):
        return self._off_time

    @off_time.setter
    def off_time(self, value):
        self._off_time = value

    def turn_on(self, time):
        self.on_time = time
        self.state = 1

    def turn_off(self, time):
        self.off_time = time
        self.state = 0

    @abstractmethod
    def check_run_time(self, run_time, time):
        # return true if it is time to turn the device off
        if time > run_time + self._on_time:
            return True
        else:
            return False


class PoolPump(Devices):
    def __init__(self, h, run_time_):
        self._horsepower = h
        self._run_time = run_time_ * 3600  # hours to seconds

        consumption_ = self._horsepower * 745.7  # conversion from horsepower to watts
        super().__init__(consumption_)

    def check_run_time(self, time):
        super().check_run_time(self._run_time, time)


class EVCS(Devices):
    def __init__(self, level_, amps_):
        self._level = level_

        if level_ == 1 or level_ < 1 or level > 2:
            consumption_ = 120 * amps_  # 120V * Amps (typical house amperage)
        elif level_ == 2:
            consumption_ = 240 * amps_  # 240V * Amps (typical house amperage)

        super().__init__(consumption_)

    def check_run_time(self, time):
        pass
