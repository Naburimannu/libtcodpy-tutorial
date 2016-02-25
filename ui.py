"""
Global mouse and keyboard.

Call ui.init() before using.
Update with ui.poll().
After polling, access data from ui.key and ui.mouse.
"""
import libtcodpy as libtcod


def init():
    global key, mouse
    mouse = libtcod.Mouse()
    key = libtcod.Key()
