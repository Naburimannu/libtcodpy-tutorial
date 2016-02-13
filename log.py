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
MSG_LIMIT = 150


class ExplicitMessage(object):
    def __init__(self, message, color, count):
        self.message = message
        self.color = color
        self.count = count

    def can_merge(self, other):
        return (self.message == other.message and
                self.color == other.color and
                self.count + other.count < 10)


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
        new_message = ExplicitMessage(line, color, 1)
        if game_msgs and game_msgs[-1].can_merge(new_message):
            game_msgs[-1].count += 1
            return
        game_msgs.append(new_message)
