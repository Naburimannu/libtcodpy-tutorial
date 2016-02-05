#!/usr/bin/python
#
# libtcod python tutorial
#
 
import libtcodpy as libtcod
import shelve
 
import config
import log
from components import *
import renderer
import actions
import ai
import ui
import cartographer

INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

def pick_up(actor, o):
    """
    Add an Object to the actor's inventory and remove from the map.
    """
    if len(actor.inventory) >= 26:
        log.message(actor.name.capitalize() + ' inventory is full, cannot pick up ' + o.owner.name + '.', libtcod.red)
    else:
        actor.inventory.append(o)
        actor.current_map.objects.remove(o)
        log.message(actor.name.capitalize() + ' picked up a ' + o.name + '!', libtcod.green)
 
        #special case: automatically equip, if the corresponding equipment slot is unused
        equipment = o.equipment
        if equipment and get_equipped_in_slot(actor, equipment.slot) is None:
            equip(actor, equipment)
 
def drop(actor, o):
    """
    Remove an Object from the actor's inventory and add it to the map
    at the player's coordinates.
    If it's equipment, dequip before dropping.
    """
    if o.equipment:
        dequip(actor, o.equipment)
 
    actor.current_map.objects.append(o)
    actor.inventory.remove(o)
    o.x = actor.x
    o.y = actor.y
    log.message(actor.name.capitalize() + ' dropped a ' + o.name + '.', libtcod.yellow)
 
def use(actor, o):
    """
    If the object has the Equipment component, toggle equip/dequip.
    Otherwise invoke its use_function and (if not cancelled) destroy it.
    """
    if o.equipment:
        toggle_equip(actor, o.equipment)
        return
 
    if o.item.use_function is None:
        log.message('The ' + o.name + ' cannot be used.')
    else:
        if o.item.use_function(actor) != 'cancelled':
            actor.inventory.remove(o)
 

def toggle_equip(actor, eqp):
    if eqp.is_equipped:
        dequip(actor, eqp)
    else:
        equip(actor, eqp)
 
def equip(actor, eqp):
    """
    Equip the object (and log).
    Ensure only one object per slot.
    """
    old_equipment = get_equipped_in_slot(actor, eqp.slot)
    if old_equipment is not None:
        dequip(actor, old_equipment)
 
    eqp.is_equipped = True
    log.message('Equipped ' + eqp.owner.name + ' on ' + eqp.slot + '.', libtcod.light_green)
 
def dequip(actor, eqp):
    """
    Dequip the object (and log).
    """
    if not eqp.is_equipped: return
    eqp.is_equipped = False
    log.message('Dequipped ' + eqp.owner.name + ' from ' + eqp.slot + '.', libtcod.light_yellow)
 
def get_equipped_in_slot(actor, slot):
    """
    Returns Equipment in a slot, or None.
    """
    if hasattr(actor, 'inventory'):
        for obj in actor.inventory:
            if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
                return obj.equipment
    return None
 
 
def player_move_or_attack(player, dx, dy): 
    x = player.x + dx
    y = player.y + dy
 
    # Is there an attackable object?
    target = None
    for object in player.current_map.objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break
 
    if target is not None:
        actions.attack(player.fighter, target)
    else:
        if actions.move(player, dx, dy):
            player.current_map.fov_needs_recompute = True
 

def inventory_menu(player, header):
    """
    Show a menu with each item of the inventory as an option.
    """
    if len(player.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for item in player.inventory:
            text = item.name
            #show additional information, in case it's equipped
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)
 
    index = renderer.menu(header, options, INVENTORY_WIDTH)
 
    #if an item was chosen, return it
    if index is None or len(player.inventory) == 0: return None
    return player.inventory[index].item
 
def handle_keys(player):
    """
    Returns 'playing', 'didnt-take-turn', or 'exit'.
    """
    key = ui.key
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  #exit game
 
    if player.game_state == 'playing':
        #movement keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack(player, 0, -1)
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack(player, 0, 1)
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack(player, -1, 0)
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack(player, 1, 0)
        elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            player_move_or_attack(player, -1, -1)
        elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
            player_move_or_attack(player, 1, -1)
        elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
            player_move_or_attack(player, -1, 1)
        elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
            player_move_or_attack(player, 1, 1)
        elif key.vk == libtcod.KEY_KP5:
            pass  #do nothing ie wait for the monster to come to you
        else:
            #test for other keys
            key_char = chr(key.c)
 
            if key_char == 'g':
                # pick up an item
                for object in player.current_map.objects:  #look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        pick_up(player, object)
                        break
 
            if key_char == 'i':
                # show the inventory; if an item is selected, use it
                chosen_item = inventory_menu(player, 'Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    use(player, chosen_item.owner)
 
            if key_char == 'd':
                # show the inventory; if an item is selected, drop it
                chosen_item = inventory_menu(player, 'Press the key next to an item to drop it, or any other to cancel.\n')
                if chosen_item is not None:
                    drop(player, chosen_item.owner)
 
            if key_char == 'c':
                # show character information
                level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                renderer.msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
                       '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
                       '\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense), CHARACTER_SCREEN_WIDTH)
 
            if key_char == '<':
                # go down stairs, if the player is on them
                if player.current_map.stairs.x == player.x and player.current_map.stairs.y == player.y:
                    next_level(player)
 
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
        while choice == None:
            choice = renderer.menu('Level up! Choose a stat to raise:\n',
                          ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
                           'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
                           'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'], LEVEL_SCREEN_WIDTH)
 
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
 
    #for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red
 
def save_game(player):
    """
    Save the game to file "savegame";
    overwrites any existing data.
    """
    file = shelve.open('savegame', 'n')
    file['current_map'] = player.current_map
    file['player_index'] = current_map.objects.index(player)  #index of player in objects list
    file['game_msgs'] = log.game_msgs
    file.close()
 
def load_game():
    """
    Loads from "savegame".
    Returns the player object.
    """
    file = shelve.open('savegame', 'r')
    current_map = file['current_map']  # player will hold our reference to this
    player = current_map.objects[file['player_index']]  #get index of player in objects list and access it
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
    player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
    player.inventory = [] 
    player.level = 1
    player.game_state = 'playing'
 
    equipment_component = Equipment(slot='right hand', power_bonus=2)
    obj = Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
    player.inventory.append(obj)
    equip(player, equipment_component)
    obj.always_visible = True

    current_map = cartographer.make_map(player, 1)
    renderer.clear_console()  #unexplored areas start black (which is the default background color)
 
    log.message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)

    return player
 
def next_level(player):
    """
    Advance to the next level (changing player.current_map).
    Heals the player 50%.
    """
    log.message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
    actions.heal(player.fighter, player.fighter.max_hp / 2)
 
    log.message('After a rare moment of peace, you descend deeper into the heart of the dungeon...', libtcod.red)
    cartographer.make_map(player, player.current_map.dungeon_level + 1)
    renderer.clear_console()

 
def play_game(player):
    """
    Main loop.
    """
    player_action = None
 
    ui.init()

    while not libtcod.console_is_window_closed():
        ui.poll()
        renderer.render_all(player, ui.mouse)
        player.current_map.fov_needs_recompute = False

        libtcod.console_flush()
 
        check_level_up(player)
 
        # Erase all objects at their old locations, before they move.
        for object in player.current_map.objects:
            renderer.clear_object(object)
 
        player_action = handle_keys(player)
        if player_action == 'exit':
            save_game(player)
            break
 
        if player.game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in player.current_map.objects:
                if object.ai:
                    object.ai.take_turn(player)
 
 
renderer.renderer_init()
renderer.main_menu(new_game, play_game, load_game)
