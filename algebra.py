import math


class Rect(object):
    """
    A rectangle on the map. used to characterize a room.
    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + max(0, w)
        self.y2 = y + max(0, h)

    def __eq__(self, other):
        return (self.x1 == other.x1 and
                self.x2 == other.x2 and
                self.y1 == other.y1 and
                self.y2 == other.y2)

    def center(self):
        return Location((self.x1 + self.x2) / 2,
                        (self.y1 + self.y2) / 2)

    def intersect(self, other):
        """
        Returns true if two rectangles intersect.
        """
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

    def contains(self, location):
        return (location.x > self.x1 and location.x <= self.x2 and
                location.y > self.y1 and location.y <= self.y2)


class Location(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.x == other.x and self.y == other.y)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        return Location(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Location(self.x - other.x, self.y - other.y)

    def bound(self, rect):
        if (self.x > rect.x2):
            self.x = rect.x2
        if (self.y > rect.y2):
            self.y = rect.y2
        if (self.x < rect.x1):
            self.x = rect.x1
        if (self.y < rect.y1):
            self.y = rect.y1

    def to_string(self):
        return str(self.x) + ', ' + str(self.y)


class Direction(object):
    def __init__(self, x, y, left = None, right = None):
        self.x = x
        self.y = y
        self.left = left
        self.right = right

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.x == other.x and self.y == other.y)

    def __ne__(self, other):
        return not self.__eq__(other)

    def normalize(self):
        """
        Normalize to length 1 (preserving direction), then round and
        convert to integer so the movement is restricted to the map grid.
        """
        distance = math.sqrt(self.x ** 2 + self.y ** 2)
        self.x = int(round(self.x / distance))
        self.y = int(round(self.y / distance))


north = Direction(0, -1)
south = Direction(0, 1)
west = Direction(-1, 0)
east = Direction(1, 0)
northwest = Direction(-1, -1)
northeast = Direction(1, -1)
southwest = Direction(-1, 1)
southeast = Direction(1, 1)

north.left = northwest
northwest.left = west
west.left = southwest
southwest.left = south
south.left = southeast
southeast.left = east
east.left = northeast
northeast.left = north

north.right = northeast
northeast.right = east
east.right = southeast
southeast.right = south
south.right = southwest
southwest.right = west
west.right = northwest
northwest.right = north
