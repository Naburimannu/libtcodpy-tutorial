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
# Number of lines of messages normally displayed on screen
MSG_HEIGHT = config.PANEL_HEIGHT - 1
# Number of lines of messages retained for history display (^p)
MSG_LIMIT = 50


def init():
    global game_msgs

    # The list of game messages and their colors; starts empty.
    game_msgs = []


def message(new_msg, color=libtcod.white):
    """
    Add a colored string to the end of the log;
    does wordwrap at MSG_WIDTH characters.
    """
    global game_msgs
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        # If the buffer is full, remove the first line to make room for the new one.
        if len(game_msgs) == MSG_LIMIT:
            del game_msgs[0]

        game_msgs.append((line, color))
