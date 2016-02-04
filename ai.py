import libtcodpy as libtcod

from components import *
import actions

# Might make sense to have this defined
# in spells.py instead, dropping the
# default argument?
CONFUSE_NUM_TURNS = 10

 
def basic_monster(monster, player, metadata):
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

def confused_monster(monster, player, metadata):
    if metadata.num_turns > 0:
        #move in a random direction, and decrease the number of turns confused
        actions.move(monster, libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
        metadata.num_turns -= 1
 
    else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
        monster.ai = metadata.old_ai
        log.message(monster.name.capitalize() + ' is no longer confused!', libtcod.red)

