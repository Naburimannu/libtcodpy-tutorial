import libtcodpy as libtcod

import config
import algebra
import map
from components import *
import ai
import spells

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30


def _random_position_in_room(room):
    return algebra.Location(libtcod.random_get_int(0, room.x1+1, room.x2-1),
                            libtcod.random_get_int(0, room.y1+1, room.y2-1))


def _create_room(new_map, room):
    """
    Make the tiles in a rectangle passable
    """
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            new_map.blocked[x][y] = False
            new_map.block_sight[x][y] = False


def _create_h_tunnel(new_map, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        new_map.blocked[x][y] = False
        new_map.block_sight[x][y] = False


def _create_v_tunnel(new_map, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        new_map.blocked[x][y] = False
        new_map.block_sight[x][y] = False


def _random_choice_index(chances):
    """
    choose one option from list of chances, returning its index
    """
    dice = libtcod.random_get_int(0, 1, sum(chances))

    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        if dice <= running_sum:
            return choice
        choice += 1


def _random_choice(chances_dict):
    """
    choose one option from dictionary of chances, returning its key
    """
    chances = chances_dict.values()
    strings = chances_dict.keys()

    return strings[_random_choice_index(chances)]


def _from_dungeon_level(new_map, table):
    # Returns a value that depends on level.
    # The table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if new_map.dungeon_level >= level:
            return value
    return 0


def _place_objects(new_map, room, player):
    max_monsters = _from_dungeon_level(new_map, [[2, 1], [3, 4], [5, 6]])

    monster_chances = {}
    # orc always shows up, even if all other monsters have 0 chance.
    monster_chances['orc'] = 80
    monster_chances['troll'] = _from_dungeon_level(new_map, [[15, 3], [30, 5], [60, 7]])

    max_items = _from_dungeon_level(new_map, [[1, 1], [2, 4]])

    item_chances = {}
    # Healing potion always shows up, even if all other items have 0 chance.
    item_chances['heal'] = 35
    item_chances['lightning'] = _from_dungeon_level(new_map, [[25, 4]])
    item_chances['fireball'] = _from_dungeon_level(new_map, [[25, 6]])
    item_chances['confuse'] = _from_dungeon_level(new_map, [[10, 2]])
    item_chances['sword'] = _from_dungeon_level(new_map, [[5, 4]])
    item_chances['shield'] = _from_dungeon_level(new_map, [[15, 8]])

    num_monsters = libtcod.random_get_int(0, 0, max_monsters)
    for i in range(num_monsters):
        pos = _random_position_in_room(room)

        if not new_map.is_blocked_at(pos):
            choice = _random_choice(monster_chances)
            if choice == 'orc':
                fighter_component = Fighter(hp=20, defense=0, power=4, xp=35, death_function=ai.monster_death)
                ai_component = AI(ai.basic_monster, ai.basic_monster_metadata(player))
                monster = Object(pos, 'o', 'orc', libtcod.desaturated_green,
                                 blocks=True, fighter=fighter_component, ai=ai_component)

            elif choice == 'troll':
                fighter_component = Fighter(hp=30, defense=2, power=8, xp=100, death_function=ai.monster_death)
                ai_component = AI(ai.basic_monster, ai.basic_monster_metadata(player))
                monster = Object(pos, 'T', 'troll', libtcod.darker_green,
                                 blocks=True, fighter=fighter_component, ai=ai_component)

            new_map.objects.append(monster)
            monster.current_map = new_map

    num_items = libtcod.random_get_int(0, 0, max_items)
    for i in range(num_items):
        pos = _random_position_in_room(room)

        if not new_map.is_blocked_at(pos):
            choice = _random_choice(item_chances)
            if choice == 'heal':
                item_component = Item(use_function=spells.cast_heal)
                item = Object(pos, '!', 'healing potion', libtcod.violet, item=item_component)

            elif choice == 'lightning':
                item_component = Item(use_function=spells.cast_lightning)
                item = Object(pos, '#', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)

            elif choice == 'fireball':
                item_component = Item(use_function=spells.cast_fireball)
                item = Object(pos, '#', 'scroll of fireball', libtcod.light_yellow, item=item_component)

            elif choice == 'confuse':
                item_component = Item(use_function=spells.cast_confuse)
                item = Object(pos, '#', 'scroll of confusion', libtcod.light_yellow, item=item_component)

            elif choice == 'sword':
                equipment_component = Equipment(slot='right hand', power_bonus=3)
                item = Object(pos, '/', 'sword', libtcod.sky, equipment=equipment_component)

            elif choice == 'shield':
                equipment_component = Equipment(slot='left hand', defense_bonus=1)
                item = Object(pos, '[', 'shield', libtcod.darker_orange, equipment=equipment_component)

            new_map.objects.insert(0, item)
            item.always_visible = True  # Items are visible even out-of-FOV, if in an explored area


def _build_map(new_map):
    new_map.rng = libtcod.random_new_from_seed(new_map.random_seed)
    num_rooms = 0
    for r in range(MAX_ROOMS):
        w = libtcod.random_get_int(new_map.rng, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(new_map.rng, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = libtcod.random_get_int(new_map.rng, 0, new_map.width - w - 1)
        y = libtcod.random_get_int(new_map.rng, 0, new_map.height - h - 1)

        new_room = map.Room(x, y, w, h)

        failed = False
        for other_room in new_map.rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            # There are no intersections, so this room is valid.
            _create_room(new_map, new_room)
            new_ctr = new_room.center()

            if num_rooms > 0:
                prev_ctr = new_map.rooms[num_rooms-1].center()

                if libtcod.random_get_int(new_map.rng, 0, 1) == 1:
                    _create_h_tunnel(new_map, prev_ctr.x, new_ctr.x, prev_ctr.y)
                    _create_v_tunnel(new_map, prev_ctr.y, new_ctr.y, new_ctr.x)
                else:
                    _create_v_tunnel(new_map, prev_ctr.y, new_ctr.y, prev_ctr.x)
                    _create_h_tunnel(new_map, prev_ctr.x, new_ctr.x, new_ctr.y)

            new_map.rooms.append(new_room)
            num_rooms += 1

    # Create stairs at the center of the last room.
    stairs = Object(new_ctr, '<', 'stairs down', libtcod.white, always_visible=True)
    stairs.destination = None
    stairs.dest_position = None
    new_map.objects.insert(0, stairs)
    new_map.portals.insert(0, stairs)

    # Test - tunnel off the right edge
    # _create_h_tunnel(new_map, new_ctr.x, new_map.width-1, new_ctr.y)


def make_map(player, dungeon_level):
    """
    Creates a new simple map at the given dungeon level.
    Sets player.current_map to the new map, and adds the player as the first
    object.
    """
    new_map = map.Map(config.MAP_HEIGHT, config.MAP_WIDTH, dungeon_level)
    new_map.objects.append(player)
    player.current_map = new_map
    player.camera_position = algebra.Location(0, 0)
    new_map.random_seed = libtcod.random_save(0)
    _build_map(new_map)
    for new_room in new_map.rooms:
        _place_objects(new_map, new_room, player)
    player.pos = new_map.rooms[0].center()

    new_map.initialize_fov()
    return new_map


def _test_map_repeatability():
    """
    Require that two calls to _build_map() with the same seed produce the
    same corridors and rooms.
    """
    map1 = map.Map(config.MAP_HEIGHT, config.MAP_WIDTH, 3)
    map1.random_seed = libtcod.random_save(0)
    _build_map(map1)

    map2 = map.Map(config.MAP_HEIGHT, config.MAP_WIDTH, 3)
    map2.random_seed = map1.random_seed
    _build_map(map2)

    assert map1.block_sight == map2.block_sight
    assert map1.blocked == map2.blocked
    for i in range(len(map1.rooms)):
        assert map1.rooms[i] == map2.rooms[i]

if __name__ == '__main__':
    _test_map_repeatability()
    print('Cartographer tests complete.')
