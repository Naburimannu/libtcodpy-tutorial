import libtcodpy as libtcod

import config
import log

color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)

FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

PANEL_Y = config.SCREEN_HEIGHT - config.PANEL_HEIGHT
MSG_X = config.BAR_WIDTH + 2

LIMIT_FPS = 20


def renderer_init():
    """
    Initialize libtcod and set up our basic consoles to draw into.
    """
    global _con, _panel
    libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 'python/libtcod tutorial', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    _con = libtcod.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)
    _panel = libtcod.console_new(config.SCREEN_WIDTH, config.PANEL_HEIGHT)


def msgbox(text, width=50):
    """
    Display a message, wait for any keypress.
    """
    menu(text, [], width)


def log_display(width = 50):
    """
    Display the recent log history, wait for any keypress.
    menu() 
    """
    colored_text_list(log.game_msgs[:25], width)


def colored_text_list(lines, width):
    """
    Display a series of colored lines of text.
    """
    # Create an off-screen console that represents the menu's window.
    height = len(lines)
    window = libtcod.console_new(width, height)

    y = 0
    for (line, color) in lines:
        libtcod.console_set_default_foreground(window, color)
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE,
                                 libtcod.LEFT, line)
        y += 1

    x = config.SCREEN_WIDTH/2 - width/2
    y = config.SCREEN_HEIGHT/2 - height/2
    print(width, height, x, y)
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    libtcod.console_flush()
    while True:
        key = libtcod.console_wait_for_keypress(True)
        if not (key.vk == libtcod.KEY_ALT or key.vk == libtcod.KEY_CONTROL or
                key.vk == libtcod.KEY_SHIFT):
            break;


def main_menu(new_game, play_game, load_game):
    """
    Prompt the player to start a new game, continue playing the last game,
    or exit.
    """
    img = libtcod.image_load('menu_background.png')

    while not libtcod.console_is_window_closed():
        # Show the background image, at twice the regular console resolution.
        libtcod.image_blit_2x(img, 0, 0, 0)

        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(
            0, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE,
            libtcod.CENTER, 'TOMBS OF THE ANCIENT KINGS')
        libtcod.console_print_ex(
            0, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-2, libtcod.BKGND_NONE,
            libtcod.CENTER, 'By Jotaf')

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
    global _con
    libtcod.console_clear(_con)


def _render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(_panel, back_color)
    libtcod.console_rect(_panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(_panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(_panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(_panel, libtcod.white)
    libtcod.console_print_ex(
        _panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))


def _get_names_under_mouse(objects, fov_map, mouse):
    (x, y) = (mouse.cx, mouse.cy)

    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

    names = ', '.join(names)
    return names.capitalize()


def _draw_object(o, map, fov_map):
    # Show if it's visible to the player
    # or it's set to "always visible" and on an explored tile.
    global _con
    if (libtcod.map_is_in_fov(fov_map, o.x, o.y) or
            (o.always_visible and map.explored[o.x][o.y])):
        libtcod.console_set_default_foreground(_con, o.color)
        libtcod.console_put_char(_con, o.x, o.y, o.char, libtcod.BKGND_NONE)


def clear_object(o):
    """
    Erase the character that represents this object.
    """
    global _con
    libtcod.console_put_char(_con, o.x, o.y, ' ', libtcod.BKGND_NONE)


def menu(header, options, width):
    """
    Display a menu of options headed by letters; return the index [0, 25] of the selection, or None.
    """
    global _con
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    # Calculate total height for the header (after auto-wrap) and one line per option.
    header_height = libtcod.console_get_height_rect(_con, 0, 0, width, config.SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    # Create an off-screen console that represents the menu's window.
    window = libtcod.console_new(width, height)

    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    x = config.SCREEN_WIDTH/2 - width/2
    y = config.SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    libtcod.console_flush()
    while True:
        key = libtcod.console_wait_for_keypress(True)
        if not (key.vk == libtcod.KEY_ALT or key.vk == libtcod.KEY_CONTROL or
                key.vk == libtcod.KEY_SHIFT):
            break;

    index = key.c - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def _set(con, x, y, color, mode):
    libtcod.console_set_char_background(con, x, y, color, mode)


def _draw_fov(current_map):
    for y in range(current_map.height):
        for x in range(current_map.width):
            visible = libtcod.map_is_in_fov(current_map.fov_map, x, y)
            wall = current_map.block_sight[x][y]
            if not visible:
                # If it's not visible, only draw if it's explored
                if current_map.explored[x][y]:
                    if wall:
                        _set(_con, x, y, color_dark_wall, libtcod.BKGND_SET)
                    else:
                        _set(_con, x, y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    _set(_con, x, y, color_light_wall, libtcod.BKGND_SET)
                else:
                    _set(_con, x, y, color_light_ground, libtcod.BKGND_SET)
                current_map.explored[x][y] = True


def render_all(player, mouse):
    global _con, _panel
    global color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground

    current_map = player.current_map
    if current_map.fov_needs_recompute:
        # Recompute FOV if needed (the player moved or something in
        # the dungeon changed).
        libtcod.map_compute_fov(
            current_map.fov_map, player.x,
            player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        _draw_fov(current_map)

    # Draw all objects in the list, except the player. We want it to
    # always appear over all other objects, so it's drawn later.
    # (Could also achieve this by guaranteeing the player is always
    # the last object in current_map.objects.)
    for object in current_map.objects:
        if object != player:
            _draw_object(object, current_map, current_map.fov_map)
    _draw_object(player, current_map, current_map.fov_map)

    libtcod.console_blit(_con, 0, 0, config.MAP_WIDTH,
                         config.MAP_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_background(_panel, libtcod.black)
    libtcod.console_clear(_panel)

    y = 1
    for (line, color) in log.game_msgs:
        libtcod.console_set_default_foreground(_panel, color)
        libtcod.console_print_ex(_panel, MSG_X, y, libtcod.BKGND_NONE,
                                 libtcod.LEFT, line)
        y += 1

    # Show the player's stats.
    _render_bar(1, 1, config.BAR_WIDTH, 'HP', player.fighter.hp,
                player.fighter.max_hp,
                libtcod.light_red, libtcod.darker_red)
    libtcod.console_print_ex(
        _panel, 1, 3, libtcod.BKGND_NONE,
        libtcod.LEFT, 'Dungeon level ' + str(current_map.dungeon_level))

    # Display names of objects under the mouse.
    libtcod.console_set_default_foreground(_panel, libtcod.light_gray)
    libtcod.console_print_ex(
        _panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
        _get_names_under_mouse(current_map.objects, current_map.fov_map, mouse))

    # Blit the contents of "_panel" to the root console.
    libtcod.console_blit(_panel, 0, 0, config.SCREEN_WIDTH, config.PANEL_HEIGHT,
                         0, 0, PANEL_Y)
