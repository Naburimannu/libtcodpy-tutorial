import libtcodpy as libtcod

import algebra


class Room(algebra.Rect):
    def __init__(self, x, y, w, h):
        super(self.__class__, self).__init__(x, y, w, h)


class Terrain(object):
    def __init__(self, name, display_name, icon, seen_color, unseen_color, blocks, blocks_sight):
        self.name = name
        self.display_name = display_name  # text displayed on mouseover
        self.icon = icon  # character drawn on screen
        self.seen_color = seen_color
        self.unseen_color = unseen_color
        self.blocks = blocks
        self.blocks_sight = blocks_sight

terrain_types = [
        Terrain('wall', None, None, libtcod.Color(130, 110, 50), libtcod.Color(0, 0, 100), True, True),
        Terrain('ground', None, None, libtcod.Color(200, 180, 50), libtcod.Color(50, 50, 150), False, False)
            ]


class Map(object):
    """
    A (width x height) region of tiles, presumably densely occupied.
    Has a dungeon_level and a collection of (rectangular) rooms.
    Has portals connecting to other maps.
    """
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

        # Maps default to walls (blocked) & unexplored
        self.terrain = [[0 for y in range(height)] for x in range(width)]
        self._explored = [[False for y in range(height)] for x in range(width)]

    def initialize_fov(self):
        """
        Set up corresponding C state for libtcod.
        Must be called explicitly after loading from savegame or entering from
        another map.
        """
        self.fov_needs_recompute = True
        self.fov_map = libtcod.map_new(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                libtcod.map_set_properties(
                    self.fov_map, x, y,
                    not terrain_types[self.terrain[x][y]].blocks_sight,
                    not terrain_types[self.terrain[x][y]].blocks)

    def terrain_at(self, pos):
        """
        Returns the Terrain at (pos).
        position *must* be within the current map.
        """
        return terrain_types[self.terrain[pos.x][pos.y]]

    def is_blocked_at(self, pos):
        """
        Returns true if impassible map terrain or any blocking objects
        are at (x, y).
        """
        if terrain_types[self.terrain[pos.x][pos.y]].blocks:
            return True
        for object in self.objects:
            if object.blocks and object.pos == pos:
                return True
        return False

    def is_explored(self, pos):
        return self._explored[pos.x][pos.y]

    def explore(self, pos):
        self._explored[pos.x][pos.y] = True

    def out_of_bounds(self, pos):
        return "You can't go that way!"
