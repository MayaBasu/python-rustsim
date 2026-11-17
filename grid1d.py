import dataclasses
from enum import Enum
from runtimeconstants import Parameters

class grid1dunits(Enum):
    angstroms = 1
    nm = 10
    um = 1000



class too_high:
    pass
class too_low:
    pass
class snapped_to_grid:
    grid_point: int
class between_grid_points:
    lower_grid_point: int
    upper_grid_point: int
    fractional_residual: float

#The grid1d location type is the return value when a point is located in a 1d grid
#the options are that the point is outside of the grid (too high or too low)
#that it is close enough (determined by numerical precision in Parameters) to a grid point to be "snapped"
#to that grid point, or, that it is between two grid points. In this last case we save the fractional_residual
#as the interpolation coefficient

grid1dlocation = Union[too_low, too_high, snapped_to_grid, between_grid_points]


@dataclasses.dataclass
class Grid1d():
    unit: grid1dunits
    step_size: float
    min_value: float
    max_value: float
    num_steps: int
    snap_precision: float

    @staticmethod
    def from_num_steps(num_points: int, min_value: float,  max_value: float, relative_snap_precision: float, unit:grid1dunits) -> Grid1d:
        assert max_value > min_value + Parameters.precision , "Max value must be greater than min value by more than numerical precision"
        assert num_points > 1, "Must have more than 1 point"
        assert isinstance(num_points, int)
        assert relative_snap_precision > 0, "Relative snap precision must be positive"
        assert relative_snap_precision < 0.5, "Relative snap precision must be less than 0.5"

        step_size = (max_value-min_value)/(num_points - 1)
        snap_precision = step_size*relative_snap_precision

        return Grid1d(
            unit,
            step_size,
            min_value,
            max_value,
            num_points - 1,
            snap_precision
        )

    @staticmethod
    def from_points(points:[float], relative_snap_precision:float ,unit: grid1dunits) -> Grid1d:
        num = len(points)
        assert num >= 2, "Need at least 2 points to make a grid"
        high = points[-1]
        low = points[0]
        assert low < high, "First point is not lower than last point"
        expected_interval = (high - low) / (num - 1)
        snap_precision = relative_snap_precision * expected_interval
        for i in range(0,num-1):
            assert points[i + 1] > points[i], \
                f"Failed to make grid because points at index {i} do not monotonically increase"
            assert abs((points[i + 1] - points[i]) - expected_interval) < 2 * snap_precision, \
                " Failed to make grid because points must be evenly spaced"
        return Grid1d.from_num_steps(num, low, high, relative_snap_precision, unit)

    @staticmethod
    def standard_grid():
        Grid1d.from_num_steps(
            Parameters.wave_num,
            Parameters.min_wave_nm,
            Parameters.max_wave_nm,
            0.0001,
            grid1dunits.nm
        )


    def locate(self, point, unit) -> grid1dlocation:
        assert unit == self.unit, "automatic unit conversion not yet implemented"

        if point > (self.maximum_value + self.snap_precision):
            return too_high
        if point < (self.min_value - self.snap_precision):
            return too_low

        #distance from the point to the lowest value in the grid
        delta = (point - self.minimum_value);

        #indices of lower and upper grid points next to 'point'
        lower = (delta / self.step_size).floor();
        upper = (delta / self.step_size).ceil();

        #determine if the point is close enough to a grid point to be snapped to it
        if ((upper * self.step_size) - delta) < self.snap_precision:
            return snapped_to_grid(upper)
        if (delta - (lower * self.step_size)) < self.snap_precision:
            return snapped_to_grid(lower)






