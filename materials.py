import random
from abc import ABC, abstractmethod


# convert feet to meters, returns float
def ft2m(ft):
    m = ft / 3.2808
    return float(m)


class Material(ABC):
    @abstractmethod
    def __init__(self, type_, r, mass_, thickness_, emissivity) -> None:
        """Generic abstract constructor for materials

        :param type_: material type
        :type type_: str
        :param r: RSI value for material
        :type r: float
        :param mass_: material mass
        :type mass_: float
        :param thickness_: material thickness
        :type thickness_: float
        :param emissivity: material emissivity
        :type emissivity: float
        """

        self.type = type_
        self.R = r
        self.mass = float(mass_)
        self.thickness = thickness_
        self.e = emissivity

    @property
    def mass(self) -> float:
        """Get wall mass"""
        return self._mass

    @mass.setter
    def mass(self, value) -> None:
        """Set wall mass (in kg)"""
        self._mass = value

    @property
    def thickness(self) -> float:
        """Get wall thickness"""
        return self._thickness

    @thickness.setter
    def thickness(self, value) -> None:
        """Set wall thickness (in meters)"""
        self._thickness = ft2m(value)

    @property
    def e(self) -> float:
        """Get wall thermal efficiency"""
        return self._e

    @e.setter
    def e(self, value) -> None:
        """Set wall thermal efficiency"""
        self._e = value

    @property
    def R(self) -> float:
        """Get RSI value of wall material"""
        return self._R

    @R.setter
    def R(self, value) -> None:
        """Set RSI value of wall material (in (m^2 * K)/W)"""
        self._R = value

    @property
    def type(self) -> str:
        """Get wall type"""
        return self._type

    @type.setter
    def type(self, value) -> None:
        """Set wall type"""
        self._type = value


class LowEfficiency(Material):
    """Low Efficiency Wall Material"""

    def __init__(self) -> None:
        mass = 1200
        thickness = random.randint(3, 6)
        r = thickness * random.uniform(1., 2.9) * 5.67826  # multiply by 5.67 to get RSI value
        e = 0.90
        super().__init__("LOW", r, mass, thickness, e)


class MedEfficiency(Material):
    """Medium Efficiency Wall Material"""

    def __init__(self) -> None:
        mass = 1200
        thickness = random.randint(3, 6)
        r = thickness * random.uniform(2.9, 3.8) * 5.67826
        e = 0.80

        super().__init__("MEDIUM", r, mass, thickness, e)


class HighEfficiency(Material):
    """High Efficiency Wall Material"""

    def __init__(self) -> None:
        mass = 1200
        thickness = random.randint(3, 6)
        r = thickness * random.uniform(3.7, 4.3) * 5.67826
        e = 0.70

        super().__init__("HIGH", r, mass, thickness, e)


class Brick(Material):
    """Brick Material. For testing purposes"""

    def __init__(self) -> None:
        mass = 1200
        thickness = random.randint(3, 6)
        e = 0.93
        k = 0.47
        r = thickness / (k * 100)

        super().__init__("BRICK", r, mass, thickness, e)
        self.cp = 900
