import dataclasses
import matplotlib.pyplot as plt
from runtimeconstants import Parameters
import numpy as np

@dataclasses.dataclass
class CoordinateSystem():
    # A coordinate system is a cartesian system defined by a center and two axis
    # This object allows clear differentiation between sky coordinates and detector plane coordinates etc
    # Guarantees:
    # 1. Each value is a float, not Nan or Inf - TODO
    # 2. Euclidean lengths of axis are longer than the float precision

    x_axis: [float, float]
    y_axis: [float, float]
    center: [float, float]

    def __post_init__(self):
        assert self.x_axis[0]**2 + self.x_axis[1]**2> Parameters.precision, \
            "Euclidean length of x-axis must be greater than the floating point precision"
        assert self.y_axis[0] ** 2 + self.y_axis[1] ** 2 > Parameters.precision, \
            "Euclidean length of y-axis must be greater than the floating point precision"

    @staticmethod
    def ABSOLUTE_COORDINATES() -> CoordinateSystem:
        return CoordinateSystem(
            [1,0],
            [0,1],
            [0,0])

    def plot(self, ax):
        ax.plot([self.center[0],self.center[0] + self.x_axis[0]],
                [self.center[1],self.center[1] + self.x_axis[1]])
        ax.plot([self.center[0], self.center[0] + self.y_axis[0]],
                [self.center[1], self.center[1] + self.y_axis[1]])


@dataclasses.dataclass
class Point:
    # Point in a given coordinate system. This can be a point source or the location of a PSF
    # TODO: check that the x, y are normal floats
    x: float
    y: float
    coordinate_system: CoordinateSystem #is there some way to store a 'reference' here instead of copying data?

    def new(x,y,coordinate_system):
        assert isinstance(coordinate_system,CoordinateSystem)
        assert isinstance(x, float | int)
        assert isinstance(y, float | int)
        return Point(x,y,coordinate_system)

    def transform_to(self, new_coordinate_system: CoordinateSystem) -> Point:
        #This function takes a point and returns it transformed to another coordinate system
        assert isinstance(new_coordinate_system, CoordinateSystem), "Can only transform point if given type CoordinateSystem"


        #calculate the x and y positions of self in absolute coordinates
        absolute_x = self.x * self.coordinate_system.x_axis[0] + \
            self.y * self.coordinate_system.y_axis[0] + \
            self.coordinate_system.center[0];

        absolute_y = self.x * self.coordinate_system.x_axis[1] + \
            self.y * self.coordinate_system.y_axis[1] + \
            self.coordinate_system.center[1];

        #determinanite of the coordinate transform
        det = new_coordinate_system.y_axis[1] * new_coordinate_system.x_axis[0] - \
        new_coordinate_system.y_axis[0] * new_coordinate_system.x_axis[1]

        #projections onto the new coordinate axis
        proj_x = ((absolute_x - new_coordinate_system.center[0]) * new_coordinate_system.y_axis[1] - \
         (absolute_y - new_coordinate_system.center[1]) * new_coordinate_system.y_axis[0]) / det

        proj_y = (-(absolute_x - new_coordinate_system.center[0]) * new_coordinate_system.x_axis[1] + \
         (absolute_y - new_coordinate_system.center[1]) * new_coordinate_system.x_axis[0]) / det

        return Point(proj_x, proj_y, new_coordinate_system)

    def to_absolute(self) -> Point:
        #transform a point to absolute coordinates
        return self.transform_to(CoordinateSystem.ABSOLUTE_COORDINATES())

    def zero(coordinate_system:CoordinateSystem) -> Point:
        return Point(0,0, coordinate_system)


    def plot(self, ax):
        #all plotting happens in absolute coordinates
        point = self.to_absolute()
        ax.scatter(point.x,point.y)

    def __truediv__(self, other) -> Point:
        if isinstance(other, float) | isinstance(other, int):
            if abs(other) < Parameters.precision:
                raise Exception("Division by zero")
            return Point(
                self.x/other,
                self.y/other,
                self.coordinate_system
            )
        if isinstance(other, Point):
            if not other.coordinate_system == self.coordinate_system:
                other = other.transform_to(self.coordinate_system)
            if abs(other.x) < Parameters.precision:
                raise Exception("Division by zero")
            if abs(other.y) < Parameters.precision:
                raise Exception("Division by zero")
            return Point(
                self.x/other.x,
                self.y/other.y,
                self.coordinate_system
            )
        else:
            raise Exception("Points can only be divided by int, float, or another point")

    def __sub__(self, other) -> Point:
        if not isinstance(other, Point):
            raise Exception("Only another Point can be subtracted from a Point")
        if not other.coordinate_system == self.coordinate_system:
            other = other.transform_to(self.coordinate_system)

        return Point(
            self.x - other.x,
            self.y - other.y,
            self.coordinate_system
        )
    def __round__(self) -> Point:
        return Point(
            round(self.x),
            round(self.y),
            self.coordinate_system
        )
    def floor(self) -> Point:
        return Point(
            np.floor(self.x),
            np.floor(self.y),
            self.coordinate_system
        )
    def __mul__(self, other:Point|int|float)-> Point:
        if isinstance(other, float|int):
            return Point(
            self.x*other,
            self.y*other,
            self.coordinate_system
        )
        if isinstance(other, Point):
            if not other.coordinate_system == self.coordinate_system:
                other = other.transform_to(self.coordinate_system)
            return Point(
                self.x*other.x,
                self.y*other.y,
                self.coordinate_system
            )
        raise Exception("Can only multiply Point by another point (component-wise multiplication) int or float")


