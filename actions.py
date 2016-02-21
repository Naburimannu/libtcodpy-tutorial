"""
Implementation of actions.

Includes those which might be used by the AI (movement and combat)
and those which are currently only offered to the player.
Magical effects and targeting (spells.py) could also live here.

Conditionals and interfaces for the player sit up top in roguelike.py.
"""
import libtcodpy as libtcod

import log
import algebra
from components import *


def move(o, direction):
    """
    Moves object by (dx, dy).
    Returns true if move succeeded.
    """
    goal = o.pos + direction
    if not o.current_map.is_blocked_at(goal):
        o.pos = goal
        return True
    return False


def move_towards(o, target_pos):
    """
    Moves object one step towards target location.
    Returns true if move succeeded.
    """
    dir = algebra.Direction(target_pos.x - o.x, target_pos.y - o.y)
    dir.normalize()
    return move(o, dir)


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


def pick_up(actor, o, report=True):
    """
    Add an Object to the actor's inventory and remove from the map.
    """
    for p in actor.inventory:
        if o.item.can_combine(p):
            p.item.count += o.item.count
            actor.current_map.objects.remove(o)
            if report:
                log.message(actor.name.capitalize() + ' picked up a ' + o.name + '!', libtcod.green)
            return True

    if len(actor.inventory) >= 26:
        if report:
            log.message(actor.name.capitalize() + ' inventory is full, cannot pick up ' +
                        o.name + '.', libtcod.red)
        return False
    else:
        actor.inventory.append(o)
        actor.current_map.objects.remove(o)
        if report:
            log.message(actor.name.capitalize() + ' picked up a ' + o.name + '!', libtcod.green)

        # Special case: automatically equip if the corresponding equipment slot is unused.
        equipment = o.equipment
        if equipment and _get_equipped_in_slot(actor, equipment.slot) is None:
            equip(actor, equipment)
        return True

def drop(actor, o, report=True):
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
    if report:
        log.message(actor.name.capitalize() + ' dropped a ' + o.name + '.', libtcod.yellow)


def use(actor, o, report=True):
    """
    If the object has the Equipment component, toggle equip/dequip.
    Otherwise invoke its use_function and (if not cancelled) destroy it.
    """
    if o.equipment:
        _toggle_equip(actor, o.equipment, report)
        return

    if o.item.use_function is None:
        if report:
            log.message('The ' + o.name + ' cannot be used.')
    else:
        if o.item.use_function(actor) != 'cancelled':
            if o.item.count > 1:
                o.item.count -= 1
            else:
                actor.inventory.remove(o)


def _toggle_equip(actor, eqp, report=True):
    if eqp.is_equipped:
        dequip(actor, eqp, report)
    else:
        equip(actor, eqp, report)


def equip(actor, eqp, report=True):
    """
    Equip the object (and log unless report=False).
    Ensure only one object per slot.
    """
    old_equipment = _get_equipped_in_slot(actor, eqp.slot)
    if old_equipment is not None:
        dequip(actor, old_equipment)

    eqp.is_equipped = True
    if report:
        log.message('Equipped ' + eqp.owner.name + ' on ' + eqp.slot + '.', libtcod.light_green)


def dequip(actor, eqp, report):
    """
    Dequip the object (and log).
    """
    if not eqp.is_equipped:
        return
    eqp.is_equipped = False
    if report:
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


class _MockMap(object):
    def is_blocked_at(self, pos):
        return False


def _test_move():
    o = Object(algebra.Location(0, 0), 'o', 'test object', libtcod.white)
    o.current_map = _MockMap()
    assert o.pos == algebra.Location(0, 0)
    move(o, algebra.south)
    assert o.pos == algebra.Location(0, 1)
    move(o, algebra.southeast)
    assert o.pos == algebra.Location(1, 2)


def _test_move_towards():
    o = Object(algebra.Location(0, 0), 'o', 'test object', libtcod.white)
    o.current_map = _MockMap()
    assert o.pos == algebra.Location(0, 0)
    move_towards(o, algebra.Location(10, 10))
    assert o.pos == algebra.Location(1, 1)
    move_towards(o, algebra.Location(10, 10))
    assert o.pos == algebra.Location(2, 2)
    move_towards(o, algebra.Location(-10, 2))
    assert o.pos == algebra.Location(1, 2)
    move_towards(o, o.pos)
    assert o.pos == algebra.Location(1, 2)


def _test_actions():
    _test_move()
    _test_move_towards()


if __name__ == '__main__':
    _test_actions()
    print('Action tests complete.')
