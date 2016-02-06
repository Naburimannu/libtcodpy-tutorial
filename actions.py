"""
Actions which might be used by the AI: movement and combat.

Player-only actions could live here but can also sit up top in roguelike.py.
Magical effects and targeting (spells.py) could also live here.
"""
import math

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
