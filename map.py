import libtcodpy as libtcod

import algebra

class Room(algebra.Rect):
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
        self.portals = []

        self.random_seed = None
        self.rng = None

        self.fov_map = None

        # Maps default to blocked & unexplored
        self.blocked = [[True for y in range(height)] for x in range(width)]
        self._explored = [[False for y in range(height)] for x in range(width)]
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

    def is_blocked_at(self, pos):
        return self.is_blocked(pos.x, pos.y)

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

    def is_explored(self, pos):
        return self._explored[pos.x][pos.y]

    def explore(self, pos):
        self._explored[pos.x][pos.y] = True
