import libtcodpy as libtcod

def init():
    global key, mouse
    mouse = libtcod.Mouse()
    key = libtcod.Key()

def poll():
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)


