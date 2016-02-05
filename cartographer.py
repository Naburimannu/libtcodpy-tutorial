import libtcodpy as libtcod

import config
import map
from components import *
import ai
import spells
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

class Rect:
    #a rectangle on the map. used to characterize a room.
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
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
 

def _create_room(new_map, room):
    """
    Make the tiles in a rectangle passable
    """
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            new_map.blocked[x][y] = False
            new_map.block_sight[x][y] = False
 
def _create_h_tunnel(new_map, x1, x2, y):
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        new_map.blocked[x][y] = False
        new_map.block_sight[x][y] = False
 
def _create_v_tunnel(new_map, y1, y2, x):
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        new_map.blocked[x][y] = False
        new_map.block_sight[x][y] = False
 
def _random_choice_index(chances):  #choose one option from list of chances, returning its index
    #the dice will land on some number between 1 and the sum of the chances
    dice = libtcod.random_get_int(0, 1, sum(chances))
 
    #go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
 
        #see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1
 
def _random_choice(chances_dict):
    #choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()
 
    return strings[_random_choice_index(chances)]
 
def _from_dungeon_level(new_map, table):
    #returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if new_map.dungeon_level >= level:
            return value
    return 0
 
def _place_objects(new_map, room):
    #this is where we decide the chance of each monster or item appearing.
 
    #maximum number of monsters per room
    max_monsters = _from_dungeon_level(new_map, [[2, 1], [3, 4], [5, 6]])
 
    #chance of each monster
    monster_chances = {}
    monster_chances['orc'] = 80  #orc always shows up, even if all other monsters have 0 chance
    monster_chances['troll'] = _from_dungeon_level(new_map, [[15, 3], [30, 5], [60, 7]])
 
    #maximum number of items per room
    max_items = _from_dungeon_level(new_map, [[1, 1], [2, 4]])
 
    #chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    item_chances['heal'] = 35  #healing potion always shows up, even if all other items have 0 chance
    item_chances['lightning'] = _from_dungeon_level(new_map, [[25, 4]])
    item_chances['fireball'] =  _from_dungeon_level(new_map, [[25, 6]])
    item_chances['confuse'] =   _from_dungeon_level(new_map, [[10, 2]])
    item_chances['sword'] =     _from_dungeon_level(new_map, [[5, 4]])
    item_chances['shield'] =    _from_dungeon_level(new_map, [[15, 8]])
 
 
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, max_monsters)
 
    for i in range(num_monsters):
        #choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not new_map.is_blocked(x, y):
            choice = _random_choice(monster_chances)
            if choice == 'orc':
                #create an orc
                fighter_component = Fighter(hp=20, defense=0, power=4, xp=35, death_function=ai.monster_death)
                ai_component = AI(ai.basic_monster)
 
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                                 blocks=True, fighter=fighter_component, ai=ai_component)
 
            elif choice == 'troll':
                #create a troll
                fighter_component = Fighter(hp=30, defense=2, power=8, xp=100, death_function=ai.monster_death)
                ai_component = AI(ai.basic_monster)
 
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
                                 blocks=True, fighter=fighter_component, ai=ai_component)
 
            new_map.objects.append(monster)
            monster.current_map = new_map
 
    #choose random number of items
    num_items = libtcod.random_get_int(0, 0, max_items)
 
    for i in range(num_items):
        #choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not new_map.is_blocked(x, y):
            choice = _random_choice(item_chances)
            if choice == 'heal':
                #create a healing potion
                item_component = Item(use_function=spells.cast_heal)
                item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
 
            elif choice == 'lightning':
                #create a lightning bolt scroll
                item_component = Item(use_function=spells.cast_lightning)
                item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
 
            elif choice == 'fireball':
                #create a fireball scroll
                item_component = Item(use_function=spells.cast_fireball)
                item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, item=item_component)
 
            elif choice == 'confuse':
                #create a confuse scroll
                item_component = Item(use_function=spells.cast_confuse)
                item = Object(x, y, '#', 'scroll of confusion', libtcod.light_yellow, item=item_component)
 
            elif choice == 'sword':
                #create a sword
                equipment_component = Equipment(slot='right hand', power_bonus=3)
                item = Object(x, y, '/', 'sword', libtcod.sky, equipment=equipment_component)
 
            elif choice == 'shield':
                #create a shield
                equipment_component = Equipment(slot='left hand', defense_bonus=1)
                item = Object(x, y, '[', 'shield', libtcod.darker_orange, equipment=equipment_component)
 
            new_map.objects.insert(0, item)
            item.always_visible = True  #items are visible even out-of-FOV, if in an explored area
 
 
def make_map(player, dungeon_level):
    """
    Creates a new simple map at the given dungeon level.
    Sets player.current_map to the new map, and adds the player as the first
    object.
    """
    new_map = map.Map(config.MAP_HEIGHT, config.MAP_WIDTH, dungeon_level)
    new_map.objects.append(player)
    player.current_map = new_map
 
    rooms = []
    num_rooms = 0
 
    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, new_map.width - w - 1)
        y = libtcod.random_get_int(0, 0, new_map.height - h - 1)
 
        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)
 
        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
 
        if not failed:
            #this means there are no intersections, so this room is valid
 
            #"paint" it to the map's tiles
            _create_room(new_map, new_room)
 
            #add some contents to this room, such as monsters
            _place_objects(new_map, new_room)
 
            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()
 
            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    _create_h_tunnel(new_map, prev_x, new_x, prev_y)
                    _create_v_tunnel(new_map, prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    _create_v_tunnel(new_map, prev_y, new_y, prev_x)
                    _create_h_tunnel(new_map, prev_x, new_x, new_y)
 
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1
 
    #create stairs at the center of the last room
    new_map.stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, always_visible=True)
    new_map.objects.insert(0, new_map.stairs)

    new_map.initialize_fov()
    return new_map
 