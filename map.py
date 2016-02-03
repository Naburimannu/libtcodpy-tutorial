import libtcodpy as libtcod # for field of view management

class Tile(object):
    """
    A tile of the map and its properties.
    """
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
 
        #all tiles start unexplored
        self.explored = False
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

    # Could encode this further to shrink save-file sizes,
    # or consider changing array-of-structs to struct-of-arrays
    # if actual compression is worthwhile.
    def __getstate__(self):
        return [self.blocked, self.explored, self.block_sight]

    def __setstate__(self, values):
        self.blocked = values[0]
        self.explored = values[1]
        self.block_sight = values[2]

    # Avoid allocating a __dict__, which can be 2kB on some
    # Python implementations but seems to only be 8B for
    # Python 2.7 on Windows?
    __slots__ = ['blocked', 'explored', 'block_sight']

class Map(object):
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.objects = []
        # Default to blocked tiles.
        self.tiles = [[ Tile(True)
                 for y in range(height) ]
               for x in range(width) ]
        # TODO: do stairs get cloned when saved?
        self.stairs = None
        self.fov_map = None

    def initialize_fov(self):
        # After being loaded from savegame, we need to make sure the C state
        # is reinitialized, so we can't just set this in __init__().
        self.fov_needs_recompute = True
        self.fov_map = libtcod.map_new(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                libtcod.map_set_properties(self.fov_map, x, y, not self.tiles[x][y].block_sight, not self.tiles[x][y].blocked)
