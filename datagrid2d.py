import dataclasses
from array import ArrayType

from grid2d import grid2d, interpolation_data
import numpy as np
from geometry import Point, CoordinateSystem

@dataclasses.dataclass
class Data2D():
    grid: grid2d
    data: np.ndarray[tuple[int, int], np.dtype[np.float64]]

    def new_from_data(grid:grid2d, data: np.ndarray[tuple[int, int], np.dtype[np.float64]])-> Data2D:
        if not isinstance(data,np.ndarray):
            raise Exception("new_from_data expects the data to be in a numpy array")
        assert data.shape == (grid.xy_num[0],grid.xy_num[1])
        #check that the data shape is the
        return Data2D(grid, data)

    def value_at_index(self, index:int) -> np.float64:
        assert 0 <= index <= self.grid.num_points(), "Index for data_at_index is out of bounds"
        print(index)
        x,y = self.grid.xy_indices(index)
        print("tried to index" + str(x) + str(y))
        print(self.data[(y,x)])
        return self.data[(y,x)]
    def value(self, point:Point) -> float:

        #TODO: can this calculation be vectorized if the interpolation data is in a numpy array?
        #Seems like this could possibly become a bottleneck if it is not optimized in some way
        #Issue: can't figure outhow to typing in interpolation_data if the entry is a numpy array
        #Question: what is the cost of the np.array([]) operation? is this similar to a zero cost type system
        #in rust or is the data copied to a new object to make the array?
        interpolation_data: interpolation_data = self.grid.get_projected_interpolation_data(point)

        values = np.array(list(map(self.value_at_index,interpolation_data.corners)))
        return (np.dot(values,np.array(interpolation_data.coefficients)))/interpolation_data.normalization

grid = grid2d.new_from_step_size(2, 2, 1, 1, Point.zero(CoordinateSystem.ABSOLUTE_COORDINATES()), 0.001, CoordinateSystem.ABSOLUTE_COORDINATES())

print(grid)
data = np.array([[1,2],[1,2]])
datagrid = Data2D.new_from_data(grid, data)
print(datagrid.value(Point.new(0.25,0.25,CoordinateSystem.ABSOLUTE_COORDINATES())))







