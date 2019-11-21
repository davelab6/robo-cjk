"""
Copyright 2019 Black Foundry.

This file is part of Robo-CJK.

Robo-CJK is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Robo-CJK is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Robo-CJK.  If not, see <https://www.gnu.org/licenses/>.
"""
import math

class PointLocation(object):
    def __init__(self, rfPoint, cont, seg, idx):
        p = Point(rfPoint)
        self.pos = p
        self.rfPoint = rfPoint
        self.cont = cont
        self.seg = seg
        self.idx = idx

class Point(object):
    __slots__ = ('x', 'y')
    def __init__(self, ix=0.0, iy=0.0):
        self.x = ix
        self.y = iy
    def __len__(self): return 2
    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError("coordinate index {} out of range [0,1]".format(i))
    def __repr__(self):
        return "({:f},{:f})".format(self.x, self.y)
    def __str__(self):
        return self.__repr__()
    def __add__(self, rhs): # rhs = right hand side
        return Point(self.x + rhs.x, self.y + rhs.y)
    def __sub__(self, rhs):
        return Point(self.x - rhs.x, self.y - rhs.y)
    def __or__(self, rhs): # dot product
        return (self.x * rhs.x + self.y * rhs.y)
    def __mul__(self, s): # 's' is a number, not a point
        return Point(s * self.x, s * self.y)
    def __rmul__(self, s): # 's' is a number, not a point
        return Point(s * self.x, s * self.y)

    def opposite(self):
        return Point(-self.x, -self.y)
    def rotateCCW(self):
        return Point(-self.y, self.x)
    def squaredLength(self):
        return self.x * self.x + self.y * self.y
    def length(self):
        return math.sqrt(self.squaredLength())

    def sheared(self, angleInDegree):
        r = math.tan(math.radians(angleInDegree))
        return Point(self.x - r*self.y, self.y)
    def absolute(self):
        return Point(abs(self.x), abs(self.y))
    def normalized(self):
        l = self.length()
        if l < 1e-6: return Point(0.0, 0.0)
        return Point(float(self.x)/l, float(self.y)/l)
    def swapAxes(self):
        return Point(self.y, self.x)
    def projectOnX(self):
        return Point(self.x, 0,0)
    def projectOnAxis(self,axis):
        if axis == 0:
            return Point(self.x, 0.0)
        else:
            return Point(0.0, self.y)
    def projectOnY(self):
        return Point(0.0, self.y)