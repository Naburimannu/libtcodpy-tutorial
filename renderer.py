import libtcodpy as libtcod

import config
import log
import algebra
import ui

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


class ScreenCoords(tuple):
    @staticmethod
    def fromWorldCoords(camera_coords, world_coords):
        x = world_coords[0] - camera_coords[0]
        y = world_coords[1] - camera_coords[1]
        if (x < 0 or y < 0 or x >= config.MAP_PANEL_WIDTH or y >= config.MAP_PANEL_HEIGHT):
            return ScreenCoords((None, None))
        return ScreenCoords((x, y))

    @staticmethod
    def toWorldCoords(camera_coords, screen_coords):
        x = screen_coords[0] + camera_coords[0]
        y = screen_coords[1] + camera_coords[1]
        return algebra.Location(x, y)


def renderer_init():
    """
    Initialize libtcod and set up our basic consoles to draw into.
    """
    global _con, _panel
    libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 'python/libtcod tutorial', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    _con = libtcod.console_new(config.MAP_PANEL_WIDTH, config.MAP_PANEL_HEIGHT)
    _panel = libtcod.console_new(config.SCREEN_WIDTH, config.PANEL_HEIGHT)


def msgbox(text, width=50):
    """
    Display a message, wait for any keypress.
    """
    menu(text, [], width)


def log_display(width=60):
    """
    Display the recent log history, wait for any keypress.
    """
    colored_text_list(log.game_msgs, width)


def _write_log(messages, window, x, initial_y):
    y = initial_y
    for (line, color, count) in messages:
        libtcod.console_set_default_foreground(window, color)
        if count > 1:
            line += ' (x' + str(count) + ')'
        libtcod.console_print_ex(window, x, y, libtcod.BKGND_NONE,
                                 libtcod.LEFT, line)
        y += 1


def colored_text_list(lines, width):
    """
    Display *lines* of (text, color) in a window of size *width*.
    Scroll through them if the mouse wheel is spun or the arrows are pressed.
    """
    length = len(lines)
    height = min(length, 40)
    window = libtcod.console_new(width, height)
    offset = -height

    while True:
        if offset > -height:
            offset = -height
        if offset < -length:
            offset = -length

        libtcod.console_clear(window)
        _write_log(lines[offset:length + offset + height],
                   window, 0, 0)

        x = config.SCREEN_WIDTH/2 - width/2
        y = config.SCREEN_HEIGHT/2 - height/2
        libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

        libtcod.console_flush()
        while True:
            ui.poll()
            if (ui.mouse.wheel_up or ui.key.vk == libtcod.KEY_UP or
                ui.key.vk == libtcod.KEY_KP8):
                offset = offset - 1
                break
            if (ui.mouse.wheel_down or ui.key.vk == libtcod.KEY_DOWN or
                ui.key.vk == libtcod.KEY_KP2):
                offset = offset + 1
                break
            if (ui.key.vk == libtcod.KEY_PAGEUP or
                ui.key.vk == libtcod.KEY_KP9):
                offset = offset - height
                break
            if (ui.key.vk == libtcod.KEY_PAGEDOWN or
                ui.key.vk == libtcod.KEY_KP3):
                offset = offset + height
                break
            if (ui.key.vk == libtcod.KEY_ALT or
                ui.key.vk == libtcod.KEY_CONTROL or
                ui.key.vk == libtcod.KEY_SHIFT or
                ui.key.vk == libtcod.KEY_NONE):
                break;
            return;


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


def _get_names_under_mouse(player, objects, fov_map, mouse):
    pos = ScreenCoords.toWorldCoords(player.camera_position,
                                        (mouse.cx, mouse.cy))

    names = [obj.name for obj in objects
             if obj.x == pos.x and obj.y == pos.y and
             libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

    names = ', '.join(names)
    return names.capitalize()


def _draw_object(o, player):
    # Show if it's visible to the player
    # or it's set to "always visible" and on an explored tile.
    global _con
    if (libtcod.map_is_in_fov(player.current_map.fov_map, o.x, o.y) or
            (o.always_visible and
             player.current_map.is_explored(algebra.Location(o.x, o.y)))):
        libtcod.console_set_default_foreground(_con, o.color)
        (x, y) = ScreenCoords.fromWorldCoords(player.camera_position, (o.x, o.y))
        libtcod.console_put_char(_con, x, y, o.char, libtcod.BKGND_NONE)


def clear_object(player, o):
    """
    Erase the character that represents this object.
    """
    global _con
    (x, y) = ScreenCoords.fromWorldCoords(player.camera_position, (o.x, o.y))
    libtcod.console_put_char(_con, x, y, ' ', libtcod.BKGND_NONE)


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


def _draw_fov(player):
    libtcod.console_clear(_con)
    current_map = player.current_map
    for screen_y in range(min(current_map.height, config.MAP_PANEL_HEIGHT)):
        for screen_x in range(min(current_map.width, config.MAP_PANEL_WIDTH)):
            pos = ScreenCoords.toWorldCoords(player.camera_position,
                                                        (screen_x, screen_y))
            visible = libtcod.map_is_in_fov(current_map.fov_map, pos.x, pos.y)
            wall = current_map.block_sight[pos.x][pos.y]
            if not visible:
                # If it's not visible, only draw if it's explored
                if current_map.is_explored(pos):
                    if wall:
                        _set(_con, screen_x, screen_y, color_dark_wall, libtcod.BKGND_SET)
                    else:
                        _set(_con, screen_x, screen_y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    _set(_con, screen_x, screen_y, color_light_wall, libtcod.BKGND_SET)
                else:
                    _set(_con, screen_x, screen_y, color_light_ground, libtcod.BKGND_SET)
                current_map.explore(pos)

def update_camera(player):
    x = player.x - config.MAP_PANEL_WIDTH / 2
    y = player.y - config.MAP_PANEL_HEIGHT / 2

    # Make sure the camera doesn't see outside the map.
    if x > player.current_map.width - config.MAP_PANEL_WIDTH:
        x = player.current_map.width - config.MAP_PANEL_WIDTH
    if y > player.current_map.height - config.MAP_PANEL_HEIGHT:
        y = player.current_map.height - config.MAP_PANEL_HEIGHT
    if x < 0: x = 0
    if y < 0: y = 0

    if (x, y) != player.camera_position:
        player.current_map.fov_needs_recompute = True

    player.camera_position = (x, y)


def _debug_positions(player, mouse):
    global _panel
    libtcod.console_print_ex(
        _panel, 1, 4, libtcod.BKGND_NONE,
        libtcod.LEFT, '  @x ' + str(player.x) + ' y ' + str(player.y))
    libtcod.console_print_ex(
        _panel, 1, 5, libtcod.BKGND_NONE,
        libtcod.LEFT, '  mx ' + str(mouse.cx) + ' y ' + str(mouse.cy))
    libtcod.console_print_ex(
        _panel, 1, 6, libtcod.BKGND_NONE,
        libtcod.LEFT, 'camx ' + str(player.camera_position[0]) +
                      ' y ' + str(player.camera_position[1]))


def _debug_room(player):
    global _panel
    room_index = -1
    for r in player.current_map.rooms:
        if r.isIn(player.x, player.y):
            room_index = player.current_map.rooms.index(r)
            break
    if (room_index != -1):
        libtcod.console_print_ex(
            _panel, 1, 4, libtcod.BKGND_NONE,
            libtcod.LEFT, 'Room ' + str(room_index + 1))



def render_all(player, mouse):
    global _con, _panel
    global color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground

    current_map = player.current_map
    update_camera(player)

    if current_map.fov_needs_recompute:
        # Recompute FOV if needed (the player moved or something in
        # the dungeon changed).
        libtcod.map_compute_fov(
            current_map.fov_map, player.x,
            player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        _draw_fov(player)

    # Draw all objects in the list, except the player. We want it to
    # always appear over all other objects, so it's drawn later.
    # (Could also achieve this by guaranteeing the player is always
    # the last object in current_map.objects.)
    for object in current_map.objects:
        if object != player:
            _draw_object(object, player)
    _draw_object(player, player)

    libtcod.console_blit(_con, 0, 0, config.MAP_PANEL_WIDTH,
                         config.MAP_PANEL_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_background(_panel, libtcod.black)
    libtcod.console_clear(_panel)

    # Only display the (log.MSG_HEIGHT) most recent
    _write_log(log.game_msgs[-log.MSG_HEIGHT:], _panel, MSG_X, 1)

    _render_bar(1, 1, config.BAR_WIDTH, 'HP', player.fighter.hp,
                player.fighter.max_hp,
                libtcod.light_red, libtcod.darker_red)
    libtcod.console_print_ex(
        _panel, 1, 3, libtcod.BKGND_NONE,
        libtcod.LEFT, 'Dungeon level ' + str(current_map.dungeon_level))
    _debug_positions(player, mouse)
    #_debug_room(player)    

    libtcod.console_set_default_foreground(_panel, libtcod.light_gray)
    libtcod.console_print_ex(
        _panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
        _get_names_under_mouse(player, current_map.objects, current_map.fov_map, mouse))

    # Done with "_panel", blit it to the root console.
    libtcod.console_blit(_panel, 0, 0, config.SCREEN_WIDTH, config.PANEL_HEIGHT,
                         0, 0, PANEL_Y)
