"""
Spells (magic item effects) and targeting utility functions.

Could be folded into actions.py.
"""
import libtcodpy as libtcod

import log
import components
import actions
import ui
import renderer

HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25


def _target_tile(actor, max_range=None):
    """
    Return the position of a tile left-clicked in player's FOV
    (optionally in a range), or (None,None) if right-clicked.
    """
    while True:
        # Render the screen. This erases the inventory and shows
        # the names of objects under the mouse.
        libtcod.console_flush()
        ui.poll()
        renderer.render_all(actor, ui.mouse)
        actor.current_map.fov_needs_recompute = False

        (x, y) = (ui.mouse.cx, ui.mouse.cy)

        if ui.mouse.rbutton_pressed or ui.key.vk == libtcod.KEY_ESCAPE:
            return (None, None)

        # Accept the target if the player clicked in FOV
        # and within the range specified.
        if (ui.mouse.lbutton_pressed and
                libtcod.map_is_in_fov(actor.current_map.fov_map, x, y) and
                (max_range is None or actor.distance(x, y) <= max_range)):
            return (x, y)


def _target_monster(actor, max_range=None):
    """
    Returns a clicked monster inside FOV up to a range,
    or None if right-clicked.
    """
    while True:
        (x, y) = _target_tile(actor, max_range)
        if x is None:
            return None

        for obj in actor.current_map.objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != actor:
                return obj


def _closest_monster(actor, max_range):
    """
    Find closest enemy in the player's FOV, up to a maximum range.
    """
    closest_enemy = None
    closest_dist = max_range + 1

    for object in actor.current_map.objects:
        if (object.fighter and not object == actor and
                libtcod.map_is_in_fov(actor.current_map.fov_map,
                                      object.x, object.y)):
            dist = actor.distance_to(object)
            if dist < closest_dist:
                closest_enemy = object
                closest_dist = dist
    return closest_enemy


def cast_heal(actor):
    """
    Heal the caster.
    """
    if actor.fighter.hp == actor.fighter.max_hp:
        log.message('You are already at full health.', libtcod.red)
        return 'cancelled'

    log.message('Your wounds start to feel better!', libtcod.light_violet)
    actions.heal(actor.fighter, HEAL_AMOUNT)


def cast_lightning(actor):
    """
    Find closest enemy (inside a maximum range) and damage it.
    """
    monster = _closest_monster(actor, LIGHTNING_RANGE)
    if monster is None:
        log.message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'

    log.message('A lighting bolt strikes the ' + monster.name +
                ' with a loud thunder! The damage is ' +
                str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    actions.inflict_damage(actor, monster.fighter, LIGHTNING_DAMAGE)


def cast_fireball(actor):
    log.message('Left-click a target tile for the fireball, '
                'or right-click to cancel.', libtcod.light_cyan)
    (x, y) = _target_tile(actor)
    if x is None:
        return 'cancelled'
    log.message('The fireball explodes, burning everything within ' +
                str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)

    for obj in actor.current_map.objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            log.message('The ' + obj.name + ' gets burned for ' +
                        str(FIREBALL_DAMAGE) + ' hit points.',
                        libtcod.orange)
            actions.inflict_damage(actor, obj.fighter, FIREBALL_DAMAGE)


def cast_confuse(actor):
    log.message('Left-click an enemy to confuse it, or right-click to cancel.',
                libtcod.light_cyan)
    monster = _target_monster(actor, CONFUSE_RANGE)
    if monster is None:
        return 'cancelled'

    old_ai = monster.ai
    monster.ai = AI(ai.confused_monster, ai.confused_monster_metadata(old_ai))
    monster.ai.set_owner(monster)
    log.message('The eyes of the ' + monster.name +
                ' look vacant, as he starts to stumble around!',
                libtcod.light_green)
