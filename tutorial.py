#!/usr/bin/python
#
# libtcod python tutorial
#
 
import libtcodpy as libtcod
import shelve
 
import config
import log

from components import *
import map
import renderer

import actions

INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

  
#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
 
#spell values
HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25
 
#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150
 
 
 
 
 

 
 
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
 
def basic_monster(monster, metadata):
    #a basic monster takes its turn. if you can see it, it can see you
    if libtcod.map_is_in_fov(monster.current_map.fov_map, monster.x, monster.y): 
        #move towards player if far away
        if monster.distance_to(player) >= 2:
            actions.move_towards(monster, player.x, player.y)
        #close enough, attack! (if the player is still alive.)
        elif player.fighter.hp > 0:
            actions.attack(monster.fighter, player)
 
class confused_monster_metadata:
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

def confused_monster(monster, metadata):
    if metadata.num_turns > 0:
        #move in a random direction, and decrease the number of turns confused
        actions.move(monster, libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
        metadata.num_turns -= 1
 
    else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
        monster.ai = metadata.old_ai
        log.message(monster.name.capitalize() + ' is no longer confused!', libtcod.red)


def pick_up(actor, o):
    """
    Add an Object to the player's inventory and remove from the map.
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
    Remove an Object from the player's inventory and add it to the map
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
    Otherwise invoke its use_function and destroy it.
    """
    if o.equipment:
        toggle_equip(actor, o.equipment)
        return
 
    if o.item.use_function is None:
        log.message('The ' + o.name + ' cannot be used.')
    else:
        if o.item.use_function() != 'cancelled':
            actor.inventory.remove(o)
 

# takes Equipment
def toggle_equip(actor, eqp):
    if eqp.is_equipped:
        dequip(actor, eqp)
    else:
        equip(actor, eqp)
 
# takes Equipment
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
 
# takes Equipment
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
 
def create_room(new_map, room):
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            new_map.blocked[x][y] = False
            new_map.block_sight[x][y] = False
 
def create_h_tunnel(new_map, x1, x2, y):
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        new_map.blocked[x][y] = False
        new_map.block_sight[x][y] = False
 
def create_v_tunnel(new_map, y1, y2, x):
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        new_map.blocked[x][y] = False
        new_map.block_sight[x][y] = False
 
def make_map(player, dungeon_level):
    renderer.clear_console()  #unexplored areas start black (which is the default background color)
 
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
            create_room(new_map, new_room)
 
            #add some contents to this room, such as monsters
            place_objects(new_map, new_room)
 
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
                    create_h_tunnel(new_map, prev_x, new_x, prev_y)
                    create_v_tunnel(new_map, prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(new_map, prev_y, new_y, prev_x)
                    create_h_tunnel(new_map, prev_x, new_x, new_y)
 
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1
 
    #create stairs at the center of the last room
    new_map.stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, always_visible=True)
    new_map.objects.insert(0, new_map.stairs)

    new_map.initialize_fov()
    return new_map
 
def random_choice_index(chances):  #choose one option from list of chances, returning its index
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
 
def random_choice(chances_dict):
    #choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()
 
    return strings[random_choice_index(chances)]
 
def from_dungeon_level(new_map, table):
    #returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if new_map.dungeon_level >= level:
            return value
    return 0
 
def place_objects(new_map, room):
    #this is where we decide the chance of each monster or item appearing.
 
    #maximum number of monsters per room
    max_monsters = from_dungeon_level(new_map, [[2, 1], [3, 4], [5, 6]])
 
    #chance of each monster
    monster_chances = {}
    monster_chances['orc'] = 80  #orc always shows up, even if all other monsters have 0 chance
    monster_chances['troll'] = from_dungeon_level(new_map, [[15, 3], [30, 5], [60, 7]])
 
    #maximum number of items per room
    max_items = from_dungeon_level(new_map, [[1, 1], [2, 4]])
 
    #chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    item_chances['heal'] = 35  #healing potion always shows up, even if all other items have 0 chance
    item_chances['lightning'] = from_dungeon_level(new_map, [[25, 4]])
    item_chances['fireball'] =  from_dungeon_level(new_map, [[25, 6]])
    item_chances['confuse'] =   from_dungeon_level(new_map, [[10, 2]])
    item_chances['sword'] =     from_dungeon_level(new_map, [[5, 4]])
    item_chances['shield'] =    from_dungeon_level(new_map, [[15, 8]])
 
 
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, max_monsters)
 
    for i in range(num_monsters):
        #choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not new_map.is_blocked(x, y):
            choice = random_choice(monster_chances)
            if choice == 'orc':
                #create an orc
                fighter_component = Fighter(hp=20, defense=0, power=4, xp=35, death_function=monster_death)
                ai_component = AI(basic_monster)
 
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                                 blocks=True, fighter=fighter_component, ai=ai_component)
 
            elif choice == 'troll':
                #create a troll
                fighter_component = Fighter(hp=30, defense=2, power=8, xp=100, death_function=monster_death)
                ai_component = AI(basic_monster)
 
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
            choice = random_choice(item_chances)
            if choice == 'heal':
                #create a healing potion
                item_component = Item(use_function=cast_heal)
                item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
 
            elif choice == 'lightning':
                #create a lightning bolt scroll
                item_component = Item(use_function=cast_lightning)
                item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
 
            elif choice == 'fireball':
                #create a fireball scroll
                item_component = Item(use_function=cast_fireball)
                item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, item=item_component)
 
            elif choice == 'confuse':
                #create a confuse scroll
                item_component = Item(use_function=cast_confuse)
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
 
 
 
 
def player_move_or_attack(player, dx, dy): 
    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy
 
    #try to find an attackable object there
    target = None
    for object in player.current_map.objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break
 
    #attack if target found, move otherwise
    if target is not None:
        actions.attack(player.fighter, target)
    else:
        if actions.move(player, dx, dy):
            player.current_map.fov_needs_recompute = True
 

def inventory_menu(header):
    #show a menu with each item of the inventory as an option
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
 
def handle_keys():
    global key, player
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  #exit game
 
    if game_state == 'playing':
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
                chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    use(player, chosen_item.owner)
 
            if key_char == 'd':
                # show the inventory; if an item is selected, drop it
                chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
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
                    next_level()
 
            return 'didnt-take-turn'
 
def check_level_up():
    #see if the player's experience is enough to level-up
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        #it is! level up and ask to raise some stats
        player.level += 1
        player.fighter.xp -= level_up_xp
        log.message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)
 
        choice = None
        while choice == None:  #keep asking until a choice is made
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
    #the game ended!
    global game_state
    log.message('You died!', libtcod.red)
    game_state = 'dead'
 
    #for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red
 
def monster_death(monster):
    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    log.message('The ' + monster.name + ' is dead! You gain ' + str(monster.fighter.xp) + ' experience points.', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.current_map.objects.remove(monster)
    monster.current_map.objects.insert(0, monster)
 
def target_tile(max_range=None):
    """
    Return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
    """
    global key, mouse, player
    while True:
        # Render the screen. This erases the inventory and shows the names of objects under the mouse.
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        renderer.render_all(player, mouse)
        player.current_map.fov_needs_recompute = False
 
        (x, y) = (mouse.cx, mouse.cy)
 
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)
 
        #accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(player.current_map.fov_map, x, y) and
                (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
 
def target_monster(max_range=None):
    #returns a clicked monster inside FOV up to a range, or None if right-clicked
    global player
    while True:
        (x, y) = target_tile(max_range)
        if x is None:  #player cancelled
            return None
 
        #return the first clicked monster, otherwise continue looping
        for obj in player.current_map.objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj
 
def closest_monster(max_range):
    #find closest enemy, up to a maximum range, and in the player's FOV
    global player
    closest_enemy = None
    closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
    for object in player.current_map.objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(player.current_map.fov_map, object.x, object.y):
            #calculate distance between this object and the player
            dist = player.distance_to(object)
            if dist < closest_dist:  #it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy
 
def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        log.message('You are already at full health.', libtcod.red)
        return 'cancelled'
 
    log.message('Your wounds start to feel better!', libtcod.light_violet)
    actions.heal(player.fighter, HEAL_AMOUNT)
 
def cast_lightning():
    #find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:  #no enemy found within maximum range
        log.message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'
 
    #zap it!
    log.message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
            + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    actions.inflict_damage(player, monster.fighter, LIGHTNING_DAMAGE)
 
def cast_fireball():
    global player
    log.message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    log.message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)
 
    for obj in player.current_map.objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            log.message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
            actions.inflict_damage(player, obj.fighter, FIREBALL_DAMAGE)
 
def cast_confuse():
    log.message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'cancelled'
 
    old_ai = monster.ai
    monster.ai = AI(confused_monster, confused_monster_metadata(old_ai))
    monster.ai.set_owner(monster)
    log.message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)
 
 
def save_game():
    global current_map, player, game_state
    """
    Overwrites any existing data.
    """
    file = shelve.open('savegame', 'n')
    file['current_map'] = current_map
    file['player_index'] = current_map.objects.index(player)  #index of player in objects list
    file['game_msgs'] = log.game_msgs
    file['game_state'] = game_state
    file.close()
 
def load_game():
    global current_map, player, game_state
 
    file = shelve.open('savegame', 'r')
    current_map = file['current_map']
    player = current_map.objects[file['player_index']]  #get index of player in objects list and access it
    log.game_msgs = file['game_msgs']
    game_state = file['game_state']
    file.close()
 
    current_map.initialize_fov()
 
def new_game():
    global player, current_map, game_state
 
    #create object representing the player
    fighter_component = Fighter(hp=100, defense=1, power=2, xp=0, death_function=player_death)
    player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
    player.inventory = [] 
    player.level = 1
 
    current_map = make_map(player, 1)
 
    game_state = 'playing'
 
    log.init()
 
    #a warm welcoming message!
    log.message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
 
    #initial equipment: a dagger
    equipment_component = Equipment(slot='right hand', power_bonus=2)
    obj = Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
    player.inventory.append(obj)
    equip(player, equipment_component)
    obj.always_visible = True
 
def next_level():
    """
    Advance to the next level.
    """
    global current_map
    log.message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
    actions.heal(player.fighter, player.fighter.max_hp / 2)  #heal the player by 50%
 
    log.message('After a rare moment of peace, you descend deeper into the heart of the dungeon...', libtcod.red)
    current_map = make_map(player, current_map.dungeon_level + 1)
 
 
def play_game():
    global key, mouse, player
 
    player_action = None
 
    mouse = libtcod.Mouse()
    key = libtcod.Key()

    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        renderer.render_all(player, mouse)
        player.current_map.fov_needs_recompute = False

        libtcod.console_flush()
 
        check_level_up()
 
        #erase all objects at their old locations, before they move
        for object in player.current_map.objects:
            renderer.clear_object(object)
 
        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break
 
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in player.current_map.objects:
                if object.ai:
                    object.ai.take_turn()
 
 
renderer.renderer_init()
renderer.main_menu(new_game, play_game, load_game)
