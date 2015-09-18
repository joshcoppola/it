from __future__ import division
from collections import Counter

import libtcodpy as libtcod
import config as g
import gen_languages as lang
from helpers import join_list, looped_increment, trim
from traits import *


mouse = libtcod.Mouse()
key = libtcod.Key()


class GuiPanel:
    def __init__(self, width, height, xoff, yoff, interface,
                 is_root=0, append_to_panels=1, transp=1,
                 backcolor=g.PANEL_BACK, frontcolor=g.PANEL_FRONT, name='default'):

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
        # Auto-set default panel colors
        libtcod.console_set_default_background(self.con, backcolor)
        libtcod.console_set_default_foreground(self.con, frontcolor)


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
            y -= 1
            #finally, some centered text with the values
        libtcod.console_set_default_foreground(self.con, text_color)
        if show_values:
            libtcod.console_print_ex(self.con, (x + int(round(total_width / 2))), y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))
        else:
            libtcod.console_print_ex(self.con, (x + int(round(total_width / 2))), y, libtcod.BKGND_NONE, libtcod.CENTER, name)


        libtcod.console_set_default_background(self.con, self.backcolor)
        libtcod.console_set_default_foreground(self.con, self.frontcolor)

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

    def add_button(self, func, args, text, topleft, width, height, hover_header=None, hover_text=None, hover_text_offset=(0, 0), color=g.PANEL_FRONT, hcolor=None, do_draw_box=True, closes_menu=0):
        ''' Pretty ugly because the panel has multiple button lists for now... '''
        self.gen_buttons.append(Button(self, func, args, text, topleft, width, height, hover_header, hover_text, hover_text_offset, color, hcolor, do_draw_box, closes_menu))

class Button:
    # A button. Usually has a border, needs to highlight on mouseover, and execute its function on click
    def __init__(self, gui_panel, func, args, text, topleft, width, height, hover_header=None, hover_text=None, hover_text_offset=(0, 0), color=g.PANEL_FRONT, hcolor=None, do_draw_box=True, closes_menu=0):
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
        self.hcolor = hcolor if hcolor else self.color * 1.5
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
                self.gui_panel.interface.add_hover_info(interface=self.gui_panel.interface, header=self.hover_header, text=self.hover_text, cx=mouse.cx + self.hover_text_offset[0], cy=mouse.cy + self.hover_text_offset[1], transp=1, do_hover=0)

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
        self.map_console = None
        self.root_console = None
        self.panel_deletions = []
        self.game = None
        self.hover_info = None

    def set_root_panel(self, root_console):
        self.root_console = root_console

    def set_map_panel(self, map_console):
        self.map_console = map_console

    def set_panels(self, panels):
        self.panels = panels

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


        wpanel = GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=self.interface, is_root=0, append_to_panels=0)

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



















def show_people(world):
    # Show people within realms
    curr_p = 0 # current person
    city_number = 0 # City #

    x_att_offset = 10 #  where to offset attribute offsets from
    x_list_offset = 35 #where to offset list of people from

    libtcod.console_clear(0) ## 0 should be variable "con"?
    libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
    libtcod.console_set_default_background(0, g.PANEL_BACK)
    libtcod.console_flush()

    key_pressed = None
    while key_pressed != libtcod.KEY_ESCAPE:
        if key_pressed == libtcod.KEY_DOWN:
            curr_p -= 1
        elif key_pressed == libtcod.KEY_UP:
            curr_p += 1
        if key_pressed == libtcod.KEY_LEFT:
            city_number -= 1
        elif key_pressed == libtcod.KEY_RIGHT:
            city_number += 1

        libtcod.console_clear(0) ## 0 should be variable "con"?
        libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
        libtcod.console_print(0, 2, 2, 'Civ people (ESC to exit, LEFT and RIGHT arrows to scroll)')

        selected_person = world.tiles[world.cities[city_number].x][world.cities[city_number].y].entities[curr_p]
        s_att = selected_person.creature
        ## Traits ##
        y = 7
        ## Skills ##
        y += 2
        libtcod.console_print(0, x_att_offset, y, 'Traits')
        y += 1
        for trait, m in selected_person.creature.traits.iteritems():
            y += 1
            libtcod.console_print(0, x_att_offset, y, tdesc(trait, m))

        ###
        color = libtcod.white
        libtcod.console_set_default_foreground(0, color)

        libtcod.console_print(0, x_att_offset, 4, '<< ' + world.tiles[world.cities[city_number].x][world.cities[city_number].y].entities[curr_p].fullname() + ' >>')
        ##### Only show people who this person knows personally for now
        y = 0
        for other_person in selected_person.creature.knowledge['entities']:
            if y + 20 > g.SCREEN_HEIGHT: # Just make sure we don't write off the screen...
                libtcod.console_print(0, x_list_offset, y + 9, '<<< more >>>')
                break

            # Use total opinions (includes trait info)
            total_opinion = selected_person.creature.get_relations(other_person)
            opinion = sum(total_opinion.values())

            y += 1
            if opinion < -3:
                color = libtcod.red
            elif opinion > 3:
                color = libtcod.green
            else:
                color = libtcod.cyan

            libtcod.console_set_default_foreground(0, color)
            libtcod.console_print(0, x_list_offset, y + 8,
                                  other_person.creature.owner.fullname() + ' (' + str(opinion) + ')')
            y += 1
            for reason, amount in total_opinion.iteritems():
                libtcod.console_print(0, x_list_offset, y + 8, reason + ': ' + str(amount))
                y += 1


            ### Flush, and check keys ###
        libtcod.console_flush()

        key = libtcod.console_wait_for_keypress(False)
        key_pressed = g.game.get_key(key)


def show_cultures(world, spec_culture=None):
    index = 0

    key_pressed = None
    event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

    while key_pressed != libtcod.KEY_ESCAPE:
        #### If there's been a specific culture specified
        if spec_culture:
            culture = spec_culture
            language = culture.language

        #### Handle flipping through the world's cultures with the arrow keys
        else:
            if key_pressed == libtcod.KEY_LEFT:
                index = looped_increment(initial_num=index, max_num=len(g.WORLD.cultures)-1, increment_amt=-1)
            elif key_pressed == libtcod.KEY_RIGHT:
                index = looped_increment(initial_num=index, max_num=len(g.WORLD.cultures)-1, increment_amt=-1)

            culture = world.cultures[index]
            language = culture.language

        # Clear console
        libtcod.console_clear(0) ## 0 should be variable "con"?

        culture_box_y = 13
        language_box_y = culture_box_y + 1

        #### General ######
        g.game.interface.root_console.draw_box(0, g.SCREEN_WIDTH - 1, 0, g.SCREEN_HEIGHT - 1, g.PANEL_FRONT) #Box around everything
        ## Box around cultural descriptions
        g.game.interface.root_console.draw_box(1, g.SCREEN_WIDTH - 2, 1, culture_box_y, g.PANEL_FRONT)
        ## Header
        libtcod.console_print(0, 2, 2, 'Cultures and Languages (ESC to exit, LEFT and RIGHT arrows to scroll)')

        libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
        libtcod.console_set_default_background(0, g.PANEL_BACK)
        libtcod.console_print(0, 4, 4, '-* The {0} culture *-'.format(culture.name))

        ## Background info, including subsitence and races
        libtcod.console_print(0, 4, 6, 'The {0} are a {1}-speaking {2} culture of {3}.'.format(culture.name, language.name.capitalize(), culture.subsistence, join_list([c.capitalize() for c in culture.races])))
        traits = [tdesc(trait, m) for (trait, m) in culture.culture_traits.iteritems()]
        libtcod.console_print(0, 4, 7, 'They are considered {0}'.format(join_list(traits)))
        ## Religion
        libtcod.console_print(0, 4, 9, 'They worship {0} gods in the Pantheon of {1}'.format(len(culture.pantheon.gods), culture.pantheon.gods[0].fulltitle()))
        ## Cultural weapons
        libtcod.console_print(0, 4, 11, 'Their arsenal includes {0}'.format(join_list(culture.weapons)))

        ###### PHONOLOGY ########
        g.game.interface.root_console.draw_box(x=1, x2=40, y=language_box_y, y2=language_box_y + 2 + len(language.consonants), color=g.PANEL_FRONT)
        y = language_box_y + 1
        libtcod.console_print(0, 4, y, 'Consonants in {0}'.format(language.name))
        for consonant in language.consonants:
            y += 1
            cnum = consonant.num
            libtcod.console_print(0, 4, y, language.orthography.mapping[cnum])
            libtcod.console_print(0, 7, y, lang.PHON_TO_ENG_EXAMPLES[cnum])

        y += 4
        g.game.interface.root_console.draw_box(x=1, x2=40, y=y-1, y2=y-1 + 2 + len(language.vowel_freqs), color=g.PANEL_FRONT)
        libtcod.console_print(0, 4, y, 'Vowels in {0}'.format(language.name))
        for (vnum, vfreq) in language.vowel_freqs:
            y += 1
            libtcod.console_print(0, 4, y, language.orthography.mapping[vnum])
            libtcod.console_print(0, 7, y, lang.PHON_TO_ENG_EXAMPLES[vnum])
        ###### / PHONOLOGY #######

        ###### VOCABULARY ########
        y = language_box_y + 1
        g.game.interface.root_console.draw_box(x=41, x2=68, y=y-1, y2=y-1 + 2 + len(language.vocabulary), color=g.PANEL_FRONT)
        libtcod.console_print(0, 43, y, 'Basic {0} vocabulary'.format(language.name))
        sorted_vocab = [(k, v) for k, v in language.vocabulary.iteritems()]
        sorted_vocab.sort()
        for (eng_word, word) in sorted_vocab:
            y += 1
            if y > g.SCREEN_HEIGHT - 2:
                break
            libtcod.console_print(0, 43, y, eng_word)
            libtcod.console_print(0, 55, y, word)

        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        key_pressed = g.game.get_key(key)


def show_civs(world):
    city_number = 0
    minr, maxr = 0, g.SCREEN_HEIGHT - 6

    view = 'economy'

    key_pressed = None
    event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

    while key_pressed != libtcod.KEY_ESCAPE:
        if key_pressed == libtcod.KEY_PAGEUP or mouse.wheel_up:
            if not minr - 1 < 0:
                minr -= 1
                maxr -= 1
        if key_pressed == libtcod.KEY_PAGEDOWN or mouse.wheel_down:
            if not maxr + 1 > len(all_agents):
                maxr += 1
                minr += 1

        if key_pressed == libtcod.KEY_LEFT:
            city_number -= 1
            minr, maxr = 0, g.SCREEN_HEIGHT - 6
        if key_pressed == libtcod.KEY_RIGHT:
            city_number += 1
            minr, maxr = 0, g.SCREEN_HEIGHT - 6

        if city_number < 0:
            city_number = len(world.cities) - 1
        elif city_number > len(world.cities) - 1:
            city_number = 0

        libtcod.console_clear(0) ## 0 should be variable "con"?

        #### Set current variables ####
        city = world.cities[city_number]
        ################################

        if key_pressed == 'p':
            show_people(world=world)
        elif key_pressed == 'e':
            view = 'economy'
        elif key_pressed == 'd':
            economy_tab(world=world, city=city)
        elif key_pressed == 'b':
            view = 'building'
        elif key_pressed == 'f':
            view = 'figures'
        elif key_pressed == 'c':
            show_cultures(world=world, spec_culture=city.culture)
        elif key_pressed == 'r':
            world.cities[city_number].econ.run_simulation()
        elif key_pressed == 'a':
            city.econ.graph_results(solid=city.econ.get_all_available_commodity_tokens(), dot=[])


        #### General ######
        g.game.interface.root_console.draw_box(0, g.SCREEN_WIDTH - 1, 0, g.SCREEN_HEIGHT - 1, g.PANEL_FRONT) #Box around everything
        g.game.interface.root_console.draw_box(1, g.SCREEN_WIDTH - 2, 1, 7, g.PANEL_FRONT)
        libtcod.console_print(0, 2, 2, 'Civilizations (ESC to exit, LEFT and RIGHT arrows to change city, PGUP PGDOWN to scroll vertically)')
        libtcod.console_print(0, 2, 4, '<p> Show people   <b> Show buildings   <f> Show figures   <e> Show economy   <d> Detailed economy   <c> Culture')

        ## Show government type - left panel
        #g.game.interface.root_console.draw_box(1, 28, 8, g.SCREEN_HEIGHT - 2, g.PANEL_FRONT) # Around relations
        # Check for title holder

        # if city.faction.leader:
        #     title_info = '{0} {1}, age {2}'.format(city.faction.leader_prefix, city.faction.get_leader().fullname(), city.faction.get_leader().creature.get_age())
        # else:
        #     title_info = 'No holder'
        # libtcod.console_print(0, 2, 11, title_info)
        # libtcod.console_print(0, 2, 12, 'Dynastic heirs:')
        #
        # y = 13
        # for heir in city.faction.heirs:
        #     libtcod.console_print(0, 2, y, '{0}, age {1}'.format(heir.fullname(), heir.creature.get_age()))
        #     y += 1

        ######### Cities and governers #############
        g.game.interface.root_console.draw_box(1, g.SCREEN_WIDTH - 2, 8, g.SCREEN_HEIGHT - 2, g.PANEL_FRONT) # Around cities + govs

        y = 14
        libtcod.console_set_default_foreground(0, libtcod.color_lerp(city.color, g.PANEL_FRONT, .5))
        libtcod.console_print(0, 4, y - 4, 'City of {0} (Population: {1}, {2} gold)'.format(city.name, city.get_population(), city.treasury))
        libtcod.console_print(0, 4, y - 3, 'Access to: {0}'.format(join_list(city.native_res.keys())))
        if city.faction.parent is None:
            liege = ' * Independent *  '
        else:
            liege = 'Vassal to ' + city.faction.parent.site.name + '. '
        libtcod.console_print(0, 4, y - 2, liege + 'Vassals: ' + ', '.join([vassal.site.name for vassal in city.faction.subfactions]))
        libtcod.console_set_default_foreground(0, g.PANEL_FRONT)

        if view == 'building':
            ####### Positions of interest in the city ###########
            libtcod.console_print(0, 4, y, '-* Important structures *-')

            y += 1
            for building in city.buildings:
                y += 1
                if y > g.SCREEN_HEIGHT - 12:
                    libtcod.console_print(0, 4, y, '<< More >> ')
                    break

                libtcod.console_print(0, 4, y, '-* ' + building.name + ' *- ')
                for worker in building.current_workers:
                    y += 1
                    libtcod.console_print(0, 4, y, worker.fulltitle())
                y += 1


        elif view == 'economy':

            ####### AGENTS ############
            libtcod.console_set_default_foreground(0, g.PANEL_FRONT * .7)
            libtcod.console_print(0, 4, y, 'Agent name')
            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.yellow, g.PANEL_FRONT, .7))
            libtcod.console_print(0, 30, y, 'Gold')

            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.light_yellow, g.PANEL_FRONT, .7))
            libtcod.console_print(0, 40, y, 'g/i')

            #libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.blue, g.PANEL_FRONT, .7))
            #libtcod.console_print_ex(0, 40, y, libtcod.BKGND_NONE, libtcod.RIGHT, 'Buys')
            #libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.cyan, g.PANEL_FRONT, .7))
            #libtcod.console_print(0, 46, y, 'Sells')
            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.green, g.PANEL_FRONT, .7))
            libtcod.console_print(0, 52, y, 'Alive')

            libtcod.console_set_default_foreground(0, g.PANEL_FRONT)


            all_agents = (city.econ.all_agents + city.econ.buy_merchants + city.econ.sell_merchants)
            merchants = city.econ.buy_merchants + city.econ.sell_merchants

            for agent in all_agents[minr:maxr]:
                y += 1
                if y > g.SCREEN_HEIGHT - 5:
                    break


                if agent in merchants and agent.current_location == city:
                    agent_name = '{0} {1} (here)'.format(agent.name, agent.id_)
                elif agent in merchants and agent.current_location is not None:
                    agent_name = '{0} {1} ({2})'.format(agent.name, agent.id_, agent.current_location.owner.name)
                elif agent in merchants and agent.current_location is None:
                    agent_name = '{0} {1} (traveling)'.format(agent.name, agent.id_)
                else:
                    agent_name = '{0} {1}'.format(agent.name, agent.id_)

                if agent.attached_to == g.player:
                    agent_name += ' (you)'

                ### (debug) Player can take on role of economy agent at a whim
                if mouse.cy == y and 4 <= mouse.cx <= 85:
                    acolor = libtcod.dark_yellow

                    # Set the g.player to "become" one of these agents
                    if mouse.lbutton_pressed:
                        agent.update_holder(figure=g.player)

                        for panel in g.game.interface.gui_panels:
                            if panel.name == 'Panel4':
                                break

                        panel.render = True
                        pcolor = libtcod.color_lerp(g.PANEL_FRONT, libtcod.light_green, .5)
                        panel.wmap_buttons.append(Button(gui_panel=panel, func=g.WORLD.time_cycle.goto_next_week, args=[],
                                                              text='Advance', topleft=(15, 40), width=12, height=3, color=pcolor, do_draw_box=True) )

                else:
                    acolor = g.PANEL_FRONT

                libtcod.console_set_default_foreground(0, acolor)
                libtcod.console_print(0, 4, y, agent_name[:26])
                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.yellow, g.PANEL_FRONT, .7))
                libtcod.console_print(0, 30, y, str(agent.gold))

                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.light_yellow, g.PANEL_FRONT, .7))
                libtcod.console_print(0, 40, y, '{0:.2f}'.format(agent.gold / agent.population_number))

                #libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.blue, g.PANEL_FRONT, .7))
                #libtcod.console_print(0, 40, y, str(agent.buys))
                #libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.cyan, g.PANEL_FRONT, .7))
                #libtcod.console_print(0, 46, y, str(agent.sells))
                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.green, g.PANEL_FRONT, .7))
                libtcod.console_print(0, 52, y, str(agent.turns_alive))

            # Set color back
            libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
            ###### End print individual agents ######

            ## Print good info ##
            y = 12
            libtcod.console_print(0, 60, y - 2, 'Most demanded last turn: ' + city.econ.find_most_demanded_commodity(restrict_based_on_available_resource_slots=0))

            libtcod.console_print(0, 60, y, 'Commodity')
            libtcod.console_print(0, 78, y, 'Avg$')
            libtcod.console_print(0, 84, y, 'Last$')
            libtcod.console_print(0, 90, y, 'Sply')
            libtcod.console_print(0, 96, y, 'Dmnd')
            libtcod.console_print(0, 102, y, 'D:S')
            libtcod.console_print(0, 108, y, 'G')

            y += 2

            # Loop through each type of commodity, show overall supply / demand, and then print out all items of that type
            for type_of_commodity, auctions in sorted(city.econ.auctions_by_category.iteritems()):

                total_supply_for_this_type = sum(auct.supply for auct in auctions)
                total_demand_for_this_type = sum(auct.demand for auct in auctions)
                d_s_ratio = total_demand_for_this_type / max(total_supply_for_this_type, 1)


                libtcod.console_set_default_foreground(0, g.PANEL_FRONT * .5)
                libtcod.console_print(0, 60, y, type_of_commodity)

                if len(auctions) > 1:
                    libtcod.console_print(0, 90, y, str(total_supply_for_this_type))
                    libtcod.console_print(0, 96, y, str(total_demand_for_this_type))
                    libtcod.console_print(0, 102, y, "{0:.2f}".format(round(d_s_ratio, 2)))

                libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
                y+= 1

                # Display info about each printed commodity
                for auction in sorted(auctions, key=lambda auct: auct.mean_price, reverse=True):
                    commodity = auction.commodity
                    # Mark whether it's imported / exported
                    if   commodity in city.get_all_imports():  libtcod.console_print(0, 60, y, chr(25))
                    elif commodity in city.get_all_exports():  libtcod.console_print(0, 60, y, chr(26))

                    # Name of commodity / mean price
                    libtcod.console_print(0, 62, y, commodity)
                    libtcod.console_print(0, 78, y, str(auction.mean_price))

                    # Color trades - green means price last round was > than avg, red means < than avg
                    if auction.mean_price <= auction.get_last_valid_price():
                        color = libtcod.color_lerp(libtcod.green, g.PANEL_FRONT, auction.mean_price / max(1, auction.get_last_valid_price()) ) #prevent division by 0
                    else:
                        color = libtcod.color_lerp(libtcod.red, g.PANEL_FRONT, auction.get_last_valid_price() / max(1, auction.mean_price) ) #prevent division by 0
                    libtcod.console_set_default_foreground(0, color)
                    libtcod.console_print(0, 84, y, str(auction.get_last_valid_price()))
                    ## /color trades
                    libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
                    libtcod.console_print(0, 90, y, str(auction.supply))
                    libtcod.console_print(0, 96, y, str(auction.demand))
                    # Ratio
                    d_s_ratio = auction.demand / max(auction.supply, 1)

                    if auction.supply == 0:
                        color_mod = .5
                        color = libtcod.red
                    elif auction.demand == 0:
                        color_mod = .5
                        color = libtcod.magenta
                    else:
                        color_mod = min(abs(1 - d_s_ratio), .75)
                        color = libtcod.green

                    libtcod.console_set_default_foreground(0, libtcod.color_lerp(color, g.PANEL_FRONT, color_mod))
                    libtcod.console_print(0, 102, y, "{0:.2f}".format(round(d_s_ratio, 2)))
                    libtcod.console_set_default_foreground(0, g.PANEL_FRONT)

                    # Iteration in economy
                    # libtcod.console_print(0, 108, y, str(auction.iterations))
                    libtcod.console_print(0, 108, y, str(city.econ.collected_taxes[commodity]) )
                    libtcod.console_print(0, 114, y, '+{0}'.format(city.econ.collected_taxes_history[commodity][-1]) )
                    y += 1
                # y += 1

            # Prepare agent counts for a summary table
            agents_condensed = [a.name for a in city.econ.all_agents]
            for m in city.econ.sell_merchants:
                agents_condensed.append('{0} (sell)'.format(m.name))
            for m in city.econ.buy_merchants:
                agents_condensed.append('{0} (buy)'.format(m.name))

            agent_counts = Counter(agents_condensed)
            agent_counts_sorted = [(k, v) for k, v in agent_counts.iteritems()]
            agent_counts_sorted.sort(key=lambda x: x[1], reverse=True)


            secotion_2_y = y + 3
            y = secotion_2_y

            libtcod.console_print(0, 60, y - 1, '-* {0} agents *-'.format(len(agents_condensed)))


            for agent_name, num in agent_counts_sorted:
                y += 1
                if y < g.SCREEN_HEIGHT - 5:
                    libtcod.console_print(0, 60, y, '{0} {1}'.format(num, trim(agent_name, 26)))



            ### Good info ###
            y = secotion_2_y

            libtcod.console_print(0, 90, y - 1, '-* Imports *-')
            for other_city, commodities in city.imports.iteritems():
                for commodity in commodities:
                    y += 1
                    if y < g.SCREEN_HEIGHT - 5:
                        libtcod.console_print(0, 90, y, '{0} from {1}'.format(commodity, other_city.name))

            y += 3
            libtcod.console_print(0, 90, y - 1, '-* Exports *-')
            for other_city, commodities in city.exports.iteritems():
                for commodity in commodities:
                    y += 1
                    if y < g.SCREEN_HEIGHT - 5:
                        libtcod.console_print(0, 90, y, '{0} to {1}'.format(commodity, other_city.name))
                        ## End print good info ##


        elif view == 'figures':
            selected = False
            ## Figures currently residing here
            y = 16
            ny = y # for opinions

            libtcod.console_print(0, 34, y - 2, '{0} notable characters'.format(len(world.tiles[city.x][city.y].entities)))
            for figure in world.tiles[city.x][city.y].entities:
                if y > g.SCREEN_HEIGHT - 5:
                    break

                ##
                #if 34 <= mouse.cx <= 34+len(figure.fullname()) and mouse.cy == y:
                if 34 <= mouse.cx <= 60 + len(figure.creature.get_profession()) and mouse.cy == y:
                    selected = True

                    if figure.creature.sex:
                        symb = chr(11)
                        color = libtcod.light_blue
                    else:
                        color = libtcod.light_red
                        symb = chr(12)

                    libtcod.console_set_default_foreground(0, color)
                    libtcod.console_print(0, 85, ny, symb)
                    libtcod.console_set_default_foreground(0, g.PANEL_FRONT)

                    libtcod.console_print(0, 87, ny, figure.fullname())
                    libtcod.console_print(0, 85, ny + 1,
                                          figure.creature.get_profession() + ', age ' + str(figure.creature.get_age()))

                    spouseinfo = 'No spouse'
                    if figure.creature.spouse:
                        end = ''
                        if figure.creature.spouse.creature.status == 'dead':
                            end = ' (dead)'
                        spouseinfo = 'Married to ' + figure.creature.spouse.fulltitle() + end

                    libtcod.console_print(0, 85, ny + 2, spouseinfo)

                    if figure.creature.current_citizenship == city:
                        info = 'Currently lives here'
                    else:
                    #    info = 'Staying at ' + random.choice(city.get_building_type('Tavern')).get_name()
                        info = 'Currently visiting'

                    libtcod.console_print(0, 85, ny + 3, info)

                    ny += 4
                    for trait, m in figure.creature.traits.iteritems():
                        libtcod.console_print(0, 85, ny + 1, tdesc(trait, m))
                        ny += 1

                    ny += 1
                    for issue, (opinion, reasons) in figure.creature.opinions.iteritems():
                        ny += 1
                        ##
                        s = issue + ': ' + str(opinion)
                        libtcod.console_print(0, 85, ny, s)
                        for reason, amount in reasons.iteritems():
                            ny += 1
                            libtcod.console_print(0, 86, ny, reason + ': ' + str(amount))

                if selected:
                    libtcod.console_set_default_foreground(0, libtcod.color_lerp(g.PANEL_FRONT, libtcod.yellow, .5))
                    selected = False

                elif libtcod.console_get_default_foreground != g.PANEL_FRONT:
                    libtcod.console_set_default_foreground(0, g.PANEL_FRONT)

                libtcod.console_print(0, 34, y, figure.fullname())

                libtcod.console_print(0, 57, y, str(figure.creature.get_age()))

                libtcod.console_print(0, 60, y, figure.creature.get_profession())

                if figure.creature.dynasty:
                    libtcod.console_put_char_ex(0, 32, y, figure.creature.dynasty.symbol,
                                                figure.creature.dynasty.symbol_color,
                                                figure.creature.dynasty.background_color)

                if figure.creature.sex:
                    symb = chr(11)
                    color = libtcod.light_blue
                else:
                    color = libtcod.light_red
                    symb = chr(12)

                libtcod.console_set_default_foreground(0, color)
                libtcod.console_print(0, 55, y, symb)
                libtcod.console_set_default_foreground(0, g.PANEL_FRONT)


                # Increase so next figure goes onto next line
                y += 1

        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        key_pressed = g.game.get_key(key)

def economy_tab(world, city):
    agent_index = 0

    key_pressed = None
    event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

    while key_pressed != libtcod.KEY_ESCAPE:
        if key_pressed == libtcod.KEY_PAGEUP:
            if agent_index - 1 < 0:
                pass
            else:
                agent_index -= 1
        if key_pressed == libtcod.KEY_PAGEDOWN:
            agent_index += 1

        if key_pressed == libtcod.KEY_UP:
            agent_index = 0
        if key_pressed == libtcod.KEY_DOWN:
            agent_index = 0

        elif key_pressed == 'p':
            show_people(world=world)
        elif key_pressed == 'e':
            view = 'economy'
        elif key_pressed == 'b':
            view = 'building'
        elif key_pressed == 'r':
            city.econ.run_simulation()

        libtcod.console_clear(0) ## 0 should be variable "con"?

        #### General ######
        g.game.interface.root_console.draw_box(0, g.SCREEN_WIDTH - 1, 0, g.SCREEN_HEIGHT - 1, g.PANEL_FRONT) #Box around everything
        g.game.interface.root_console.draw_box(1, g.SCREEN_WIDTH - 2, 1, 7, g.PANEL_FRONT)
        libtcod.console_print(0, 2, 2, 'Civilizations (ESC to exit, LEFT and RIGHT arrows to scroll)')
        libtcod.console_print(0, 2, 4, '<p> - Show people    <b> - Show buildings    <f> - Show figures    <e> Show economy')

        libtcod.console_set_default_foreground(0, g.PANEL_FRONT)
        libtcod.console_print(0, 2, 5, '{0} square km. Access to: {1}'.format(len(city.territory), join_list(city.native_res.keys())))

        ####### AGENTS ############
        y = 10

        libtcod.console_set_default_foreground(0, g.PANEL_FRONT * .7)
        libtcod.console_print(0, 5, y, 'Agent name')
        libtcod.console_print(0, 25, y, 'Inventory')
        libtcod.console_print(0, 45, y, 'Beliefs')

        libtcod.console_set_default_foreground(0, g.PANEL_FRONT)

        iy, cy, ly = y, y, y
        agent_list = city.econ.all_agents
        if agent_index > len(agent_list) - 6:
            agent_index = len(agent_list) - 6
        for agent in agent_list[agent_index:agent_index + 6]:
            y = max(iy, cy, ly, y + 6) + 1
            if y > 70:
                break
            libtcod.console_print(0, 5, y, agent.name)
            libtcod.console_print(0, 5, y + 1, '{0} gold'.format(agent.gold))
            libtcod.console_print(0, 5, y + 2, '{0} buys'.format(agent.buys))
            libtcod.console_print(0, 5, y + 3, '{0} sells'.format(agent.sells))
            libtcod.console_print(0, 5, y + 4, 'Alive: {0}'.format(agent.turns_alive))
            #libtcod.console_print(0, 5, y + 5, '{0} since food'.format(agent.turns_since_food))

            iy = y
            for item, amount in agent.input_product_inventory.iteritems():
                libtcod.console_print(0, 25, iy, '{0} ({1})'.format(item, amount))
                iy += 1
                if iy > 70: break
            for item, amount in agent.buy_inventory.iteritems():
                libtcod.console_print(0, 25, iy, '{0} ({1})'.format(item, amount))
                iy += 1
                if iy > 70: break

            cy, ly = y, y
            if agent in city.econ.all_agents:
                for commodity, value in agent.perceived_values[agent.buy_economy].iteritems():
                    libtcod.console_print(0, 45, cy, '{0}: {1} ({2})'.format(commodity, value.center, value.uncertainty))
                    cy += 1
                    if cy > 70: break

                for j in xrange(len(agent.last_turn)):
                    libtcod.console_print(0, 70, ly, agent.last_turn[j])
                    ly += 1
                    if ly > 70: break

            elif agent in city.econ.buy_merchants + city.econ.sell_merchants and agent.current_location == city.econ:
                for commodity, value in agent.perceived_values[agent.buy_economy].iteritems():
                    libtcod.console_print(0, 45, cy, '{0} - {1}: {2} ({3})'.format(agent.buy_economy.owner.name, commodity, value.center, value.uncertainty))
                    cy += 1
                    if cy > 70: break
                for commodity, value in agent.perceived_values[agent.sell_economy].iteritems():
                    libtcod.console_print(0, 45, cy, '{0} - {1}: {2} ({3})'.format(agent.sell_economy.owner.name, commodity, value.center, value.uncertainty))
                    cy += 1
                    if cy > 70: break

                for j in xrange(len(agent.last_turn)):
                    libtcod.console_print(0, 70, ly, agent.last_turn[j])
                    ly += 1
                    if ly > 70: break

                    ###### End print individual agents ######
        '''
        ## Print good info ##
        y = 12
        libtcod.console_print_left(0, 80, y, libtcod.BKGND_NONE, 'Commodity')
        libtcod.console_print_left(0, 95, y, libtcod.BKGND_NONE, 'Avg/LR/Sply/Dmnd/iterations')

        y += 2

        for commodity, auction in city.econ.auctions.iteritems():
            if auction.supply != None and auction.demand != None:
                libtcod.console_print_left(0, 80, y, libtcod.BKGND_NONE, commodity)
                libtcod.console_print_left(0, 95, y, libtcod.BKGND_NONE, str(auction.mean_price))
                libtcod.console_print_left(0, 100, y, libtcod.BKGND_NONE, str(auction.price_history[-1]))
                libtcod.console_print_left(0, 104, y, libtcod.BKGND_NONE, str(auction.supply))
                libtcod.console_print_left(0, 108, y, libtcod.BKGND_NONE, str(auction.demand))
                libtcod.console_print_left(0, 112, y, libtcod.BKGND_NONE, str(auction.iterations))
                y += 1
        '''
        ## End print good info ##
        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        key_pressed = g.game.get_key(key)








