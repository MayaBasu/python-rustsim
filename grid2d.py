import dataclasses
from typing import Optional, Tuple

import numpy as np
from fontTools.tfmLib import UNREACHABLE
from geometry import Point
from geometry import CoordinateSystem
from runtimeconstants import Parameters

@dataclasses.dataclass
class FourCorners():
    one: int
    two: int
    three: int
    four: int
    def get_corners(self) -> list[int]:
        return [self.one,self.two,self.three,self.four]
@dataclasses.dataclass
class TwoCorners():
    one: int
    two: int
    def get_corners(self) -> list[int]:
        return [self.one,self.two]
@dataclasses.dataclass
class OneCorner():
    one: int
    def get_corners(self) -> list[int]:
        return [self.one]

corners = FourCorners | TwoCorners | OneCorner

@dataclasses.dataclass
class interpolation_data():
    corners: corners
    coefficients: np.array() #add typing for arrays?
    normalization: float

@dataclasses.dataclass
class grid2d():
    coordinate_system: coordinate_system
    xy_num: [int, int]
    xy_step_size: [float, float]
    center: Point
    snap_precision: float

    @staticmethod
    def new_from_step_size(x_num,
                           y_num,
                           x_step_size,
                           y_step_size,
                           center:Point,
                           relative_snap_precision,
                           coordinate_system) -> grid2d:

        return grid2d(
            coordinate_system,
            [x_num,y_num],
            [x_step_size, y_step_size],
            center,
            relative_snap_precision*np.min([x_step_size, y_step_size])
        )

    def num_points(self) -> int:
        return self.xy_num[0]*self.xy_num[1]

    def xy_indices(self, grid_number: int) -> Tuple[int,int]:
        assert grid_number <= self.num_points()-1
        x_index = grid_number % self.xy_num[0]
        y_index = (grid_number - x_index) / self.xy_num[0]
        return int(x_index), int(y_index)

    def grid_number(self, x_index: int, y_index: int) -> int:
        assert x_index <= self.xy_num[0] - 1
        assert y_index <= self.xy_num[1] - 1
        return int(y_index * self.xy_num[0] + x_index)

    def size(self) -> Point:
        [x_num, y_num] = self.xy_num
        [x_step, y_step] = self.xy_step_size

        return Point.new(
            (x_num - 1)* x_step,
            (y_num - 1)* y_step,
            self.coordinate_system)

    def corner(self)-> Point:
        half_size = self.size() / 2.0
        return self.center - half_size

    def locate(self, grid_number: int) -> Point:
        x_index, y_index = self.xy_indices(grid_number)
        delta_x = x_index * self.xy_step_size[0]
        delta_y = y_index * self.xy_step_size[1]
        corner = self.corner()
        return Point(
            corner.x + delta_x,
            corner.y + delta_y,
            self.coordinate_system
        )

    def is_point_inside(self, point: Point)-> bool:
        point = point.transform_to(self.coordinate_system);
        half_grid_size = self.size() / 2.0;
        delta = point - self.center;
        if (abs(delta.x) > (half_grid_size.x + self.snap_precision)) | \
            (abs(delta.y) > (half_grid_size.y + self.snap_precision)):
            return False
        else:
            return True

    def project_inside(self, point: Point) -> Point:
        point = point.transform_to(self.coordinate_system)
        corner = self.corner()
        if point.x < corner.x - self.snap_precision:
            new_x = corner.x
        if point.x > corner.x + self.size().x + self.snap_precision:
            new_x = corner.x + self.size().x
        else:
            new_x = point.x
        if point.y < corner.y - self.snap_precision:
            new_y = corner.y
        if point.y > corner.y + self.size().y + self.snap_precision:
            new_y = corner.y + self.size().y
        else:
            new_y = point.y
        return Point(
            new_x,
            new_y,
            self.coordinate_system)

    def fit_grid(self, point: Point, fractional_residual: bool) -> Optional[int,int,float,float]:
        point = point.transform_to(self.coordinate_system)
        if not self.is_point_inside(point):
            raise Exception("Could not grid point because it was outside of the grid, use projected fit grid instead")
        delta = point - self.corner()
        step = Point(
            self.xy_step_size[0],
            self.xy_step_size[1],
            self.coordinate_system)

        modulus = round(delta / step)
        if fractional_residual:
            residual = delta / step - modulus
        else:
            residual = delta - modulus * step

        return (modulus.x, modulus.y,residual.x, residual.y)

    def project_fit_grid(self, point:Point, fractional_residual: bool) -> Optional[int,int, float,float]:
        return self.fit_grid(self.project_inside(point), fractional_residual)

    def snap(self, point: Point) -> Optional[int]:
        try:
            x_mod, y_mod, x_res, y_res = self.fit_grid(point, False)
        except ValueError:
            raise Exception("Can not snap point to grid which is outside of the grid")
        if abs(x_res) > Parameters.precision or abs(y_res) > Parameters.precision:
            raise Exception("Failed to snap point due to it being further than the grid's snap_precision from any grid point")

        return self.grid_number(x_mod, y_mod)

    def find_corners(self, point: Point) -> Optional[corners]:

        point = point.transform_to(self.coordinate_system)
        try:
            x_mod, y_mod, x_res, y_res = self.fit_grid(point, False)
        except ValueError:
            raise Exception("Tried to find corners of a point located outside of grid, try projecting first")

        #case one  - snap to single point
        if (abs(x_res) < Parameters.precision) and (abs(y_res) < Parameters.precision):
            return OneCorner(int(self.grid_number(x_mod, y_mod)))

        delta = point - self.corner()
        step = Point(
        self.xy_step_size[0],
        self.xy_step_size[1],
        self.coordinate_system)
        lower_left_corner = [int((delta / step).floor().x), int((delta / step).floor().y)]

        #case two, point is between two vertical points
        if (abs(x_res) < Parameters.precision):
            return TwoCorners(
                self.grid_number(x_mod, lower_left_corner[1]),
                self.grid_number(x_mod, lower_left_corner[1] + 1)
            )
        #case three, point is between to horizontal points
        if (abs(y_res) < Parameters.precision):
            return TwoCorners(
                self.grid_number(lower_left_corner[0], y_mod),
                self.grid_number(lower_left_corner[0] + 1, y_mod))
        #case four, point is inside of a four corner box
        else:
            return FourCorners(
                self.grid_number(lower_left_corner[0], lower_left_corner[1]),
                self.grid_number(lower_left_corner[0], lower_left_corner[1] + 1),
                self.grid_number(lower_left_corner[0] + 1, lower_left_corner[1] + 1),
                self.grid_number(lower_left_corner[0] + 1, lower_left_corner[1])
            )

    def get_interpolation_data(self, point: Point) -> Optional[interpolation_data]:
        #Using the Wikipedia conventions: https: // en.wikipedia.org / wiki / Bilinear_interpolation
        #Except y-axis is flipped
        point = point.transform_to(self.coordinate_system)
        corners = self.find_corners(point)
        print(corners)
        if isinstance(corners, FourCorners):
            [Q12, Q11, Q21, Q22] = corners.get_corners()

            Q12point = self.locate(Q12)
            Q21point = self.locate(Q21)
            (x1, y2) = (Q12point.x, Q12point.y)
            (x2, y1) = (Q21point.x, Q21point.y)

            point = point.transform_to(self.coordinate_system)
            x = point.x
            y = point.y

            c11 = -(x2 - x) * (y2 - y)
            c12 = -(x2 - x) * (y - y1)
            c21 = -(x - x1) * (y2 - y)
            c22 = -(x - x1) * (y - y1)
            normalization = self.xy_step_size[0] * self.xy_step_size[1];

            return interpolation_data(
                [Q12, Q11, Q21, Q22],
                [c12, c11, c21, c22],
                normalization
            )
        if isinstance(corners, TwoCorners):
            [Q1, Q2] = corners.get_corners()

            Q1point = self.locate(Q1)
            Q2point = self.locate(Q2)
            (x1, y1) = (Q1point.x, Q1point.y)
            (x2, y2) = (Q2point.x, Q2point.y)

            point = point.transform_to(self.coordinate_system)
            x = point.x;
            y = point.y;

            if (abs(x1 - x2) < 2.0 * Parameters.precision) and (abs(y1 - y2) > 2.0 * Parameters.precision):
            #Case: the corners are above and below the point
                c1 = abs(y2 - y);
                c2 = abs(y1 - y);
                normalization = self.xy_step_size[1];
                return interpolation_data(
                    [Q1, Q2],
                    [c1, c2],
                    normalization
                )
            if (abs(x1 - x2) > 2.0 * Parameters.precision) and (abs()(y1 - y2) < 2.0 * Parameters.precision):
                #Case: corners are on the sides of the point
                c1 = abs(x2 - x);
                c2 = abs(x1 - x);
                normalization = self.xy_step_size[0];
                return interpolation_data(
                    [Q1, Q2],
                    [c1, c2],
                    normalization
                )
            else:
                #This is unreachable since this case should be covered by one_corner, not two_corners
                assert UNREACHABLE
        if isinstance(corners, OneCorner):
            [Q1] = corners.get_corners()
            return interpolation_data(
                [Q1],
                [1],
                1
            )
        else:
            raise Exception("Could not get interpolationd ata due to point being outside grid, try projected interpolation coefficients")

    def get_projected_interpolation_data(self, point:Point) -> Optional[interpolation_data]:
        point = self.project_inside(point)
        return self.get_interpolation_data(point)



