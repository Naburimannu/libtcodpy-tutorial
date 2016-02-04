import libtcodpy as libtcod

import config
import log

color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 10

#sizes and coordinates relevant for the GUI
PANEL_Y = config.SCREEN_HEIGHT - config.PANEL_HEIGHT
MSG_X = config.BAR_WIDTH + 2

LIMIT_FPS = 20  #20 frames-per-second maximum

def renderer_init():
    """
    Initialize libtcod and set up our basic consoles to draw into.
    """
    global con, panel
    libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 'python/libtcod tutorial', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    con = libtcod.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)
    panel = libtcod.console_new(config.SCREEN_WIDTH, config.PANEL_HEIGHT)

 
def msgbox(text, width=50):
    menu(text, [], width)  #use menu() as a sort of "message box"

def main_menu(new_game, play_game, load_game):
    img = libtcod.image_load('menu_background.png')
 
    while not libtcod.console_is_window_closed():
        #show the background image, at twice the regular console resolution
        libtcod.image_blit_2x(img, 0, 0, 0)
 
        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(0, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
                                 'TOMBS OF THE ANCIENT KINGS')
        libtcod.console_print_ex(0, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER, 'By Jotaf')
 
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)
 
        if choice == 0:
            play_game(new_game())
        if choice == 1:
            try:
                player = load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game(player)
        elif choice == 2:
            break

def clear_console():
    libtcod.console_clear(con)

def _render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)
 
    #render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
 
    #now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
 
    #finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
                                 name + ': ' + str(value) + '/' + str(maximum))
 


def _get_names_under_mouse(objects, fov_map, mouse):
    #return a string with the names of all objects under the mouse
 
    (x, y) = (mouse.cx, mouse.cy)
 
    #create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
 
    names = ', '.join(names)  #join the names, separated by commas
    return names.capitalize()
 
def _draw_object(o, map, fov_map):
    #only show if it's visible to the player; or it's set to "always visible" and on an explored tile
    if (libtcod.map_is_in_fov(fov_map, o.x, o.y) or
            (o.always_visible and map.explored[o.x][o.y])):
        #set the color and then draw the character that represents this object at its position
        libtcod.console_set_default_foreground(con, o.color)
        libtcod.console_put_char(con, o.x, o.y, o.char, libtcod.BKGND_NONE)

 
def clear_object(o):
    #erase the character that represents this object
    libtcod.console_put_char(con, o.x, o.y, ' ', libtcod.BKGND_NONE)

 
def menu(header, options, width):
    """
    Display a menu of options headed by letters; return the index [0, 25] of the selection, or None.
    """
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
 
    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, config.SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height
 
    #create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)
 
    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
 
    #print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
 
    #blit the contents of "window" to the root console
    x = config.SCREEN_WIDTH/2 - width/2
    y = config.SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
 
    #present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)
 
    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None
 
def render_all(player, mouse):
    global color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
 
    current_map = player.current_map
    if current_map.fov_needs_recompute:
        #recompute FOV if needed (the player moved or something)
        libtcod.map_compute_fov(current_map.fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
 
        #go through all tiles, and set their background color according to the FOV
        for y in range(current_map.height):
            for x in range(current_map.width):
                visible = libtcod.map_is_in_fov(current_map.fov_map, x, y)
                wall = current_map.block_sight[x][y]
                if not visible:
                    #if it's not visible right now, the player can only see it if it's explored
                    if current_map.explored[x][y]:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                else:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
                        #since it's visible, explore it
                    current_map.explored[x][y] = True
 
    #draw all objects in the list, except the player. we want it to
    #always appear over all other objects! so it's drawn later.
    for object in current_map.objects:
        if object != player:
            _draw_object(object, current_map, current_map.fov_map)
    _draw_object(player, current_map, current_map.fov_map)
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, config.MAP_WIDTH, config.MAP_HEIGHT, 0, 0, 0)
 
 
    #prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
 
    #print the game messages, one line at a time
    y = 1
    for (line, color) in log.game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
        y += 1
 
    #show the player's stats
    _render_bar(1, 1, config.BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darker_red)
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(current_map.dungeon_level))
 
    #display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, _get_names_under_mouse(current_map.objects, current_map.fov_map, mouse))
 
    #blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, config.SCREEN_WIDTH, config.PANEL_HEIGHT, 0, 0, PANEL_Y)
 
