import math


class Location(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.x == other.x and self.y == other.y)

    def __ne__(self, other):
        return not self.__eq__(other)


class Direction(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

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

