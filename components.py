import math

 
class Object:
    """
    This is a generic object: the player, a monster, an item, the stairs...
    It's always represented by a character on screen.
    """
    def __init__(self, x, y, char, name, color, blocks=False, always_visible=False, fighter=None, ai=None, item=None, equipment=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible
        self.fighter = fighter
        self._ensure_ownership(fighter)
 
        self.ai = ai
        self._ensure_ownership(ai)
 
        self.item = item
        self._ensure_ownership(item)
 
        self.equipment = equipment
        self._ensure_ownership(equipment)
 
    def _ensure_ownership(self, component):
        if (component):
            component.set_owner(self)
 
    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
 
    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

class Item:
    """
    An item that can be picked up and used.
    """
    def __init__(self, use_function=None):
        self.use_function = use_function
 
    def set_owner(self, entity):
        self.owner = entity
 
class Equipment:
    """
    An object that can be equipped, yielding bonuses.
    Requires an Item component.
    """
    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
 
        self.slot = slot
        self.is_equipped = False
 
    def set_owner(self, entity):
        self.owner = entity

        # There must be an Item component for the Equipment component to work properly.
        entity.item = Item()
        entity.item.set_owner(entity)
 