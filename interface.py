import libtcodpy as libtcod

import config
import algebra
import log
import ui
import renderer


def poll():
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                libtcod.EVENT_MOUSE, ui.key, ui.mouse)
    return (ui.key, ui.mouse)


def parse_move(key):
    """
    Returns (bool, direction, bool).
    First value is True if a direction key was pressed, False otherwise.
    Direction will be None if first value is False or the '.' or numpad 5 were pressed.
    Last value is True if shift was held (run / page-scroll), False otherwise.
    """
    key_char = chr(key.c)
    if (key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8 or
            key_char == 'k' or key_char == 'K'):
        return (True, algebra.north, key.shift)
    elif (key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2 or
            key_char == 'j' or key_char == 'J'):
        return (True, algebra.south, key.shift)
    elif (key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4 or
            key_char == 'h' or key_char == 'H'):
        return (True, algebra.west, key.shift)
    elif (key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6 or
            key_char == 'l' or key_char == 'L'):
        return (True, algebra.east, key.shift)
    elif (key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7 or
            key_char == 'y' or key_char == 'Y'):
        return (True, algebra.northwest, key.shift)
    elif (key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9 or
            key_char == 'u' or key_char == 'U'):
        return (True, algebra.northeast, key.shift)
    elif (key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1 or
            key_char == 'b' or key_char == 'B'):
        return (True, algebra.southwest, key.shift)
    elif (key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3 or
            key_char == 'n' or key_char == 'N'):
        return (True, algebra.southeast, key.shift)
    elif (key.vk == libtcod.KEY_KP5 or key_char == '.'):
        # do nothing but note that a relevant key was pressed
        return (True, None, False)
    return (False, None, False)


def _colored_text_list(lines, width):
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
        renderer.write_log(lines[offset:length + offset + height],
                           window, 0, 0)

        x = config.SCREEN_WIDTH/2 - width/2
        y = config.SCREEN_HEIGHT/2 - height/2
        libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

        libtcod.console_flush()
        while True:
            (key, mouse) = poll()
            (key_pressed, direction, shift) = parse_move(key)
            if key_pressed:
                if direction == algebra.north and not shift:
                    offset -= 1
                    break
                elif direction == algebra.south and not shift:
                    offset += 1
                    break
                elif (direction == algebra.northeast or
                        (direction == algebra.north and shift)):
                    offset -= height
                    break
                elif (direction == algebra.southeast or
                        (direction == algebra.south and shift)):
                    offset += height
                    break
            elif (key.vk == libtcod.KEY_ALT or
                  key.vk == libtcod.KEY_CONTROL or
                  key.vk == libtcod.KEY_SHIFT or
                  key.vk == libtcod.KEY_NONE):
                break
            return

def log_display(width=60):
    """
    Display the recent log history, wait for any keypress.
    """
    _colored_text_list(log.game_msgs, width)


def target_tile(actor, max_range=None):
    """
    Return the position of a tile left-clicked in player's FOV
    (optionally in a range), or (None,None) if right-clicked.
    """
    (key, mouse) = poll()
    (ox, oy) = (ui.mouse.cx, ui.mouse.cy)
    using_mouse = False
    using_keyboard = False
    (kx, ky) = renderer.ScreenCoords.fromWorldCoords(actor.camera_position,
                                                     actor.pos)
    pos = None

    while True:
        # Render the screen. This erases the inventory and shows
        # the names of objects under the mouse.
        libtcod.console_flush()
        (key, mouse) = poll()
        renderer.render_all(actor, (kx, ky))
        actor.current_map.fov_needs_recompute = False
        if (mouse.cx != ox or mouse.cy != oy):
            using_mouse = True
            using_keyboard = False
        (key_pressed, direction, shift) = _parse_move(key)
        if key_pressed:
            using_keyboard = True
            if using_mouse:
                (ox, oy) = (mouse.cx, mouse.cy)
            using_mouse = False
            if direction:
                kx += direction.x
                ky += direction.y

        if using_mouse:
            (kx, ky) = (mouse.cx, mouse.cy)
        pos = renderer.ScreenCoords.toWorldCoords(actor.camera_position, (kx, ky))
        libtcod.console_set_default_background(renderer.overlay, libtcod.black)
        libtcod.console_clear(renderer.overlay)
        (ux, uy) = renderer.ScreenCoords.fromWorldCoords(actor.camera_position,
                                                         actor.pos)
        libtcod.line_init(ux, uy, kx, ky)

        nx, ny = libtcod.line_step()
        while ((not (nx is None)) and nx >= 0 and ny >= 0 and
               nx < config.MAP_PANEL_WIDTH and
               ny < config.MAP_PANEL_HEIGHT):
            libtcod.console_set_char_background(renderer.overlay, nx, ny, libtcod.sepia, libtcod.BKGND_SET)
            nx, ny = libtcod.line_step()

        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            libtcod.console_clear(renderer.overlay)
            return None

        # Accept the target if the player clicked in FOV
        # and within the range specified.
        if ((mouse.lbutton_pressed or key.vk == libtcod.KEY_ENTER) and
                libtcod.map_is_in_fov(actor.current_map.fov_map, pos.x, pos.y) and
                (max_range is None or actor.distance(pos) <= max_range)):
            libtcod.console_clear(renderer.overlay)
            return pos
