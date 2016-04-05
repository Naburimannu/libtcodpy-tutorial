# Copyright 2016 Thomas C. Hudson
# Governed by the license described in LICENSE.txt
import libtcodpy as libtcod

import log
import algebra
from components import *
import actions
import map
import spells

def dagger():
    return Object(algebra.Location(0, 0), '-', 'dagger', libtcod.sky,
                  item=Item(description='A leaf-shaped bronze knife; provides +2 Attack'),
                  equipment=Equipment(slot='right hand', power_bonus=2))

def healing_potion(pos=algebra.Location(0, 0)):
    return Object(pos, '!', 'healing potion', libtcod.violet,
                  item=Item(use_function=spells.cast_heal,
                    description='A flask of revivifying alchemical mixtures; heals ' + str(spells.HEAL_AMOUNT) + ' hp.'))

def lightning_scroll(pos=algebra.Location(0, 0)):
    return Object(pos, '#', 'scroll of lightning bolt', libtcod.light_yellow,
            item=Item(use_function=spells.cast_lightning,
                      description='Reading these runes will strike your nearest foe with lightning for ' +
                      str(spells.LIGHTNING_DAMAGE) + ' hp.'))

def fireball_scroll(pos=algebra.Location(0, 0)):
    return Object(pos, '#', 'scroll of fireball', libtcod.light_yellow,
        item=Item(use_function=spells.cast_fireball,
                  description='Reading these runes will cause a burst of flame inflicting ' + str(spells.FIREBALL_DAMAGE) +
                              ' hp on nearby creatures.'))

def confusion_scroll(pos=algebra.Location(0, 0)):
    return Object(pos, '#', 'scroll of confusion', libtcod.light_yellow,
                  item=Item(use_function=spells.cast_confuse,
                            description='Reading these runes will confuse the creature you focus on for a short time.'))

def sword(pos=algebra.Location(0, 0)):
    return Object(pos, '/', 'sword', libtcod.sky,
                  item=Item(description='A heavy-tipped bronze chopping sword; provides +3 Attack'),
                  equipment=Equipment(slot='right hand', power_bonus=3))

def shield(pos=algebra.Location(0, 0)):
    return Object(pos, '[', 'shield', libtcod.darker_orange,
                  item=Item(description='A bronze-edged oval shield; provides +1 Defense'),
                  equipment=Equipment(slot='left hand', defense_bonus=1))
