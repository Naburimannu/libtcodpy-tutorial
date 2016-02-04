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
    global game_msgs
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
        game_msgs.append( (line, color) )
 