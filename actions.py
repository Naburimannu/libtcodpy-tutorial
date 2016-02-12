"""
Implementation of actions.

Includes those which might be used by the AI (movement and combat)
and those which are currently only offered to the player.
Magical effects and targeting (spells.py) could also live here.

Conditionals and interfaces for the player sit up top in roguelike.py.
"""
import math

import libtcodpy as libtcod

import log


def move(o, dx, dy):
    """
    Moves object by (dx, dy).
    Returns true if move succeeded.
    """
    if not o.current_map.is_blocked(o.x + dx, o.y + dy):
        o.x += dx
        o.y += dy
        return True
    return False


def move_towards(o, target_x, target_y):
    """
    Moves object one step towards target location.
    Returns true if move succeeded.
    """
    dx = target_x - o.x
    dy = target_y - o.y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    # Normalize to length 1 (preserving direction), then round and
    # convert to integer so the movement is restricted to the map grid.
    dx = int(round(dx / distance))
    dy = int(round(dy / distance))
    return move(o, dx, dy)


def attack(fighter, target):
    """
    A simple formula for attack damage.
    """
    damage = fighter.power - target.fighter.defense

    if damage > 0:
        log.message(
            fighter.owner.name.capitalize() + ' attacks ' + target.name +
            ' for ' + str(damage) + ' hit points.')
        inflict_damage(fighter.owner, target.fighter, damage)
    else:
        log.message(
            fighter.owner.name.capitalize() + ' attacks ' + target.name +
            ' but it has no effect!')


def inflict_damage(actor, fighter, damage):
    """
    Apply damage.
    """
    if damage > 0:
        fighter.hp -= damage

        if fighter.hp <= 0:
            function = fighter.death_function
            if function is not None:
                function(fighter.owner)

            actor.fighter.xp += fighter.xp


def heal(fighter, amount):
    """
    Heal by the given amount, without going over the maximum.
    """
    fighter.hp += amount
    if fighter.hp > fighter.max_hp:
        fighter.hp = fighter.max_hp


def pick_up(actor, o):
    """
    Add an Object to the actor's inventory and remove from the map.
    """
    if len(actor.inventory) >= 26:
        log.message(actor.name.capitalize() + ' inventory is full, cannot pick up ' +
                    o.name + '.', libtcod.red)
    else:
        actor.inventory.append(o)
        actor.current_map.objects.remove(o)
        log.message(actor.name.capitalize() + ' picked up a ' + o.name + '!', libtcod.green)

        # Special case: automatically equip if the corresponding equipment slot is unused.
        equipment = o.equipment
        if equipment and _get_equipped_in_slot(actor, equipment.slot) is None:
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
        _toggle_equip(actor, o.equipment)
        return

    if o.item.use_function is None:
        log.message('The ' + o.name + ' cannot be used.')
    else:
        if o.item.use_function(actor) != 'cancelled':
            actor.inventory.remove(o)


def _toggle_equip(actor, eqp):
    if eqp.is_equipped:
        dequip(actor, eqp)
    else:
        equip(actor, eqp)


def equip(actor, eqp, report=True):
    """
    Equip the object (and log unless report=False).
    Ensure only one object per slot.
    """
    old_equipment = _get_equipped_in_slot(actor, eqp.slot)
    if old_equipment is not None:
        dequip(actor, old_equipment)

    eqp.is_equipped = True
    if report is True:
        log.message('Equipped ' + eqp.owner.name + ' on ' + eqp.slot + '.', libtcod.light_green)


def dequip(actor, eqp):
    """
    Dequip the object (and log).
    """
    if not eqp.is_equipped:
        return
    eqp.is_equipped = False
    log.message('Dequipped ' + eqp.owner.name + ' from ' + eqp.slot + '.', libtcod.light_yellow)


def _get_equipped_in_slot(actor, slot):
    """
    Returns Equipment in a slot, or None.
    """
    if hasattr(actor, 'inventory'):
        for obj in actor.inventory:
            if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
                return obj.equipment
    return None
