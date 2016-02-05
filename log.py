"""
Global message log.

Call log.init() before using.
Retrieve (message, color) tuples from log.game_msgs[].
Append them using log.message().
"""

import libtcodpy as libtcod
import textwrap

import config

MSG_WIDTH = config.SCREEN_WIDTH - config.BAR_WIDTH - 2
MSG_HEIGHT = config.PANEL_HEIGHT - 1

def init():
    global game_msgs

    # the list of game messages and their colors, starts empty
    game_msgs = []

def message(new_msg, color = libtcod.white):
    """
    Add a colored string to the log; does wordwrap at MSG_WIDTH characters.
    """
    global game_msgs
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
        game_msgs.append( (line, color) )
 