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
    does wordwrap at MSG_WIDTH-5 characters
    since a count e.g. " (x3)" can add up to 5.
    """
    global game_msgs
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH-5)

    for line in new_msg_lines:
        # If the buffer is full, remove the first line to make room for the new one.
        if len(game_msgs) == MSG_LIMIT:
            del game_msgs[0]
        if not(game_msgs == []):
            (last_line, last_color, last_count) = game_msgs[-1]
            if (line == last_line and color == last_color and
                last_count < 9):
                game_msgs[-1] = (line, color, last_count + 1)
                return
        game_msgs.append((line, color, 1))
