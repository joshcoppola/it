from __future__ import division
import random
from random import randint as roll

import libtcodpy as libtcod
import config as g


BUILDING_INFO = {
    'tomb':{'cons materials': 500},
    'bowyer':{'cons materials': 100},
    'barracks':{'cons materials': 200},
    'stable':{'cons materials': 200},
    'weaponsmith':{'cons materials': 200},
    'armorer':{'cons materials': 200},
    'hideout':{'cons materials': 30}
}


class Building:
    '''A building'''

    def __init__(self, zone, type_, template, site, construction_material, professions, inhabitants, tax_status, wx, wy, constructed=1):
        self.zone = zone
        self.template = template
        self.type_ = type_
        self.name = type_

        self.site = site
        self.construction_material = construction_material
        self.wx = wx
        self.wy = wy

        self.cost_to_build = BUILDING_INFO[self.type_] if self.type_ in BUILDING_INFO else {}

        self.linked_economy_agent = None

        self.professions = []
        self.inhabitants = []
        self.tax_staus = tax_status

        for profession in professions:
            self.add_profession(profession)

        for inhabitant in inhabitants:
            self.add_inhabitant(inhabitant)

        self.constructed = constructed

        self.current_workers = []
        self.physical_property = []

        self.housed_objects = []
        # Garrison consists of armies
        self.garrison = []

        self.captives = []


        self.add_building_to_map_func = 'will be implemented at some point'
        self.add_building_to_map_args = []

        self.set_name()


    def add_housed_object(self, obj):
        self.housed_objects.append(obj)

    def remove_housed_object(self, obj):
        self.housed_objects.remove(obj)

    def add_inhabitant(self, inhabitant):
        inhabitant.creature.house = self
        self.inhabitants.append(inhabitant)

    def remove_inhabitant(self, figure):
        figure.creature.house = None
        self.inhabitants.remove(figure)


    def add_housed_objects_to_map(self):
        ''' will be expanded later? '''
        for obj in self.housed_objects:
            self.place_within(obj)

    def place_within(self, obj):
        ## Place an object within the building
        if not self.physical_property:
            print self.get_name(), 'has no physical property!'
            return
            # Choose a tile that is not blocked
        while 1:
            x, y = random.choice(self.physical_property)
            if not g.M.tiles[x][y].blocks_mov:
                break

        g.M.add_object_to_map(x=x, y=y, obj=obj)


    def set_name(self):
        if self.type_ == 'Tavern':
            num = roll(1, 5)
            if num == 1:
                front = 'The {0} {1}'.format(random.choice(g.TAVERN_ADJECTIVES), random.choice(g.TAVERN_NOUNS))
                ending = random.choice(['', '', '', ' Inn', ' Tavern', ' Tavern', ' Lodge', ' Bar and Inn'])
            elif num == 2:
                front = 'The {0}\'s {1}'.format(random.choice(g.TAVERN_NOUNS), random.choice(g.TAVERN_OBJECTS))
                ending = ''
            elif num == 3:
                front = '{0}\'s {1}'.format(random.choice(g.TAVERN_NOUNS), random.choice(g.TAVERN_OBJECTS))
                ending = random.choice([' Inn', ' Tavern', ' Tavern', ' Lodge', ' Bar and Inn'])
            elif num == 4:
                front = '{0}\'s {1}'.format(self.site.name, random.choice(g.TAVERN_OBJECTS))
                ending = ''
            elif num == 5:
                front = 'The {0} of the {1} {2}'.format(random.choice(('Inn', 'Tavern', 'Lodge')), random.choice(g.TAVERN_ADJECTIVES), random.choice(g.TAVERN_NOUNS))
                ending = ''

            self.name = front + ending

    def get_name(self):
        return self.name

    def add_worker(self, worker):
        self.current_workers.append(worker)
        worker.creature.profession.current_work_building = self

    def remove_worker(self, worker):
        self.current_workers.remove(worker)
        worker.creature.profession.current_work_building = None

    def add_profession(self, profession):
        profession.building = self
        profession.current_work_building = self
        self.professions.append(profession)

    def fill_position(self, profession):
        # Give temples and nobles and stuff an initial dynasty to begin with
        potential_employees = [figure for figure in g.WORLD.tiles[self.site.x][self.site.y].entities if
                               figure.creature.profession is None and figure.creature.sex == 1 and figure.creature.get_age() > g.MIN_MARRIAGE_AGE]

        # Mostly try to use existing folks to fill the position
        if not profession.name in ('Assassin', ) and len(potential_employees) > 0:
            human = random.choice(potential_employees)
        # Otherwise, create a new person
        else:
            born = g.WORLD.time_cycle.years_ago(roll(18, 40))
            human = self.site.create_inhabitant(sex=1, born=born, dynasty=None, important=0, house=None)

        ## Actually give profession to the person ##
        profession.give_profession_to(human)


    def fill_initial_positions(self):
        for profession in self.professions:
            self.fill_position(profession)


    def add_building_to_map(self, *args):
        # Find an ok center point
        building_center = (roll(50, 100), roll(50, 100))
        building_size = (roll(15, 20), roll(15, 20))
        '''
        ## Make a nice rectangle, with walls at the corners
        for q in xrange(building_center[0], building_center[0] + building_size[0] + 1):
            for r in xrange(building_center[1], building_center[1] + building_size[1] + 1):
                g.M.tiles[q][r].building = self
                self.physical_property.append((q, r))
                ## Add wall or floor
                if q in [building_center[0], building_center[0] + building_size[0]] or r in [building_center[1], building_center[1] + building_size[1]]:
                    g.M.tiles[q][r].make_wall(libtcod.darkest_grey)
                else:
                    g.M.tiles[q][r].make_floor(floor_type='dirt')

        door_coords = (int(building_center[0] + (building_size[0] / 2)), building_center[1] + building_size[1])

        g.M.make_door(x=door_coords[0], y=door_coords[1], floor_type='dirt')
        '''
        bx, by = building_center[0], building_center[1]
        for i, row in enumerate(BUILDINGS[self.template]):
            for j, tile in enumerate(row):
                x, y = bx+j, by+i
                self.physical_property.append((x, y))

                if tile == '#':
                    g.M.tiles[x][y].make_wall(libtcod.darkest_grey)
                elif tile == ' ':
                    g.M.tiles[x][y].make_floor(floor_type='stone')
                elif tile in ('d', '-'):
                    g.M.make_door(x=x, y=y, floor_type='stone')


    def add_building_from_rect_lot(self, rect, building_color, floor, door_dir):

        w, h = rect.x2-rect.x1, rect.y2-rect.y1
        if (w, h) in BUILDINGS[self.type_]:

            bx, by = rect.x1, rect.y1
            template = random.choice(BUILDINGS['houses'][(w, h)])
            for i, row in enumerate(template):
                for j, tile in enumerate(row):
                    x, y = bx+j, by+i
                    self.physical_property.append((x, y))

                    if tile == '#':
                        g.M.tiles[x][y].make_wall(libtcod.darkest_sepia)
                    elif tile == ' ':
                        g.M.tiles[x][y].make_floor(floor_type='dirt')
                    elif tile in ('d', '-'):
                        g.M.make_door(x=x, y=y, floor_type='dirt')

        else:
            for x in xrange(rect.x1, rect.x2 + 1):
                for y in xrange(rect.y1, rect.y2 + 1):
                    self.physical_property.append((x, y))
                    self.usemap.tiles[x][y].building = self

                    if x in (rect.x1, rect.x2) or y in (rect.y1, rect.y2):
                        self.usemap.tiles[x][y].make_wall(building_color)
                    else:
                        self.usemap.tiles[x][y].make_floor(floor_type=floor)

    def add_physical_property_rect(self, physical_property_rect):
        for x in xrange(physical_property_rect.x1, physical_property_rect.x2 + 1):
            for y in xrange(physical_property_rect.y1, physical_property_rect.y2 + 1):
                self.physical_property.append((x, y))
                g.M.tiles[x][y].building = self


    def create_door_and_outside_road(self, rect, door_dir):
        pass








'''
b - bedroom
c - closet
d - den
D - dormitory
h - hallway
j - jail
k - kitchen
l - library
p - pantry
r = recreation
'''

BUILDINGS = {'house':{}, 'shop':{}}

BUILDINGS['TEST'] = [
'###############',
'#      #      #',
'#      #      #',
'#      #      #',
'#      #      #',
'#      #      #',
'#      #      #',
'###-######-##########',
'#             #     #',
'#             #     #',
'#             #     #',
'#             -     #',
'#             #     #',
'#             #     #',
'#             #     #',
'#             #     #',
'#             #     #',
'#################d###'
]

BUILDINGS['temple1'] = [
'##################################################',
'#             #                                  #',
'#             #                                  #',
'#             #          #           #           #',
'#             #                                  #',
'#             #                                  #',
'#             #                                  #',
'#             #          #           #        ####',
'#             #                               #',
'#             #                               #',
'#             #                               #',
'#             -          #           #        #',
'#             #                               #',
'#             #                               #',
'#             #                               #',
'#             #                               ####',
'#             #                                  #',
'###############                        ###########',
'#             #                        #         #',
'#             #                        #         #',
'#             #                        #         #',
'#             -                   ######         #',
'#             #                   #           ####',
'#             #                   -           #',
'###-####      #                   #           #',
'#      #      ################-#-########-#####',
'#      #      #          #           #        #',
'#      ###-####                               #',
'#             -          #     #     #        #',
'#             #                               #',
'#             #          #     #     #        ####',
'#             #                                  #',
'#             #          #     #     #           #',
'#             -                                  #',
'#             #          #     #     #           #',
'#             #                                  #',
'###-######-####          #     #     #        ####',
'#             #                               #',
'#             #          #     #     #        #',
'#             #                               #',
'#             -          #     #     #        #',
'#             #                               #',
'#             #          #     #     #        #',
'#             #                               #',
'#             #########                ###########',
'#             #       #                #         #',
'###############       #                #         #',
'#      #      #       #                #         #',
'#      #      #########                #         #',
'#      #      #                        #         #',
'#      #      #                   ######         #',
'#      ####-###                   #           ####',
'#      #                          -           #',
'###-####                          #           #',
'#             ############    ##d##           #',
'#             #               #   #           #',
'#             #               #   #           #',
'#             -               #   #           #',
'#             #     ###########   #############',
'#             #     #',
'#             #     #',
'#             #     #',
'#             #     #',
'#################d###'
]





BUILDINGS['house'][(6, 6)] = [
[
'#####.',
'#   ##',
'#    #',
'##-###',
'#    #',
'#    #',
'##d###'
],

[
'.####.',
'##  ##',
'#    #',
'#    #',
'#    #',
'##  ##',
'.#d##.'
],

[
'######',
'#    #',
'#    #',
'#  ###',
'#    #',
'##  ##',
'.#d##.'
]
]


BUILDINGS['house'][(7, 7)] = [
[
'#######',
'#  #  #',
'#  #  #',
'##-##-#',
'#     #',
'#     #',
'#     #',
'##d####'
],

[
'#######',
'#     #',
'#     #',
'##-####',
'#  #  #',
'#  -  #',
'#  #  #',
'##d####'
],

[
'...####',
'####  #',
'#     #',
'##-####',
'#     #',
'#     #',
'#     #',
'##d####'
]
]


BUILDINGS['house'][(8, 8)] = [
[
'########',
'#   #  #',
'#   #  #',
'##-##  #',
'#   #  #',
'#   ##-#',
'#      #',
'#      #',
'####d###'
],

[
'########',
'#   #  #',
'#   #  #',
'##-##  #',
'#   -  #',
'#  #####',
'#  -   #',
'#  #   #',
'########'
],

[
'#####...',
'#   #...',
'#   ####',
'##-##  #',
'#   -  #',
'#   ####',
'#      #',
'#      #',
'####d###'
]
]


BUILDINGS['house'][(12, 12)] = [
[
'############',
'#     #    #',
'#     -    #',
'#     ######',
'#     -    #',
'#     #    #',
'#   ########',
'##-##      #',
'#   #      #',
'#   ##-#####',
'#       #',
'#      ##',
'####d###'
],

[
'############',
'#  #       #',
'#  #       #',
'##-#       #',
'#          #',
'##-####-####',
'#   #      #',
'#####   ####',
'.#      -  #',
'.#      ####',
'.#       #',
'.#       #',
'.####d####'
],

[
'.##########.',
'.#   #    #.',
'.#   #    #.',
'.##-###-###.',
'.#        #.',
'.#     #####',
'.#     #   #',
'.####      #',
'.#         #',
'.#     #####',
'.#       #',
'.#       #',
'.####d####'
]
]






