class ElectricalStorage:
    """Electrical Storage System, holds charges of backup power"""

    def __init__(self) -> None:
        """Constructor for electrical storage system"""

        self._amps = 415  # Ah
        self._voltage = 12  # V
        self._max_capacity = self._amps * self._voltage * 3600  # Watts (multiply by 3600 to convert from W*hr to J)
        self._current_capacity = float(0)
        self._charge_history = list()

    def discharge(self, w) -> int:
        """Discharge w Watts from the battery

        :param w: Watts to remove from the battery
        :type w: float
        :return: 1 if the battery was successfully discharged, 0 otherwise
        """

        if (self._current_capacity - w) < 0:
            self._charge_history.append(self._current_capacity)
            return 0
        else:
            self._current_capacity -= w
            self._charge_history.append(self._current_capacity)
            return 1

    def charge(self, w) -> int:
        """Add w Watts to the battery

        :param w: Watts to add to the battery
        :type w: float
        :return: 1 if the battery was successfully charged, 0 otherwise
        """

        if (self._current_capacity + w) >= self._max_capacity:
            self._charge_history.append(self._current_capacity)
            return 0
        else:
            self._current_capacity += w
            self._charge_history.append(self._current_capacity)
            return 1

    def current_charge(self, step=None) -> int:
        """ Returns the charge of the battery, either at the current step or at a specified step


        :param step: Step to evaluate. Default None
        :type step: int
        :return: Charge of electrical system at step
        """

        if step is not None:
            return self._charge_history[int(step)]
        return self._current_capacity


class SolarPanel:
    """Photovoltaic Cell Array Object.

    Created by each home at generation and charges the electrical storage system at each step
    """

    def __init__(self, n, watts) -> None:
        """Constructor for Photovoltaic Cells

        :param n: number of cells in array
        :type n: int
        :param watts: wattage of each cell
        :type watts: int
        return: Nothing
        """

        self._num_cells = n
        self._wattage = watts  # watts
        self._efficiency = 0.20

    def produce(self) -> float:
        """Calculate the amount of watts produced by the array PER STEP (second)

        :return: Watts produced per step (in Watts)
        """

        return (self._num_cells * self._wattage) / 3600

