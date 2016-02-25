#!/usr/bin/python
#
# libtcod python tutorial
#

import libtcodpy as libtcod
import shelve
import cProfile

import config
import log
import algebra
from components import *
import renderer
import interface
import actions
import ai
import ui
import cartographer

INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

# Experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150


def try_pick_up(player):
    for object in player.current_map.objects:
        if object.x == player.x and object.y == player.y and object.item:
            return actions.pick_up(player, object)
    return False


def try_drop(player):
    chosen_item = inventory_menu(
        player,
        'Press the key next to an item to drop it, or any other to cancel.\n')
    if chosen_item is not None:
        actions.drop(player, chosen_item.owner)
        return True
    return False


def try_use(player):
    chosen_item = inventory_menu(
        player,
        'Press the key next to an item to use it, or any other to cancel.\n')
    if chosen_item is not None:
        actions.use(player, chosen_item.owner)
        return True
    return False


def player_move_or_attack(player, direction, try_running):
    """
    Returns true if the player makes an attack or moves successfully;
    false if the attempt to move fails.
    """
    goal = player.pos + direction
    if (goal.x < 0 or goal.y < 0 or
            goal.x >= player.current_map.width or
            goal.y >= player.current_map.height):
        log.message(player.current_map.out_of_bounds(goal))
        return False

    # Is there an attackable object?
    target = None
    for object in player.current_map.objects:
        if object.fighter and object.pos == goal:
            target = object
            break

    if target is not None:
        actions.attack(player.fighter, target)
        return True
    else:
        if actions.move(player, direction):
            player.current_map.fov_needs_recompute = True
            if try_running:
                player.game_state = 'running'
                player.run_direction = direction
            return True

    return False


def inventory_menu(player, header):
    """
    Show a menu with each item of the inventory as an option.
    """
    if len(player.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for obj in player.inventory:
            text = obj.name
            # Show additional information, in case it's equipped.
            if obj.item.count > 1:
                text = text + ' (x' + str(obj.item.count) + ')'
            if obj.equipment and obj.equipment.is_equipped:
                text = text + ' (on ' + obj.equipment.slot + ')'
            options.append(text)

    index = renderer.menu(header, options, INVENTORY_WIDTH)

    if index is None or len(player.inventory) == 0:
        return None
    return player.inventory[index].item


def display_character_info(player):
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    base_attack_power = player.fighter.base_power
    attack_power = player.fighter.power
    base_defense = player.fighter.base_defense
    defense = player.fighter.defense
    renderer.msgbox('Character Information\n\nLevel: ' + str(player.level) +
                    '\nExperience: ' + str(player.fighter.xp) +
                    '\nExperience to level up: ' + str(level_up_xp) +
                    '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
                    '\nAttack: ' + str(attack_power) + 
                    ' (' + str(base_attack_power) + ' + ' + str(attack_power - base_attack_power) + ')'
                    '\nDefense: ' + str(defense) + 
                    ' (' + str(base_defense) + ' + ' + str(defense - base_defense) + ')',
                    CHARACTER_SCREEN_WIDTH)


def display_help():
    renderer.msgbox('numpad keys to move, or:\n' +
                    '  h (west) j (south) k (north) l (east)\n' +
                    '  y (nw) u (ne) b (sw) n (se) . (wait)\n' +
                    '  shift-move to run\n' +
                    'g/get, d/drop, c/character information\n' +
                    'i/inventory, equip, or use item\n' +
                    '</traverse stairs\n' +
                    'control-p/scroll through old log messages\n',
                    INVENTORY_WIDTH)


def try_stairs(player):
    for f in player.current_map.portals:
        if f.pos == player.pos:
            if f.destination is None:
                f.destination = next_level(player, f)
                # player.pos was changed by next_level()!
                f.dest_position = player.pos
                return True
            else:
                revisit_level(player, f)
                return True
    return False


def _running_lookahead(player):
    """
    Returns true if the upcoming terrain doesn't match the current terrain,
    or if there's an object in the upcoming space.
    If the player stops running when true, they should stop in the doorway to
    a room, or just before rounding a bend in a corridor or entering an
    intersection.
    """
    map = player.current_map
    dir = player.run_direction
    if (map.terrain_at(player.pos) != map.terrain_at(player.pos + dir) or
            (map.terrain_at(player.pos + dir.left.left) != map.terrain_at(player.pos + dir.left)) or
            (map.terrain_at(player.pos + dir.right.right) != map.terrain_at(player.pos + dir.right))):
        return True
    for o in map.objects:
        if (o.pos == player.pos + dir or
                o.pos == player.pos + dir.left or
                o.pos == player.pos + dir.right):
            return True
    return False


def handle_keys(player, key):
    """
    Returns 'playing', 'didnt-take-turn', or 'exit'.
    """
    key_char = chr(key.c)

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'

    elif key_char == 'p' and (key.lctrl or key.rctrl):
        interface.log_display()

    if player.game_state == 'running':
        if (player.endangered or
                key.vk != libtcod.KEY_NONE or
                _running_lookahead(player) or
                not player_move_or_attack(player, player.run_direction, False)):
            player.game_state = 'playing'
            return 'didnt-take-turn'

    if player.game_state == 'playing':
        # movement keys
        (parsed, direction, shift) = interface.parse_move(key)
        if parsed:
            if direction:
                player_move_or_attack(player, direction, shift)
            else:
                # Do nothing
                pass
        else:
            if key_char == 'g':
                try_pick_up(player)
            if key_char == 'i':
                try_use(player)
            if key_char == 'd':
                try_drop(player)
            if key_char == 'c':
                display_character_info(player)
            if key_char == '<':
                try_stairs(player)
            if (key_char == '?' or key.vk == libtcod.KEY_F1):
                display_help()

            return 'didnt-take-turn'


def check_level_up(player):
    """
    If the player has enough experience, level up immediately.
    """
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        player.level += 1
        player.fighter.xp -= level_up_xp
        log.message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)

        choice = None
        while choice is None:
            choice = renderer.menu(
                'Level up! Choose a stat to raise:\n',
                ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
                 'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
                 'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'],
                LEVEL_SCREEN_WIDTH)

        if choice == 0:
            player.fighter.base_max_hp += 20
            player.fighter.hp += 20
        elif choice == 1:
            player.fighter.base_power += 1
        elif choice == 2:
            player.fighter.base_defense += 1


def player_death(player):
    """
    End the game!
    """
    log.message('You died!', libtcod.red)
    player.game_state = 'dead'

    # For added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red


def save_game(player):
    """
    Save the game to file "savegame";
    overwrites any existing data.
    """
    file = shelve.open('savegame', 'n')
    file['current_map'] = player.current_map
    file['player_index'] = player.current_map.objects.index(player)
    file['game_msgs'] = log.game_msgs
    file.close()


def load_game():
    """
    Loads from "savegame".
    Returns the player object.
    """
    file = shelve.open('savegame', 'r')
    current_map = file['current_map']
    player = current_map.objects[file['player_index']]
    log.game_msgs = file['game_msgs']
    file.close()

    current_map.initialize_fov()

    return player


def new_game():
    """
    Starts a new game, with a default player on level 1 of the dungeon.
    Returns the player object.
    """
    # Must initialize the log before we do anything that might emit a message.
    log.init()

    fighter_component = Fighter(hp=100, defense=1, power=2, xp=0, death_function=player_death)
    player = Object(algebra.Location(0, 0), '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
    player.inventory = []
    player.level = 1
    player.game_state = 'playing'
    # True if there's a (hostile) fighter in FOV
    player.endangered = False

    item_component = Item(description='A leaf-shaped bronze knife; provides +2 Attack')
    equipment_component = Equipment(slot='right hand', power_bonus=2)
    obj = Object(algebra.Location(0, 0), '-', 'dagger', libtcod.sky,
                 item=item_component, equipment=equipment_component)
    player.inventory.append(obj)
    actions.equip(player, equipment_component, False)
    obj.always_visible = True

    cartographer.make_map(player, 1)
    renderer.clear_console()
    renderer.update_camera(player)

    log.message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
    log.message('Press ? or F1 for help.')

    return player


def next_level(player, portal):
    """
    Advance to the next level (changing player.current_map).
    Heals the player 50%.
    Returns the Map of the new level.
    """
    log.message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
    actions.heal(player.fighter, player.fighter.max_hp / 2)

    log.message('After a rare moment of peace, you descend deeper into the heart of the dungeon...', libtcod.red)
    old_map = player.current_map
    cartographer.make_map(player, player.current_map.dungeon_level + 1)
    renderer.clear_console()
    renderer.update_camera(player)

    # Create the up stairs at the current position.
    stairs = Object(player.pos, '>', 'stairs up', libtcod.white, always_visible=True)
    stairs.destination = old_map
    stairs.dest_position = portal.pos
    player.current_map.objects.insert(0, stairs)
    player.current_map.portals.insert(0, stairs)

    return player.current_map


def revisit_level(player, portal):
    """
    Return to a level the player has previously visited (changing player.current_map).
    Does *not* heal the player.
    """
    player.current_map = portal.destination
    player.pos = portal.dest_position
    # Call to initialize_fov() should be redundant but in practice seems to have
    # worked around an intermittent bug.
    player.current_map.initialize_fov()
    player.current_map.fov_needs_recompute = True
    renderer.update_camera(player)
    renderer.clear_console()


def play_game(player):
    """
    Main loop.
    """
    player_action = None

    ui.init()

    while not libtcod.console_is_window_closed():
        (key, mouse) = interface.poll()
        renderer.render_all(player, (mouse.cx, mouse.cy))
        player.current_map.fov_needs_recompute = False

        libtcod.console_flush()

        check_level_up(player)

        # Erase all objects at their old locations, before they move.
        for object in player.current_map.objects:
            renderer.clear_object(player, object)

        player_action = handle_keys(player, key)
        if player_action == 'exit':
            save_game(player)
            break

        if (player_action != 'didnt-take-turn' and
            (player.game_state == 'playing' or
             player.game_state == 'running')):
            for object in player.current_map.objects:
                if object.ai:
                    object.ai.take_turn(player)

if __name__ == '__main__':
    renderer.renderer_init()
    # cProfile.run('renderer.main_menu(new_game, play_game, load_game)')
    renderer.main_menu(new_game, play_game, load_game)
