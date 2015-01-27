
from __future__ import division
import libtcodpy as libtcod
#from it import PANEL_BACK, PANEL_FRONT

PANEL_BACK = libtcod.Color(18, 15, 15)
#PANEL_FRONT = libtcod.Color(88, 80, 64)
PANEL_FRONT = libtcod.Color(138, 115, 95)


class GuiPanel:
    def __init__(self, width, height, xoff, yoff, interface,
                 is_root=0, append_to_panels=1, transp=1,
                 backcolor=PANEL_BACK, frontcolor=PANEL_FRONT, name='default'):

        self.name = name

        if is_root == 1:
            self.con = 0 # Root console (0) or an offscreen console
        else:
            self.con = libtcod.console_new(width, height)

        self.width = width
        self.height = height

        self.xoff = xoff
        self.yoff = yoff

        self.interface = interface
        if append_to_panels:
            self.interface.gui_panels.append(self)

        self.transp=transp

        self.backcolor = backcolor
        self.frontcolor = frontcolor


        self.gen_buttons = []


        self.wmap_buttons = []
        self.wmap_dynamic_buttons = []

        self.bmap_buttons = []
        self.bmap_dynamic_buttons = []

        self.recalculate_wmap_dyn_buttons = True
        self.recalculate_bmap_dyn_buttons = True

        # Whether the panel renders itself
        self.render = 1

        # Default refresh args
        self.button_refresh_args = ()
        self.render_text_args = ()

    def update_button_refresh_func(self, func, args):
        self.button_refresh_func = func
        self.button_refresh_args = args

        self.button_refresh_func(*self.button_refresh_args)

    def update_render_text_func(self, func, args):
        self.render_text_func = func
        self.render_text_args = args

        self.render_text_func(*self.render_text_args)

    def button_refresh_func(self, *args):
        pass

    def render_text_func(self):
        pass

    def blit(self):
        libtcod.console_blit(self.con, 0, 0, self.width, self.height, 0, self.xoff, self.yoff, 1, self.transp)

    def clear(self):
        libtcod.console_clear(self.con)

    def set_fore_color(self, color):
        libtcod.console_set_default_foreground(self.con, color)

    def set_back_color(self, color):
        libtcod.console_set_default_background(self.con, color)

    def render_panel(self, map_scale, mouse):
        if self.render:
            libtcod.console_set_default_background(self.con, self.backcolor)
            libtcod.console_set_default_foreground(self.con, self.frontcolor)
            libtcod.console_clear(self.con)

            self.draw_box(0, self.width-1, 0, self.height-1, self.frontcolor)

            self.render_text_func(*self.render_text_args)

            ## "General" buttons
            for button in self.gen_buttons:
                button.display(mouse)
            # Specific to worldmap ( TODO - fix.... )
            if map_scale == 'world':
                for button in self.wmap_dynamic_buttons + self.wmap_buttons:
                    button.display(mouse)

            elif map_scale == 'human':
                for button in self.bmap_dynamic_buttons + self.bmap_buttons:
                    button.display(mouse)


    def render_bar(self, x, y, total_width, name, value, maximum, bar_color, back_color, text_color=libtcod.white,
                   show_values=False, title_inset=True):
        #render a bar (HP, experience, etc). first calculate the width of the bar
        bar_width = int(round(value / maximum * total_width))
        # Make sure the value doesn't have a million repeating decimals
        value = round(value, 1)

        #render the background first
        libtcod.console_set_default_background(self.con, back_color)
        libtcod.console_rect(self.con, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

        #now render the bar on top
        libtcod.console_set_default_background(self.con, bar_color)
        if bar_width > 0:
            libtcod.console_rect(self.con, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

        # This will cause the title to appear above the bar
        if not title_inset:
            y = y - 1
            #finally, some centered text with the values
        libtcod.console_set_default_foreground(self.con, text_color)
        if show_values:
            libtcod.console_print_ex(self.con, (x + int(round(total_width / 2))), y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))
        else:
            libtcod.console_print_ex(self.con, (x + int(round(total_width / 2))), y, libtcod.BKGND_NONE, libtcod.CENTER, name)


        libtcod.console_set_default_background(self.con, self.backcolor)
        libtcod.console_set_default_background(self.con, self.frontcolor)

    def draw_box(self, x, x2, y, y2, color=libtcod.white, corners=(218, 191, 217, 192)):
        libtcod.console_set_default_foreground(self.con, color)

        box_height = (y2 - y) + 1
        box_width = (x2 - x) + 1

        hchar = chr(196)
        vchar = chr(179)

        topline = chr(corners[0]) + (hchar * (box_width - 2)) + chr(corners[1])
        bottomline = chr(corners[3]) + (hchar * (box_width - 2)) + chr(corners[2])

        libtcod.console_print(self.con, x, y, topline)
        libtcod.console_print(self.con, x, y2, bottomline)
        # Any way to simplify down boxes?
        for ny in xrange(y + 1, box_height - 1 + (y)):
            libtcod.console_print(self.con, x, ny, vchar)
        for ny in xrange(y + 1, box_height - 1 + (y)):
            libtcod.console_print(self.con, x2, ny, vchar)


    def get_user_input(self, x, y):
        ''' Getting user to type something in '''
        mouse = libtcod.Mouse()
        key = libtcod.Key()

        player_input = ''
        key_pressed = ''
        while not key_pressed == libtcod.KEY_ENTER:
            # Clear console, print the current iteration of string, and blit
            self.clear()

            libtcod.console_print(self.con, x, y, '>> %s_' % player_input)

            self.blit()
            libtcod.console_flush()

            #key = libtcod.console_wait_for_keypress(True)
            event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

            #key_pressed = get_key(key)
            if key.vk == libtcod.KEY_CHAR: key_pressed = chr(key.c)
            else:                          key_pressed = key.vk

            #  Handle special keypresses
            if key_pressed == libtcod.KEY_SPACE:
                key_pressed = ' '

            elif key_pressed == libtcod.KEY_BACKSPACE and len(player_input) > 0:
                key_pressed = ''
                player_input = player_input[0:len(player_input) - 1]

                libtcod.console_clear(self.con)
                libtcod.console_flush()

            elif key_pressed == libtcod.KEY_ENTER:
                break

            # Try to add keypress to thing
            if isinstance(key_pressed, str):
                player_input += key_pressed

        return player_input

    def add_button(self, func, args, text, topleft, width, height, hover_header=None, hover_text=None, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=0):
        ''' Pretty ugly because the panel has multiple button lists for now... '''
        self.gen_buttons.append(Button(self, func, args, text, topleft, width, height, hover_header, hover_text, color, hcolor, do_draw_box, closes_menu))

class Button:
    # A button. Usually has a border, needs to highlight on mouseover, and execute its function on click
    def __init__(self, gui_panel, func, args, text, topleft, width, height, hover_header=None, hover_text=None, hover_text_offset=(0, 0), color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=0):
        x, y = topleft

        self.gui_panel = gui_panel
        self.con = self.gui_panel.con

        self.func = func
        self.args = args

        self.text = text

        self.hover_header = hover_header
        self.hover_text = hover_text
        self.hover_text_offset = hover_text_offset

        self.color = color
        self.hcolor = hcolor
        self.do_draw_box = do_draw_box

        # Whether clicking the button will close the menu or not
        self.closes_menu = closes_menu

        self.x = x
        self.y = y
        self.text_y = self.y + (self.do_draw_box == 1)
        self.width = width - 1
        self.height = height - 1

        self.center_x = int(self.x + ((self.width) / 2) )

        self.clicked = 0

    def click(self):
        ''' Execute the function assigned to the button '''
        # First set "self.clicked" to 1, so if self.func contains a render_all() call,
        #it doesn't get caught in a weird loop of trying to render itself while it's rendering itself
        self.clicked = 1
        # Fire the function this button was destined for
        self.func(*self.args)
        # In case clicking the button causes the panel to refresh...
        self.gui_panel.button_refresh_func(*self.gui_panel.button_refresh_args)

        self.clicked = 0

        if self.closes_menu:
            self.gui_panel.interface.prepare_to_delete_panel(self.gui_panel)


    def mouse_is_inside(self, mouse):
        return self.x <= mouse.cx - self.gui_panel.xoff <= self.x + self.width and self.y <= mouse.cy - self.gui_panel.yoff <= self.y + self.height

    def display(self, mouse):
        ''' Display the button, and highlight if necessary '''
        color = self.color
        # Highlight
        if self.mouse_is_inside(mouse):
            color = self.hcolor

            if self.hover_text:
                #hover_info(interface=interface, header=['t'], text=self.hover_text, xb=self.x, yb=self.y-10, transp=0)
                interface.add_hover_info(interface=interface, header=self.hover_header, text=self.hover_text, cx=mouse.cx + self.hover_text_offset[0], cy=mouse.cy + self.hover_text_offset[1], transp=1, do_hover=0)

            # Handle clicks
            if mouse.lbutton_pressed and not self.clicked:
                mouse.lbutton_pressed = 0
                self.click()

        if self.do_draw_box:
            self.gui_panel.draw_box(self.x, self.x + self.width, self.y, self.y + self.height, color)

        libtcod.console_set_default_foreground(self.con, color)

        libtcod.console_print_rect_ex(con=self.con, x=self.center_x, y=self.text_y, w=self.width, h=self.height,
                                      flag=libtcod.BKGND_NONE, alignment=libtcod.CENTER, fmt=self.text)

        libtcod.console_set_default_foreground(self.gui_panel.con, self.gui_panel.frontcolor)


class PlayerInterface:
    def __init__(self):

        self.gui_panels = []
        self.panel_deletions = []
        self.game = None
        self.hover_info = None

    def get_panels(self, panel_name):
        ''' Used to get a panels, perhaps to force refresh etc '''
        matching_panels = [panel for panel in self.gui_panels if panel.name == panel_name]

        return matching_panels

    def prepare_to_delete_panel(self, panel):
        self.panel_deletions.append(panel)

    def delete_panel(self, panel):
        self.gui_panels.remove(panel)
        libtcod.console_delete(panel.con)
        self.panel_deletions.remove(panel)
        self.game.handle_fov_recompute()

    def set_game(self, game):
        self.game = game

    def add_hover_info(self, interface, header, text, cx, cy, xoffset=2, yoffset=2, hoffset=2, textc=libtcod.grey, bcolor=libtcod.black, transp=.5, xy_corner=0, do_hover=1):
        self.hover_info = HoverInfo(interface, header, text, cx, cy, xoffset, yoffset, hoffset, textc, bcolor, transp, xy_corner, do_hover)

    def clear_hover_info(self):
        self.hover_info = None
        self.game.handle_fov_recompute()

class HoverInfo:
    def __init__(self, interface, header, text, cx, cy, xoffset=2, yoffset=2, hoffset=2, textc=libtcod.grey, bcolor=libtcod.black, transp=.5, xy_corner=0, do_hover=1):

        self.interface = interface
        self.header = header
        self.text = text
        self.cx = cx
        self.cy = cy
        self.xoffset = xoffset
        self.yoffset = yoffset
        self.hoffset = hoffset
        self.textc = textc
        self.bcolor = bcolor
        self.transp = transp
        self.xy_corner = xy_corner
        self.do_hover = do_hover

        if self.do_hover:
            self.hover()

    def hover(self):
        width = len(max(self.text + self.header, key=len)) + (self.xoffset * 2)

        if self.header == []:   header_height = 0
        else:                   header_height = len(self.header) + 2

        height = len(self.text) + header_height + self.yoffset + self.hoffset


        wpanel = GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface, is_root=0, append_to_panels=0)

        # Header
        libtcod.console_set_default_foreground(wpanel.con, self.textc)
        y = self.yoffset
        for line in self.header:
            libtcod.console_print(wpanel.con, self.xoffset, y, line)
            y += 1

        # Text
        y = header_height + self.hoffset
        for line in self.text:
            #color_current = self.textc
            libtcod.console_print(wpanel.con, self.xoffset, y, line)
            y += 1

        # Draw box around menu if parameter is selected
        if self.bcolor is not None:
            wpanel.draw_box(0, width - 1, 0, height - 1, self.textc)


        if not self.xy_corner:
            # center to coords. Fix for hanging over the left side of the screen and the top of the screen, not yet fixed for right/bottom side.
            x = max(0, int(self.cx - int(width/2) ))
            y = max(0, self.cy - height)
        else:
            x, y = self.cx, self.cy
        # Blit to root console + flush to present changes
        libtcod.console_blit(wpanel.con, 0, 0, width, height, 0, x, y, 1.0, self.transp)
        #libtcod.console_flush()
        libtcod.console_delete(wpanel.con)

        if not self.do_hover:
            self.interface.clear_hover_info()



interface = PlayerInterface()


