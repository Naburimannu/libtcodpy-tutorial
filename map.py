import libtcodpy as libtcod


class Rect(object):
    """
    A rectangle on the map. used to characterize a room.
    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        """
        Returns true if two rectangles intersect.
        """
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Room(Rect):
    def __init__(self, x, y, w, h):
        super(self.__class__, self).__init__(x, y, w, h)

    def isIn(self, x, y):
        if (x > self.x1 and x <= self.x2 and 
            y > self.y1 and y < self.y2):
            return True

        return False


class Map(object):
    def __init__(self, height, width, dungeon_level):
        self.height = height
        self.width = width
        self.dungeon_level = dungeon_level
        self.objects = []
        self.rooms = []

        self.stairs = None
        self.fov_map = None

        # Maps default to blocked & unexplored
        self.blocked = [[True for y in range(height)] for x in range(width)]
        self.explored = [[False for y in range(height)] for x in range(width)]
        self.block_sight = [[True for y in range(height)] for x in range(width)]

    def initialize_fov(self):
        # After being loaded from savegame, we need to make sure the C state
        # is reinitialized, so we can't just set fov_needs_recompute in
        # __init__().
        self.fov_needs_recompute = True
        self.fov_map = libtcod.map_new(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                libtcod.map_set_properties(
                    self.fov_map, x, y,
                    not self.block_sight[x][y], not self.blocked[x][y])

    def is_blocked(self, x, y):
        """
        Returns true if impassible map terrain or any blocking objects
        are at (x, y).
        """
        if self.blocked[x][y]:
            return True

        for object in self.objects:
            if object.blocks and object.x == x and object.y == y:
                return True

        return False
