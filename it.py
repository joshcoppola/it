#!/usr/bin/python
from __future__ import division
import libtcodpy as libtcod
import random
from random import randint as roll
import math
import textwrap
#import shelve
import time
import os
#import multiprocessing
#import cProfile as prof
#import pstats
#import pdb
import copy
from collections import Counter

import economy
import physics as phys
from traits import CULTURE_TRAIT_INFO, TRAIT_INFO, TRAITS, tdesc
from dijkstra import Dijmap
import gen_languages as lang
import gen_creatures
import religion
import gui
from floodfill import floodfill
import building_templates
#import mapfeat2 as mgen

# Code to detect screen resolution (libtcod's doesn't work for some reason?)
try:
    from ctypes import windll
    user32 = windll.user32
    SCREEN_RES = ( user32.GetSystemMetrics(0), user32.GetSystemMetrics(1) )
except:
    print 'Cannot auto-size resolution, fall back to default...'
    SCREEN_RES = (1280, 720)


#size of the battle map
MAP_WIDTH = 250
MAP_HEIGHT = 250
# Size for cities
CITY_MAP_WIDTH = 300
CITY_MAP_HEIGHT = 300

#size of the WORLD
WORLD_WIDTH = 240
WORLD_HEIGHT = 220

WATER_HEIGHT = 100
MOUNTAIN_HEIGHT = 190


FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = 1  #light walls or not
UNALERT_FOV_RADIUS = 30
ALERT_FOV_RADIUS = 60

LIMIT_FPS = 60

# Sites must be this far apart
MIN_SITE_DIST = 4

# There can be this much space between cities when starting an economy
MAX_ECONOMY_DISTANCE = 25

##### City map generating stuff
MAX_BUILDING_SIZE = 15
INITIAL_BLDG_CHK = 3 # for initial check around building radius
INTIAL_BLDG_SIZE = 5
DEVELOPED_SURFACES = set(['road', 'wall', 'floor', 'water'])


# When looping trough, these are the tree trunk characters for large (2x2) trees
TREE_CHARS = {0:(307, 308), 1:(311, 312), 2:(313, 314), 3:(309, 310) }
TREE_STUMP_CHARS = {0:315, 1:317, 2:318, 3:316 }

## colors ##
PANEL_BACK = libtcod.Color(18, 15, 15)
PANEL_FRONT = libtcod.Color(138, 115, 95)


ENERGY_FRONT = libtcod.color_lerp(PANEL_FRONT, libtcod.yellow, .6)
ENERGY_BACK = libtcod.black

PAIN_FRONT = libtcod.color_lerp(PANEL_FRONT, libtcod.red, .6)
PAIN_BACK = libtcod.color_lerp(libtcod.dark_red, libtcod.black, .6)


DIJMAP_CREATURE_DISTANCE = 10


'''
UNIT_COSTS = {'Light Cavalry': {'horses': 1, 'ores': 1},
              'Heavy Cavalry': {'horses': 1, 'ores': 2},
              'Chariots': {'horses': 1, 'woods': 1, 'ores': 1},
              'Spearmen': {'woods': 1},
              'Swordsmen': {'ores': 2},
              'Archers': {'woods': 1},
              'Supply Wagon': {'horses': 1, 'woods': 2},
              'Supply Cart': {'woods': 2}
}
'''

PROF_OPINIONS = {
    'General taxes': {'state_gov': 4, 'merchant': -4, 'city_gov': 4, 'commoner': -4},
    'Noble taxes': {'state_gov': 4, 'city_gov': 4, 'noble': -4},
    'Church taxes': {'state_gov': 4, 'city_gov': 4, 'religion': -4}
                }

PERSONAL_OPINIONS = {
    'General taxes': {'Greedy': -2, 'Charitable': 2, 'Fiscal Liberal': 4, 'Fiscal Conservative': -4},
    'Noble taxes': {'Greedy': -2, 'Charitable': 2, 'Fiscal Liberal': 4, 'Fiscal Conservative': -4},
    'Church taxes': {'Greedy': -2, 'Charitable': 2, 'Fiscal Liberal': 4, 'Fiscal Conservative': -4, 'Devout': -4,
                     'Unbeliever': 4}
                }

MIN_MARRIAGE_AGE = 16
MAX_MARRIAGE_AGE = 50
MIN_CHILDBEARING_AGE = 16
MAX_CHILDBEARING_AGE = 40

DYNASTY_SYMBOLS = (3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 17, 20, 21, 22, 30, 31, 127, 156, 157,
                   224, 228, 232, 234, 235, 237, 239, 240, 241, 242, 243, 244, 245, 247,
                   248, 253, 174, 175, 176, 220, 221, 222, 223, 227, 158, 42, 43, 32, 206,
                   197)

LIGHT_COLORS = (
                libtcod.Color(238, 233, 233), libtcod.Color(205, 201, 201), libtcod.Color(248, 248, 255),
                libtcod.Color(245, 245, 245), libtcod.Color(220, 220, 220), libtcod.Color(255, 250, 240),
                libtcod.Color(253, 245, 230), libtcod.Color(240, 240, 230), libtcod.Color(250, 235, 215),
                libtcod.Color(238, 223, 204), libtcod.Color(205, 192, 176), libtcod.Color(255, 222, 173),
                libtcod.Color(255, 228, 181), libtcod.Color(255, 248, 220), libtcod.Color(238, 232, 205),
                libtcod.Color(205, 200, 177), libtcod.Color(255, 255, 240), libtcod.Color(238, 238, 224),
                libtcod.Color(205, 205, 193), libtcod.Color(255, 250, 205), libtcod.Color(255, 245, 238),
                libtcod.Color(238, 229, 222), libtcod.Color(205, 197, 191), libtcod.Color(240, 255, 240),
                libtcod.Color(244, 238, 224), libtcod.Color(193, 205, 193), libtcod.Color(245, 255, 250),
                libtcod.Color(240, 255, 255), libtcod.Color(230, 230, 250), libtcod.Color(255, 240, 245),
                libtcod.Color(255, 228, 225), libtcod.Color(173, 216, 230), libtcod.Color(176, 224, 230),
                libtcod.Color(175, 238, 238), libtcod.Color(190, 190, 190), libtcod.Color(211, 211, 211),
                libtcod.Color(238, 160, 238), libtcod.Color(221, 175, 221)
                )

DARK_COLORS = (
               libtcod.Color(49, 79, 79), libtcod.Color(85, 85, 85), libtcod.Color(92, 118, 124),
               libtcod.Color(19, 136, 53), libtcod.Color(25, 25, 112), libtcod.Color(0, 0, 128),
               libtcod.Color(72, 61, 139), libtcod.Color(106, 90, 135), libtcod.Color(0, 0, 205),
               libtcod.Color(6, 10, 13), libtcod.Color(0, 0, 135), libtcod.Color(60, 110, 150),
               libtcod.Color(0, 106, 109), libtcod.Color(65, 108, 110), libtcod.Color(0, 100, 0),
               libtcod.Color(85, 107, 47), libtcod.Color(103, 118, 93), libtcod.Color(36, 109, 67),
               libtcod.Color(40, 109, 83), libtcod.Color(32, 108, 100),
               libtcod.Color(50, 105, 50), libtcod.Color(64, 105, 50), libtcod.Color(34, 139, 34),
               libtcod.Color(107, 142, 35), libtcod.Color(38, 125, 32), libtcod.Color(104, 74, 11),
               libtcod.Color(58, 23, 23), libtcod.Color(115, 82, 82), libtcod.Color(139, 69, 19),
               libtcod.Color(160, 82, 45), libtcod.Color(120, 113, 43),
               libtcod.Color(30, 20, 8), libtcod.Color(120, 85, 10),
               libtcod.Color(128, 34, 34), libtcod.Color(125, 42, 42),
               libtcod.Color(106, 38, 76), libtcod.Color(109, 21, 63),
               libtcod.Color(118, 43, 26), libtcod.Color(107, 95, 50)
               )

DEBUG_MSG_COLOR = libtcod.dark_red


## For individual facing information
NEIGHBORS = ( (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1) )
COMPASS = ('north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest')

STANCES = {
    'Aggressive': {'attack_bonus': 10, 'defense_bonus': -15, 'disarm_bonus': 0, 'disarm_defense': 10, 'knock_bonus': 10,
                   'knock_defense': 10},
    'Defensive': {'attack_bonus': 0, 'defense_bonus': 10, 'disarm_bonus': 0, 'disarm_defense': -5, 'knock_bonus': 0,
                  'knock_defense': -10},
    'Prone': {'attack_bonus': -20, 'defense_bonus': -20, 'disarm_bonus': -20, 'disarm_defense': -20, 'knock_bonus': -20,
                  'knock_defense': -20}
}

TAVERN_ADJECTIVES = ('Dancing', 'Grinning', 'Crimson', 'Green', 'Red', 'Blue', 'Kingly', 'Happy', 'Drowsy',
                     'Hungry', 'Thirsty', 'Ailing', 'Friendly', 'Blind', 'Drunken', 'Noble', 'Tiny',
                     'Yawning', 'Tipsy', 'Snoring', 'Salty', 'Merry', 'Black', 'White', 'Mighty',
                     'Scheming', 'Singing', 'Ancient', 'Wise', 'Weary', 'Weeping', 'Helpless', 'Firey',
                     'Wayward')

TAVERN_NOUNS = ('Gnome', 'Knave', 'Dragon', 'Giant', 'Pony', 'Hunter', 'Boar', 'Lion', 'Dog', 'Cat',
                'Frog', 'Goblin', 'Fox', 'Snake', 'Troll', 'Serpent', 'Widow', 'Soldier', 'Wolf',
                'Wizard', 'Sage', 'Jester', 'Orphan', 'Seeker', 'Trickster', 'Griffon', 'Witch',
                'Barkeep', 'Minion')

TAVERN_OBJECTS = ('Belly', 'Smile', 'Kettle', 'Stout', 'Host', 'House', 'Cave', 'Pride', 'Story',
                  'Secret', 'Castle', 'Keep', 'Helm', 'Cloak', 'Shield', 'Dagger', 'Pint', 'Bane',
                  'Triumph', 'Folly', 'Flask', 'Cask', 'Casket', 'Delight', 'Lair', 'Mug', 'Nest', 'Keg',
                  'Bride', 'Flagon', 'Eyes', 'Brew', 'Fancy', 'Barrel', 'Wisdom', 'Jewel', 'Potion',
                  'Stew', 'Stein', 'Goblet', 'Tankard', 'Tumbler', 'Pitcher', 'Gizzard')


QUESTION_RESPONSES = {
             'name':{
                     'ask': ['What is your name?'],
                     'respond':{
                                'truth':['My name is %s', '%s'],
                                'no answer':['I don\'t want to answer that.']
                                }
                     },

             'profession':{
                     'ask': ['What do you do?'],
                     'respond':{
                                'truth':['I am a %s'],
                                'no answer':['I don\'t want to answer that.']
                                }
                     },

             'age':{
                     'ask': ['How old are you?'],
                     'respond':{
                                'truth':['I am %s', '%s'],
                                'no answer':['I don\'t want to answer that.']
                                }
                     },

             'city':{
                     'ask': ['From where do you hail?'],
                     'respond':{
                                'truth':['I currently live in %s'],
                                'no answer':['I don\'t want to answer that.']
                                }
                     },

             'goals':{
                     'ask': ['What are your current goals?'],
                     'respond':{
                                'truth':['I am currently %s'],
                                'no answer':['I don\'t want to answer that.']
                                }
                     },

             'recruit':{
                     'ask': ['Will you join me on my quest?'],
                     'respond':{
                                'yes':['I will gladly join you'],
                                'no':['No.']
                                }
                     }
}

CONVERSATION_QUESTIONS= {
                            'greet':'Hello.',
                            'name':'What is your name?',
                            'profession':'What do you do?',
                            'age':'How old are you?,',
                            'city':'From where do you hail?',
                            'goals':'What are your current goals?',
                            'recruit':'Will you join me on my quest?'}

CONVERSATION_TOPICS = ['the weather', 'religion', 'travel', 'current events',
               'politics', 'family', 'life stories', 'the economy']


civ_colors = (
              libtcod.Color(18, 113, 113), libtcod.Color(125, 72, 72), libtcod.Color(64, 64, 89),
              libtcod.Color(112, 138, 144), libtcod.Color(49, 79, 79), libtcod.Color(178, 34, 34),
              libtcod.Color(72, 61, 139), libtcod.Color(25, 25, 112), libtcod.Color(0, 0, 128),
              libtcod.Color(132, 112, 165), libtcod.Color(72, 61, 139), libtcod.Color(106, 90, 155),
              libtcod.Color(105, 136, 130), libtcod.Color(30, 144, 165), libtcod.Color(5, 5, 125),
              libtcod.Color(0, 106, 109), libtcod.Color(103, 156, 30), libtcod.Color(70, 130, 50),
              libtcod.Color(102, 155, 170), libtcod.Color(75, 128, 130), libtcod.Color(52, 139, 134),
              libtcod.Color(50, 155, 50), libtcod.Color(22, 148, 140), libtcod.Color(127, 165, 162),
              libtcod.Color(105, 105, 0), libtcod.Color(168, 165, 32), libtcod.Color(165, 165, 0),
              libtcod.Color(165, 69, 0), libtcod.Color(160, 108, 108), libtcod.Color(165, 127, 80),
              libtcod.Color(160, 32, 190), libtcod.Color(96, 121, 106), libtcod.Color(147, 112, 169),
              libtcod.Color(136, 28, 66), libtcod.Color(169, 112, 147), libtcod.Color(95, 122, 103),
              libtcod.Color(101, 120, 101), libtcod.Color(18, 90, 128), libtcod.Color(109, 11, 63),
              libtcod.Color(113, 40, 113)
              )

MCFG = {
           'tundra':{
                     'initial_blocks_mov_chance':100,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':1,
                     'small_stump_chance':1,
                     'large_tree_chance':1,
                     'large_stump_chance':1,
                     'shrub_chance':10,
                     'unique_ground_tiles':(()),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'taiga':{
                    'initial_blocks_mov_chance':200,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':10,
                     'small_stump_chance':10,
                     'large_tree_chance':1,
                     'large_stump_chance':1,
                     'shrub_chance':15,
                     'unique_ground_tiles':((293, 4), (294, 4)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'temperate forest':{
                    'initial_blocks_mov_chance':400,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     #'base_color':(233,221,209),
                     'base_color':(82, 61, 56),
                     'small_tree_chance':8,
                     'small_stump_chance':6,
                     'large_tree_chance':10,
                     'large_stump_chance':2,
                     'shrub_chance':85,
                     'unique_ground_tiles':((293, 8), (294, 8)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'temperate steppe':{
                    'initial_blocks_mov_chance':450,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':5,
                     'small_stump_chance':1,
                     'large_tree_chance':1,
                     'large_stump_chance':1,
                     'shrub_chance':10,
                     'unique_ground_tiles':((293, 4), (294, 4)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'rain forest':{
                    'initial_blocks_mov_chance':400,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     #'base_color':(182, 161, 156),
                     'base_color':(82, 61, 56),
                     'small_tree_chance':20,
                     'small_stump_chance':10,
                     'large_tree_chance':15,
                     'large_stump_chance':5,
                     'shrub_chance':100,
                     'unique_ground_tiles':((293, 9), (294, 9)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'tree savanna':{
                    'initial_blocks_mov_chance':450,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':(159, 139, 76),
                     'small_tree_chance':5,
                     'small_stump_chance':2,
                     'large_tree_chance':10,
                     'large_stump_chance':2,
                     'shrub_chance':15,
                     'unique_ground_tiles':((293, 8), (294, 8)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'grass savanna':{
                    'initial_blocks_mov_chance':300,
                     'repetitions':3,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':5,
                     'small_stump_chance':3,
                     'large_tree_chance':1,
                     'large_stump_chance':1,
                     'shrub_chance':20,
                     'unique_ground_tiles':((293, 1), (294, 1)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'dry steppe':{
                    'initial_blocks_mov_chance':400,
                     'repetitions':1,
                     'walls_to_floor':4,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':5,
                     'small_stump_chance':10,
                     'large_tree_chance':1,
                     'large_stump_chance':5,
                     'shrub_chance':10,
                     'unique_ground_tiles':((293, 5), (294, 5)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'semi-arid desert':{
                    'initial_blocks_mov_chance':300,
                     'repetitions':1,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':0,
                     'small_stump_chance':1,
                     'large_tree_chance':0,
                     'large_stump_chance':1,
                     'shrub_chance':5,
                     'unique_ground_tiles':((293, 1), (294, 1)),
                     'map_pad':0,
                     'map_pad_type':0
                     },

           'arid desert':{
                    'initial_blocks_mov_chance':300,
                     'repetitions':1,
                     'walls_to_floor':3,
                     'walls_to_wall':5,
                     'blocks_mov_color':libtcod.darker_grey,
                     'blocks_mov_surface':'rocky outcrop',
                     'shade':1,
                     'blocks_mov_height':189,

                     'base_color':'use_world_map',
                     'small_tree_chance':0,
                     'small_stump_chance':1,
                     'large_tree_chance':0,
                     'large_stump_chance':0,
                     'shrub_chance':2,
                     'unique_ground_tiles':(),
                     'map_pad':0,
                     'map_pad_type':0
                     }
           }


mouse = libtcod.Mouse()
key = libtcod.Key()


WORLD = None
player = None
M = None
time_cycle = None
camera = None

# from http://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
int2ord = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def join_list(string_list):
    if len(string_list) == 1:
        return string_list[0]
    elif len(string_list) == 2:
        return ' and '.join(string_list)
    else:
        #return ', '.join([s for s in string_list]) + ', and ', string_list[-1]
        return '{0}, and {1}'.format(', '.join([s for s in string_list]), string_list[-1])



def cart2card(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    distance = math.sqrt(dx ** 2 + dy ** 2)
    #normalize it to length 1 (preserving direction), then round it and
    #convert to integer
    dx = int(round(dx / distance))
    dy = int(round(dy / distance))

    return COMPASS[NEIGHBORS.index((dx, dy))]


def get_distance_to(x, y, target_x, target_y):
    #return the distance to another object
    dx = target_x - x
    dy = target_y - y
    return math.sqrt(dx ** 2 + dy ** 2)


def looped_increment(initial_num, max_num, increment_amt):
    incremented_num = initial_num + increment_amt
    if incremented_num > max_num:
        incremented_num = 0
    elif incremented_num < 0:
        incremented_num = max_num

    return incremented_num

def get_border_tiles(x, y):
    return ( (x, y+1), (x+1, y), (x, y-1), (x-1, y) )

def libtcod_path_to_list(path_map):
    ''' get a libtcod path into a list '''
    path = []
    while not libtcod.path_is_empty(path_map):
        x, y = libtcod.path_walk(path_map, True)
        path.append((x, y))

    return path


def in_circle(center_x, center_y, radius, x, y):
    square_dist = (center_x - x) ** 2 + (center_y - y) ** 2
    return square_dist <= radius ** 2

def is_circle_radius(center_x, center_y, radius, x, y):
    square_dist = (center_x - x) ** 2 + (center_y - y) ** 2
    return square_dist == radius ** 2


def weighted_choice(choices):
    ''' Taken from http://stackoverflow.com/questions/3679694/a-weighted-version-of-random-choice '''
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w
    assert False, "Weighted choice: shouldn't get here"


class Region:
    #a Region of the map and its properties
    def __init__(self, region, x, y, color, blocks_mov, char=' ', char_color=libtcod.black, blocks_vis=None):
        self.region = region
        self.x = x
        self.y = y
        self.color = color
        self.char = char
        self.char_color = char_color

        self.blocks_mov = blocks_mov
        self.blocks_vis = blocks_vis

        self.res = {}
        self.entities = []
        self.populations = []

        self.features = []
        self.minor_sites = []
        self.caves = []

        self.height = 0
        self.temp = 0
        # self.rainfall = 0
        # old variables, hopefully to be removed!
        self.wdist = None
        self.moist = None

        self.culture = None
        self.site = None
        self.territory = None
        self.explored = False

    def has_feature(self, feature_type):
        ''' Check if certain feature is in region '''
        for feature in self.features:
            if feature.site_type == feature_type:
                return 1

        return 0

    def get_features(self, feature_type):
        ''' Returns a list of all features, so that one may get, say, all caves in the region '''
        feature_list = []
        for feature in self.features:
            if feature.site_type == feature_type:
                feature_list.append(feature)

        return feature_list

    def get_base_color(self):
        # Give the map a base color
        base_rgb_color = MCFG[self.region]['base_color']
        if base_rgb_color == 'use_world_map':
            base_color = self.color
        else:
            base_color = libtcod.Color(*base_rgb_color)

        return base_color

    def add_minor_site(self, world, site_type, x, y, char, name, color, culture, faction):
        site = Site(world, site_type, x, y, char, name, color, culture, faction)
        self.minor_sites.append(site)

        return site

    def get_location_description(self):
        if self.site:
            return self.site.name
        elif len(self.minor_sites) or len(self.caves):
            site_names = [site.name for site in self.minor_sites + self.caves]
            return join_list(site_names)
        else:
            city, dist = WORLD.get_closest_city(self.x, self.y)
            if 0 < dist <= 3:
                return 'to the {0}s just to the {1} of {2}'.format(self.region, cart2card(city.x, city.y, self.x, self.y), city.name)
            elif dist <= 15:
                return 'to the {0}s to the {1} of {2}'.format(self.region, cart2card(city.x, city.y, self.x, self.y), city.name)
            elif dist > 15:
                return 'to the {0}s far to the {1} of {2}'.format(self.region, cart2card(city.x, city.y, self.x, self.y), city.name)
            elif dist > 30:
                return 'to the {0}s far, far to the {1} of {2}'.format(self.region, cart2card(city.x, city.y, self.x, self.y), city.name)
            else:
                return 'the unknown {0}s'.format(self.region)

class Tile:
    #a tile of the map and its properties
    def __init__(self, blocks_mov, blocks_vis=None):

        # To be set at a later time
        self.color = None
        self.shadow_color = None

        self.char = ' '
        self.char_color = None
        self.shadow_char_color = None
        ## Noise for shading/texturing the map...
        self.noise = None

        self.blocks_mov = blocks_mov
        #by default, if a tile is blocked, it also blocks sight
        if blocks_vis is None:  self.blocks_vis = blocks_mov
        else:                    self.blocks_vis = blocks_vis

        #all tiles start unexplored
        self.explored = True
        #All tiles start as earth
        self.zone = None
        self.surface = 'ground'
        self.building = None
        self.height = 0

        #Objects on the current map tile
        self.objects = []

        # Info regarding interaction
        self.interactable = 0

        # For flood filling, if you want to mark that a tile is passed but not do anything
        self.tmp_flag = 0


    def set_height(self, height):
        self.height = height

    def set_noise(self, noise):
        ''' Noise is stored here in case the tile needs to be colored a different color,
        and wants to blend in with the underlying layer. Will be updated eventually... '''
        self.noise = noise

    def set_char(self, char):
        self.char = char

    def set_color(self, color):
        ''' Change the color of the tile, and the associated shadow variable '''
        self.color = color
        #self.shadow_color = color * .5
        self.shadow_color = color * .85

    def set_char_color(self, color):
        self.char_color = color
        self.shadow_char_color = color * .5


    def colorize(self, color):
        scale = 8
        ncolor = int((self.noise+1) * scale)
        #self.set_color(libtcod.Color(self.height, self.height, self.height))
        self.set_color(color + libtcod.Color(ncolor, ncolor, ncolor) )


    def set_shadow(self, amount):
        shaded_color = libtcod.color_lerp(self.color, libtcod.black, amount)

        self.colorize(color=shaded_color)


    def make_road(self, rtype='paved'):
        # Turn tile into a road
        self.blocks_mov = 0
        self.blocks_vis = 0

        self.surface = 'road'
        self.zone = 'road'
        if rtype == 'paved':
            self.colorize(libtcod.darker_grey + libtcod.Color(roll(1, 4), roll(1, 4), roll(1, 4)) )
        # Or a dirt road
        elif rtype == 'dirt':
            self.colorize(libtcod.dark_sepia + libtcod.Color(roll(1, 4), roll(1, 4), roll(1, 4)) )

    def make_floor(self, floor_type='dirt'):
        # Turn tile into a floor
        self.surface = 'floor'
        self.blocks_mov = 0
        self.blocks_vis = 0
        if floor_type == 'dirt':
            self.colorize(libtcod.dark_sepia)
        elif floor_type == 'stone':
            self.colorize(libtcod.darker_grey)

    def make_wall(self, color):
        # Turn tile into a wall
        self.surface = 'wall'
        self.set_color(color=color + libtcod.Color(roll(1, 5), roll(1, 5), roll(1, 5)) )
        self.blocks_mov = 1
        self.blocks_vis = 1

    def make_rock(self, color=libtcod.darkest_grey):
        self.surface = 'rock'
        self.set_color(color=color)
        self.blocks_mov = 1
        self.blocks_vis = 1

    def make_water(self):
        self.blocks_mov = 1
        self.blocks_vis = 0

        self.surface = 'water'
        self.set_color(libtcod.color_lerp(self.color, libtcod.dark_blue, .5))


class Wmap:
    def __init__(self, world, wx, wy, height, width):
        # A walkable map, composed of an array of tiles
        self.world = world
        self.wx = wx
        self.wy = wy

        self.height = height
        self.width = width

        self.tiles = []
        # List of all objects inhabiting this map
        self.objects = []
        self.creatures = []
        self.sapients = []

        # Key:Value pair, where keys = faction and value = set of all members of that faction on the map
        self.factions_on_map = {}

        self.dijmaps = {}

        ## Pathfinding map and binary fov recompute toggle
        self.fov_map = libtcod.map_new(self.width, self.height)
        self.path_map = None
        self.fov_recompute = True

        #self.rock_border_cells = []


    def cache_factions_for_dmap(self):
        ''' Run when map is created, so it understands the various factions present '''
        self.factions_on_map = {}
        for obj in self.sapients:
            if obj.sapient.faction in self.factions_on_map.keys():
                self.factions_on_map[obj.sapient.faction].add(obj)
            else:
                self.factions_on_map[obj.sapient.faction] = set([obj])

        # Now add a dmap for each
        for faction, member_set in self.factions_on_map.iteritems():
            self.add_dmap(key=faction.faction_name, target_nodes=[(obj.x, obj.y) for obj in member_set], dmrange=DIJMAP_CREATURE_DISTANCE)

            # Make sure all sapients know who their enemies are
            for enemy_faction in faction.enemy_factions:
                if enemy_faction in self.factions_on_map.keys():
                    game.add_message('%s: setting enemy - %s'%(faction.faction_name, enemy_faction.faction_name), libtcod.color_lerp(faction.color, PANEL_FRONT, .5) )
                    for obj in member_set:
                        obj.sapient.add_enemy_faction(enemy_faction)

        for figure in self.sapients:
            if figure.local_brain:
                figure.local_brain.set_enemy_perceptions_from_cached_factions()


    def update_dmaps(self):
        #jobs = []
        #def stupid_function(target_nodes):
        #    self.dijmaps[faction.faction_name].update_map(target_nodes)

        for faction, member_set in self.factions_on_map.iteritems():
            target_nodes = [(obj.x, obj.y) for obj in member_set if obj.creature.status == 'alive' and (obj == player or (obj != player and obj.local_brain.ai_state != 'idle'))]
            self.dijmaps[faction.faction_name].update_map(target_nodes=target_nodes)
            #update_map_test(self.dijmaps[faction.faction_name], target_nodes)

            #j = multiprocessing.Process(target=self.dijmaps[faction.faction_name].update_map, args=(target_nodes))
            #j = multiprocessing.Process(target=self.dijmaps[faction.faction_name].update_map, args=(target_nodes))
            #j = multiprocessing.Process(target=game.add_message, args=(faction.faction_name,))
            #j = multiprocessing.Process(target=update_map_test, args=(self.dijmaps[faction.faction_name], target_nodes))

            #jobs.append(j)
            #j.start()
            #j.join()



    def set_initial_dmaps(self):
        ''' A few dijmaps will be universal to all maps '''
        self.add_dmap(key='map_center', target_nodes=[ (int(self.width/2), int(self.height/2)) ], dmrange=5000)

    def add_dmap(self, key, target_nodes, dmrange):
        ''' Add additional dmaps as needed '''
        begin = time.time()
        self.dijmaps[key] = Dijmap(sourcemap=self, target_nodes=target_nodes, dmrange=dmrange)
        end = time.time() - begin

        game.add_message('Dmap for %s created in %.2f seconds' %(key, end), libtcod.cyan)


    def get_astar_distance_to(self, x, y, target_x, target_y):
        libtcod.path_compute(self.path_map, x, y, target_x, target_y)
        new_path_len = libtcod.path_size(self.path_map)

        return new_path_len

    def tile_blocks_mov(self, x, y):
        ''' Check whether a map tile is impassable '''
        if self.tiles[x][y].blocks_mov:
            return 1
        else:
            for obj in self.tiles[x][y].objects:
                if obj.blocks_mov:
                    return 1
            return 0

    def tile_blocks_sight(self, x, y):
        ''' Check whether a map tile is impassable '''
        if self.tiles[x][y].blocks_vis:
            return 1
        else:
            for obj in self.tiles[x][y].objects:
                if obj.blocks_vis:
                    return 1
            return 0


    def create_and_vary_heightmap(self, initial_height, mborder, minr, maxr, minh, maxh, iterations):
        hm = libtcod.heightmap_new(w=self.width, h=self.height)

        # Set initial heightmap values
        for x in xrange(self.width):
            for y in xrange(self.height):
                # Set the default value
                libtcod.heightmap_set_value(hm=hm, x=x, y=y, value=initial_height)


        #### RANDOM HILLS ####
        for i in xrange(iterations):
            x, y = roll(mborder, self.width-1-mborder), roll(mborder, self.height-1-mborder)
            radius = roll(minr, maxr)
            height = roll(minh, maxh)

            # Prevent height from going above 190 for now :S
            if libtcod.heightmap_get_value(hm=hm, x=x, y=y) < (MOUNTAIN_HEIGHT - height - 1):
                libtcod.heightmap_add_hill(hm=hm, x=x, y=y, radius=radius, height=height)

        return hm


    def create_heightmap_from_surrounding_tiles(self, minh=-8, maxh=8, iterations=50):
        ## Create initial tiles
        #self.tiles = [[Tile(blocks_mov=False)
        #              for y in xrange(self.height)]
        #             for x in xrange(self.width)]

        hht = int(self.height/2)
        hwd = int(self.width/2)


        surrounding_heights = WORLD.get_surrounding_heights(coords=(self.wx, self.wy))
        this_tile_height = min(surrounding_heights[4], MOUNTAIN_HEIGHT-10)

        # Which map tiles to use from surrounding_heights variable
        surrounding_heights_to_map = (
                                      (0, 0),             (hwd, 0),             (self.width-1, 0),
                                      (0, hht),           (hwd, hht),           (self.width-1, hht),
                                      (0, self.height-1), (hwd, self.height-1), (self.width-1, self.height-1)
                                      )

        surrounding_rivers = WORLD.get_surrounding_rivers(coords=(self.wx, self.wy))

        # Which map tiles to use from the river_dirs variable
        world_to_wmap_rivers =  {
                                (1, 0):(self.width-1, int(self.height/2.5)),
                                (-1, 0):(0, int(self.height/2.5)),
                                (0, 1):(int(self.width/2.5), self.height-1),
                                (0, -1):(int(self.width/2.5), 0)
                                }


        ## Create the actual heightmap
        hm = self.create_and_vary_heightmap(initial_height=this_tile_height, mborder=int(self.width/10),
                                            minr=20, maxr=int(self.width/3), minh=minh, maxh=maxh, iterations=iterations)


        corner_tile_indices = set([0, 2, 6, 8])
        # Surrounding tiles influence map height
        for i, h in enumerate(surrounding_heights):
            x, y = surrounding_heights_to_map[i]
            height = h - this_tile_height

            ## HOW FAR THE SURROUNDING REGIONS' HEIGHTS INVADE THIS ONE
            if i in corner_tile_indices:
                radius = roll(60, 75) # bigger radius on map border
            elif i == 4:
                # Awkwardly skip this tile (since the map was already initialized with this in mind
                pass
            else:
                radius = roll(45, 60)

            libtcod.heightmap_add_hill(hm=hm, x=x, y=y, radius=radius, height=height)

        #libtcod.heightmap_rain_erosion(hm, nbDrops=int((self.width * self.height)/2), erosionCoef=.05, sedimentationCoef=.05, rnd=0)

        ######## RIVERS ##############
        if len(surrounding_rivers) >= 2:
            r1x, r1y = world_to_wmap_rivers[surrounding_rivers[0]]
            r2x, r2y = world_to_wmap_rivers[surrounding_rivers[1]]

            r1ox = roll(30, self.width-31)
            r2ox = roll(30, self.width-31)

            r1oy = roll(30, self.height-31)
            r2oy = roll(30, self.height-31)

            ### TODO -- X AND Y ARE FLIPPED AND I HAVE NO IDEA WHY
            libtcod.heightmap_dig_bezier(hm=hm, px=(r1y, r1oy, r2oy, r2y), py=(r1x, r1ox, r2ox, r2x), startRadius=5, startDepth=0, endRadius=5, endDepth=0)
            #game.add_message('height is %i'%libtcod.heightmap_get_value(hm, r1x, r1y), libtcod.red)
        ######################################################################

        return hm


    def create_map_tiles(self, hm, base_color, explored):
        self.tiles = []

        noisemap = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)
        octaves = 10
        div_amt = 50

        #1576
        # Loop through everything and create tiles
        for y in xrange(self.height):
            # Make an empty list of tile rows
            row = []
            for x in xrange(self.width):
                # Anything outside this range will be unwalkable
                if (0 < x < self.width - 1) and (0 < y < self.height - 1):      tile = Tile(blocks_mov=False)
                else:                                                           tile = Tile(blocks_mov=True)

                tile.explored = explored

                tile.set_height(int(libtcod.heightmap_get_value(hm=hm, x=x, y=y)))
                # Noise to map color
                noise_mod = libtcod.noise_get_fbm(noisemap, (x / div_amt, y / div_amt), octaves, libtcod.NOISE_SIMPLEX)
                tile.set_noise(noise_mod)
                tile.colorize(color=base_color)

                # Sand/silt/dirt around water
                if tile.height < 101:
                    tile.colorize(color=libtcod.dark_sepia)
                # Interp colors for smoother colorizing
                elif tile.height < 102:
                    tile.colorize(color=libtcod.color_lerp(libtcod.dark_sepia, base_color, .25))
                # Water
                if tile.height < WATER_HEIGHT:
                    tile.make_water()

                # Add the tile to the row
                row.append(tile)

            # Finally, add the row to the map
            self.tiles.append(row)


    def add_minor_sites_to_map(self):
        for site in self.world.tiles[self.wx][self.wy].minor_sites:
            for building in site.buildings:
                if not building.physical_property:
                    building.add_building_to_map(*building.add_building_to_map_args)


    def is_val_xy(self, coords):
        return (0 < coords[0] < self.width) and (0 < coords[1] < self.height)

    def make_city_map(self, city_class, num_nodes, min_dist, disorg):
        #Make a city on this tile
        self.cit = CityMap(self, city_class)
        self.cit.generate_city_map(num_nodes=num_nodes, min_dist=min_dist, disorg=disorg)


    def make_door(self, x, y, floor_type):
        self.tiles[x][y].make_floor(floor_type=floor_type)
        self.create_and_add_object(name='door', x=x, y=y)


    def create_and_add_object(self, name, x, y, creature=None, sapient=None, local_brain=None, world_brain=None, force_material=None):
        # Add an object to a tile
        obj = assemble_object(object_blueprint=phys.object_dict[name], creature=creature, sapient=sapient, local_brain=local_brain, world_brain=world_brain, force_material=force_material, wx=self.wx, wy=self.wy)

        # Check to see if the obj blocks movement
        if not obj.creature and (obj.blocks_mov or obj.blocks_vis):
            self.tiles[x][y].blocks_mov = obj.blocks_mov
            self.tiles[x][y].blocks_vis = obj.blocks_vis

        self.add_object_to_map(x=x, y=y, obj=obj)

        return obj

    def add_object_to_map(self, x, y, obj):
        ''' For adding an existing object to the map '''

        self.tiles[x][y].objects.append(obj)

        if obj.sapient:
            self.sapients.append(obj)
            obj.creature.next_tick = time_cycle.current_tick + 1
        elif obj.creature:
            self.creatures.append(obj)
            obj.creature.next_tick = time_cycle.current_tick + 1
        else:
            self.objects.append(obj)

        obj.x = x
        obj.y = y

        if obj.local_brain:
            obj.local_brain.ai_initialize()


    def add_sapients_from_world(self):
        hht = int(self.height/2)
        hwd = int(self.width/2)
        # Size of rectangle
        rs = 25

        world_last_dir_to_rect = {(-1, -1):Rect(x=1, y=1, w=rs, h=rs),                 (0, -1):Rect(x=hwd, y=1, w=rs, h=rs),                 (1, -1):Rect(x=self.width-(rs+2), y=1, w=rs, h=rs),
                            (-1, 0):Rect(x=1, y=hht, w=rs, h=rs),                (0, 0):Rect(x=hwd, y=hht, w=rs*3, h=rs*3),            (1, 0):Rect(x=self.width-(rs+2), y=hht, w=rs, h=rs),
                            (-1, 1):Rect(x=1, y=self.height-(rs+2), w=rs, h=rs), (0, 1):Rect(x=hwd, y=self.height-(rs+2), w=rs, h=rs), (1, 1):Rect(x=self.width-(rs+2), y=self.height-(rs+2), w=rs, h=rs)
                            }


        for entity in WORLD.tiles[self.wx][self.wy].entities:
            figure_start = world_last_dir_to_rect[entity.world_last_dir]
            # Find a non-blocked tile
            while 1:
                x = roll(figure_start.x1, figure_start.x2)
                y=roll(figure_start.y1, figure_start.y2)
                if M.is_val_xy(coords=(x, y)) and not M.tile_blocks_mov(x, y):
                    break
            # Add the entity to the map
            M.add_object_to_map(x=x, y=y, obj=entity)

        for population in WORLD.tiles[self.wx][self.wy].populations:
            population_start = world_last_dir_to_rect[population.world_last_dir]
            population.add_to_map(startrect=population_start, startbuilding=None, patrol_locations=[])

        ## DIJMAPS
        self.cache_factions_for_dmap()

        for obj in self.sapients:
            obj.creature.set_initial_desires()

        game.add_message('%i objs; %i saps' %(len(self.objects), len(self.sapients)) )

        self.initialize_fov()


    def clear_objects(self):
        for sap in self.sapients:
            sap.x = None
            sap.y = None

        self.objects = []
        self.sapients = []

    def initialize_fov(self):
        #create the FOV map, according to the generated map
        for y in xrange(self.width):
            for x in xrange(self.height):
                libtcod.map_set_properties(self.fov_map, x, y, not self.tiles[x][y].blocks_vis, not self.tiles[x][y].blocks_mov)

        for obj in self.objects + self.creatures + self.sapients:
            libtcod.map_set_properties(self.fov_map, obj.x, obj.y, not obj.blocks_vis, not obj.blocks_mov)
        self.path_map = libtcod.path_new_using_map(self.fov_map)

        map_con.clear() # unexplored areas start black (which is the default background color)


    def display(self, debug_active_unit_dijmap):
        #recompute FOV if needed (the player moved or something)
        self.fov_recompute = False
        libtcod.map_compute_fov(self.fov_map, player.x, player.y, player.creature.alert_sight_radius, FOV_LIGHT_WALLS, FOV_ALGO)
        libtcod.console_clear(map_con.con)

        # NORMAL RENDERING
        if not debug_active_unit_dijmap:
            #go through all tiles, and set their background color according to the FOV
            for cam_y in xrange(camera.height):
                for cam_x in xrange(camera.width):
                    ## TODO - which way is more efficient?
                    #(map_x, map_y) = (camera.x + x, camera.y + y)
                    (x, y) = camera.cam2map(cam_x, cam_y)
                    if self.is_val_xy((x, y)):
                        visible = libtcod.map_is_in_fov(self.fov_map, x, y)

                        if visible:
                            #libtcod.console_set_char_background(con.con, x, y, M.tiles[map_x][map_y].color, libtcod.BKGND_SET)
                            libtcod.console_put_char_ex(map_con.con, cam_x, cam_y, self.tiles[x][y].char, self.tiles[x][y].char_color, self.tiles[x][y].color)
                            #since it's visible, explore it
                            self.tiles[x][y].explored = True

                        elif self.tiles[x][y].explored:
                            #if it's not visible right now, the player can only see it if it's explored
                            #libtcod.console_set_char_background(con.con, x, y, M.tiles[map_x][map_y].color * .5, libtcod.BKGND_SET)
                            libtcod.console_put_char_ex(map_con.con, cam_x, cam_y, self.tiles[x][y].char, self.tiles[x][y].shadow_char_color, self.tiles[x][y].shadow_color)


        ## UNOPTIMIZED DIJMAP RENDERING
        elif debug_active_unit_dijmap:
            for cam_y in xrange(camera.height):
                for cam_x in xrange(camera.width):
                    #(map_x, map_y) = (camera.x + x, camera.y + y)
                    (x, y) = camera.cam2map(cam_x, cam_y)
                    if self.is_val_xy((x, y)):
                        if not self.tiles[x][y].blocks_mov:
                            intensity = 0
                            # Sum all desires for this square, weighted by intensity
                            for desire, value in render_handler.debug_active_unit_dijmap.creature.dijmap_desires.iteritems():
                                intensity += int(round(value)) * self.dijmaps[desire].dmap[x][y]

                            libtcod.console_set_char_background(map_con.con, cam_x, cam_y, libtcod.Color((255 - intensity), (255 - intensity), (255 - intensity)), libtcod.BKGND_SET)
                            #libtcod.console_set_char_background(con.con, x, y, libtcod.Color((255 - intensity), (255 - intensity), (255 - intensity)), libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(map_con.con, cam_x, cam_y, libtcod.darkest_red, libtcod.BKGND_SET)
        #########################################


        #draw all objects in the list, except the player.
        for obj in self.objects:
            if self.tiles[obj.x][obj.y].explored:
                obj.draw()

        for creature in self.creatures:
            if self.tiles[creature.x][creature.y].explored:
                creature.draw()

        for sapient in self.sapients:
            if self.tiles[sapient.x][sapient.y].explored and sapient != player:
                sapient.draw()
        player.draw()

        #blit the contents of map_con to the root console
        map_con.blit()

    def make_small_tree(self, x, y):
        ''' Make a small tree xtrunk '''
        self.tiles[x][y].surface = 'Tree trunk'
        self.tiles[x][y].blocks_mov = 1
        #self.tiles[x][y].blocks_vis = 1

        #self.tiles[x][y].set_color(libtcod.darkest_sepia)
        self.tiles[x][y].char = random.choice((288, 289))
        self.tiles[x][y].set_char_color(libtcod.darkest_sepia)


        ## Experimental shadow code
        '''
        sx, sy = x, y
        for i in xrange(3):
            sx += 1
            if self.is_val_xy((sx, sy)):
                self.tiles[sx][sy].set_shadow(amount=.5)

        for xx in xrange(sx-4, sx+5):
            for yy in xrange(sy-4, sy+5):
                if self.is_val_xy((xx, yy)):
                    amount = random.choice((0, .05, .1, .15))
                    self.tiles[xx][yy].set_shadow(amount=amount)
        '''

    def make_small_stump(self, x, y):
        ''' Make a small tree stump '''
        self.tiles[x][y].surface = 'Tree stump'
        self.tiles[x][y].blocks_mov = 1

        self.tiles[x][y].char = 290
        self.tiles[x][y].set_char_color(libtcod.darkest_sepia)

    def make_large_tree(self, x, y):
        ''' Make a large tree trunk '''
        # First check whether it's a valid location
        for i, (xx, yy) in enumerate( ( (x, y), (x, y+1), (x+1, y+1), (x+1, y) ) ):
            if self.tiles[xx][yy].blocks_mov or self.tiles[xx][yy].surface != 'ground':
                return

        # Next add the tree
        for i, (xx, yy) in enumerate( ( (x, y), (x, y+1), (x+1, y+1), (x+1, y) ) ):
            #self.tiles[xx][yy].set_color(libtcod.darkest_sepia)
            #self.tiles[xx][yy].set_shadow(amount=.2)
            self.tiles[xx][yy].char = random.choice(TREE_CHARS[i])
            self.tiles[xx][yy].set_char_color(libtcod.darkest_sepia)
            self.tiles[xx][yy].surface = 'Tree trunk'
            self.tiles[xx][yy].blocks_mov = 1
            #self.tiles[xx][yy].blocks_vis = 1


    def make_large_stump(self, x, y):
        ''' Make a large tree trunk '''
        # First check whether it's a valid location
        for i, (xx, yy) in enumerate( ( (x, y), (x, y+1), (x+1, y+1), (x+1, y) ) ):
            if self.tiles[xx][yy].blocks_mov or self.tiles[xx][yy].surface != 'ground':
                return

        # Next add the tree
        for i, (xx, yy) in enumerate( ( (x, y), (x, y+1), (x+1, y+1), (x+1, y) ) ):
            #self.tiles[xx][yy].set_color(libtcod.darkest_sepia)
            #self.tiles[xx][yy].set_shadow(amount=.2)
            self.tiles[xx][yy].char = TREE_STUMP_CHARS[i]
            self.tiles[xx][yy].set_char_color(libtcod.darkest_sepia)
            self.tiles[xx][yy].surface = 'Tree stump'
            self.tiles[xx][yy].blocks_mov = 1
            #self.tiles[xx][yy].blocks_vis = 1

    def make_shrub(self, x, y):
        self.tiles[x][y].set_char_color(libtcod.Color(49, 120, 36))
        self.tiles[x][y].char = random.choice((304, 305, 306))

    def make_ground_tile(self, x, y, char):
        self.tiles[x][y].set_char_color(libtcod.darkest_sepia)
        self.tiles[x][y].char = char

    def add_vegetation(self, cfg):
        ''' Add some vegetation to the map - should eventually vary by biome type '''
        begin = time.time()
        # Loop through entire map
        for x in xrange(self.width - 2):
            for y in xrange(self.height - 2):
                if not self.tile_blocks_mov(x, y) and self.tiles[x][y].surface == 'ground' and self.tiles[x][y].zone in (None, 'wilderness'):
                    # Not using actual "Tree" object for now; make it part of the terrain (less objects to track)
                    if roll(1, 1000) <= cfg['small_tree_chance']:
                        self.make_small_tree(x, y)

                    elif roll(1, 1000) <= cfg['small_stump_chance']:
                        self.make_small_stump(x, y)

                    elif roll(1, 1000) <= cfg['large_tree_chance']:
                        self.make_large_tree(x, y)

                    elif roll(1, 1000) <= cfg['large_stump_chance']:
                        self.make_large_stump(x, y)

                    elif roll(1, 1000) <= cfg['shrub_chance']:
                        self.make_shrub(x, y)

                    # animal remains test
                    #elif roll(1, 1000) <= 10:
                    #    self.tiles[x][y].set_char_color(libtcod.light_grey)
                    #    self.tiles[x][y].char = 255 + 16

                    else:
                        for char, chance in cfg['unique_ground_tiles']:
                            if roll(1, 1000) <= chance:
                                self.make_ground_tile(x, y, char)
                                break

        game.add_message('Vegetation: %.2f' %(time.time() - begin))


    def add_world_features(self, x, y):
        ''' Adds in roads, rivers, caves, etc ... '''
        begin = time.time()


        world_2_wmap_roads= {(1, 0):(self.width-1, int(self.height/2)),
                          (-1, 0):(0, int(self.height/2)),
                          (0, 1):(int(self.width/2), self.height-1),
                          (0, -1):(int(self.width/2), 0)
                          }


        if WORLD.tiles[x][y].has_feature('road'):
            # Find whether there are nearby roads
            road_dirs = []

            for xx, yy in get_border_tiles(x, y):
                if self.world.tiles[xx][yy].has_feature('road'):
                    road_dirs.append((xx-x, yy-y))


            # Figure out where starting road nodes should go
            road_start_positions = []
            for rdir in road_dirs:

                i, j = world_2_wmap_roads[rdir]
                road_start_positions.append(PathNode(x=i, y=j, size=5, neighbors=[]))

            ## Initialize the line, and connect the 2 points. This should
            ## cause roads to be build from appropriate map edges
            while len(road_start_positions) >= 2:
                # pop the 2 road start/endpoints
                r_begin = road_start_positions.pop(0)
                r_end = road_start_positions.pop(0)

                r_begin.connect(other=r_end, n_div=5, div_mag=1, usemap=self)
                # If there's still a point from map edge, add the midpoint of the current road so that others connect
                if len(road_start_positions) == 1:
                    ii, jj = (int((r_begin.x + r_end.x)/2), int((r_begin.y + r_end.y)/2) )
                    road_start_positions.append(PathNode(x=ii, y=jj, size=5, neighbors=[]))


        ## Add cave entrances
        for cave in WORLD.tiles[x][y].caves:
            ## find some tiles that border rock for each cave
            borders_rock = False
            while not borders_rock:
                cx, cy = roll(20, self.width-21), roll(20, self.height-21)
                if not self.tile_blocks_mov(x=cx, y=cy):
                    for nx, ny in get_border_tiles(x=cx, y=cy):
                        if M.tile_blocks_mov(x=nx, y=ny):
                            borders_rock = True
                            break
            #cx, cy = random.choice(self.rock_border_cells)
            self.tiles[cx][cy].char = 'O'
            self.tiles[cx][cy].interactable = {'func':WORLD.make_cave_map, 'args':[x, y, cave], 'text':'Enter cave', 'hover_text':['Cave entrance']}

            game.add_message(new_msg='cave at %i, %i' %(cx, cy), color=libtcod.green)

        game.add_message('World features: %.2f' %(time.time() - begin))


    def run_cellular_automata(self, cfg):
        ''' General method for running cellular automata. Takes a configuration dict which contains info
        about intitial seed chances, iterations, criteria for converting floor to wall, etc '''

        begin = time.time()
        ## Map borders
        wborder = self.width - 1 - cfg['map_pad']
        hborder = self.height - 1 - cfg['map_pad']

        for x in xrange(self.width):
            for y in xrange(self.height):
                # Configuration can choose a certain "padding" of a certain cell type for the map edge
                if (cfg['map_pad'] < x < wborder) and (cfg['map_pad'] < y < hborder):
                    # If it meets the padding criteria, seed the cells
                    if self.tiles[x][y].height > WATER_HEIGHT and (roll(1, 1000) <= cfg['initial_blocks_mov_chance'] or self.tiles[x][y].height > cfg['blocks_mov_height']) \
                        and self.tiles[x][y].zone in (None, 'wilderness') and self.tiles[x][y].surface == 'ground':

                        self.tiles[x][y].blocks_vis = 1
                        self.tiles[x][y].blocks_mov = 1
                    elif self.tiles[x][y].zone in (None, 'wilderness') and self.tiles[x][y].surface == 'ground':
                        self.tiles[x][y].blocks_vis = 0
                        self.tiles[x][y].blocks_mov = 0
                # If it doesn't meet the padding criteria, fill the cell with the padded cell type
                else:
                    self.tiles[x][y].blocks_vis = cfg['map_pad_type']
                    self.tiles[x][y].blocks_mov = cfg['map_pad_type']

        game.add_message('Seed cell automata: %.2f' %(time.time() - begin))
        begin = time.time()
        # Smoothing happens here
        for r in xrange(cfg['repetitions']):
            # Run throught entire map
            for y in xrange(self.height):
                for x in xrange(self.width):
                    if self.tiles[x][y].zone in (None, 'wilderness') and self.tiles[x][y].surface == 'ground':
                        walls = 0
                        floors = 0

                        # Tally number of walls and floors in moore neighborhood
                        for (xx, yy) in (   (x-1, y-1), (x, y-1), (x+1, y+1),
                                            (x-1, y),             (x+1, y),
                                            (x-1, y+1), (x, y+1), (x+1, y-1) ):

                            if self.is_val_xy((xx, yy)):
                                if self.tiles[xx][yy].blocks_vis:
                                    walls += 1
                                else:
                                    floors += 1

                        # Based off of the tallies above, create walls/floors
                        if walls <= cfg['walls_to_floor']:
                            self.tiles[x][y].blocks_mov = False
                            self.tiles[x][y].blocks_vis = False

                        elif walls >= cfg['walls_to_wall']:
                            self.tiles[x][y].blocks_mov = True
                            self.tiles[x][y].blocks_vis = True

        game.add_message('Iterate cell automata: %.2f' %(time.time() - begin))


    def color_blocked_tiles(self, cfg):
        begin = time.time()
        ## This will color the blocks_mov cells as well as shade them
        if cfg['blocks_mov_color'] and cfg['shade']:
            # color it
            light_color = libtcod.color_lerp(cfg['blocks_mov_color'], libtcod.white, .05)
            darkish_color = libtcod.color_lerp(cfg['blocks_mov_color'], libtcod.black, .05)
            darker_color = libtcod.color_lerp(cfg['blocks_mov_color'], libtcod.black, .2)

            hit_rock = 0
            for y in xrange(self.height):
                for x in xrange(self.width):
                    # Hit a tile where Cellular automata placed a rock
                    if self.tiles[x][y].zone in (None, 'wilderness') and self.tiles[x][y].surface == 'ground' and self.tiles[x][y].blocks_vis:
                        if hit_rock == 0:
                            self.tiles[x][y].set_color(color=light_color)
                            hit_rock = 1

                        ### Already hit rock, color in (and shade) the outcropping
                        else:
                            if self.tiles[x][y].height > self.tiles[x-1][y].height:
                                self.tiles[x][y].set_color(color=light_color)
                            elif self.tiles[x][y].height == self.tiles[x-1][y].height:
                                self.tiles[x][y].set_color(color=cfg['blocks_mov_color'])
                            elif self.tiles[x][y].height < self.tiles[x-1][y].height:
                                self.tiles[x][y].set_color(color=darkish_color)

                        self.tiles[x][y].surface = cfg['blocks_mov_surface']

                    #### Hit a free tile, reset hit_rock flag
                    elif (not self.tiles[x][y].blocks_vis) and hit_rock:
                        self.tiles[x-1][y].set_color(color=darker_color)
                        hit_rock = 0

                    #if self.tiles[x][y].surface == cfg['blocks_mov_surface']:
                    #    for xx, yy in get_border_tiles(x, y):
                    #        # Weirdness here, I only check if "block sight", may need to be more comprehensive
                    #        if self.is_val_xy((xx, yy)) and (not self.tiles[xx][yy].blocks_vis) and (xx, yy) not in self.rock_border_cells:
                    #            self.rock_border_cells.append((xx, yy))

            game.add_message('Color blocks_mov cells: %.2f' %(time.time() - begin))

        ## This will just color them (no shading)
        elif cfg['blocks_mov_color']:
            for y in xrange(self.height):
                for x in xrange(self.width):
                    if self.tiles[x][y].blocks_vis:
                        self.tiles[x][y].set_color(color=cfg['blocks_mov_color'])
                        self.tiles[x][y].surface = cfg['blocks_mov_surface']


    def fill_open_pockets(self, target_unfilled_cells):
        ''' Fills nonconnected regions set by cellular automata (for instance, to remove any unconnected unblocks_mov tiles in a cave) '''
        open_tiles = []

        def do_fill(tile):
            tile.tmp_flag = 1
        # Check the map for any seperate pockets of open cells
        for x in xrange(self.width):
            for y in xrange(self.height):
                if not self.tile_blocks_mov(x, y) and not self.tiles[x][y].tmp_flag:
                    filled_tiles = floodfill(fmap=self, x=x, y=y, do_fill=do_fill, do_fill_args=[], is_border=lambda tile: tile.blocks_mov or tile.tmp_flag)

                    if filled_tiles:
                        open_tiles.append(filled_tiles)

        # Figure out the biggest pocket
        largest_ind, largest_amt = 0, 0
        for i, tile_set in enumerate(open_tiles):
            if len(tile_set) > largest_amt:
                largest_ind, largest_amt = i, len(tile_set)

        remaining_open_tiles = open_tiles.pop(largest_ind)
        # Now fill them in
        fill_counter = 0
        for tile_set in open_tiles:
            fill_counter += 1
            x, y = tile_set.pop()

            filled_tiles = floodfill(fmap=self, x=x, y=y, do_fill=lambda tile:tile.make_rock(), do_fill_args=[], is_border=lambda tile: tile.blocks_mov)

        return remaining_open_tiles, fill_counter


    def get_points_for_circular_patrol_route(self, center_x, center_y, radius):
        ''' Will grab some points for a roughly circular patrol route '''
        ## How it works: is_circle_radius only detects points exactly on the circle's radius,
        # which ends up being ~4-12 points. Then we find out a logical order to go around the circle in,
        # and use that as the patrol route.

        def find_closest_point(point, other_points):
            closest_point = None
            closest_dist = 10000
            for opoint in other_points:
                cur_dist = get_distance_to(x=point[0], y=point[1], target_x=opoint[0], target_y=opoint[1])
                if cur_dist < closest_dist:
                    closest_point = opoint
                    closest_dist = cur_dist

            return closest_point, closest_dist

        ## Find those points in a circular pattern
        unordered_points = []
        for x in xrange(center_x-radius, center_x+radius+1):
            for y in xrange(center_y-radius, center_y+radius+1):
                if self.is_val_xy((x, y)) and is_circle_radius(center_x=center_x, center_y=center_y, radius=radius, x=x, y=y):
                    unordered_points.append((x, y))

        ## Now, find a logical order to set as patrol route
        point = unordered_points.pop(0)
        ordered_patrol_points = [point]

        while unordered_points:
            closest_point, closest_dist = find_closest_point(point=point, other_points=unordered_points)

            ordered_patrol_points.append(closest_point)
            unordered_points.remove(closest_point)

            point = closest_point


        ## Make sure the tiles are unblocked
        cleaned_patrol_route = []
        for px, py in ordered_patrol_points:
            # If the tile doesn't block movement - great, it is valid. Make sure to check that tiles are accessible by astar, otherwise...
            if not self.tile_blocks_mov(x=px, y=px): # and (not cleaned_patrol_route or (cleaned_patrol_route and self.get_astar_distance_to(px, py, cleaned_patrol_route[0][0], cleaned_patrol_route[0][0]))):
                cleaned_patrol_route.append((px, py))

            else:
                ## TODO - very inefficient, but will eventually find a valid route
                # Range to search
                srange = 0
                found_point = 0
                while srange < self.width and not found_point:
                    found_point = 0
                    # Will expand a bit each turn
                    srange += 5
                    # Check a certain range of tiles
                    for iteration in xrange(srange*srange):
                        # Get a random tile which is srange away from the current patrol route
                        xx, yy = roll(px-srange, px+srange), roll(py-srange, py+srange)
                        if self.is_val_xy((xx, yy)) and not self.tile_blocks_mov(x=xx, y=yy): # and (not cleaned_patrol_route or (cleaned_patrol_route and self.get_astar_distance_to(xx, yy, cleaned_patrol_route[0][0], cleaned_patrol_route[0][0]))):
                            # If there are any points in the cleaned route, they need to be accessible by astar
                            cleaned_patrol_route.append((xx, yy))
                            found_point = 1
                            break
                # Should have given it plenty of range and time to execute, but otherwise...
                if not found_point:
                    print 'Patrol route could not find acceptable location near', px, ',', py

        return cleaned_patrol_route




class World:
    def __init__(self, width, height):
        global camera, time_cycle

        self.height = height
        self.width = width

        game.world_map_display_type = 'normal'
        game.map_scale = 'world'

        #self.travelers = []
        self.sites = []
        self.resources = []
        self.startlocs = []
        self.ideal_locs = []

        self.dynasties = []
        self.all_figures = []
        self.important_figures = []
        self.plots = []

        self.famous_objects = set([])
        ### TODO - move this around; have it use the actual language of the first city
        self.moons, self.suns = religion.create_astronomy()

        # Set up other important lists
        self.sentient_races = []
        self.brutish_races = []

        self.bands = []
        self.languages = []
        self.cities = []
        self.hideouts = []
        self.factions = []

        self.site_index = {}

        economy.setup_resources()
        #### load phys info ####
        phys.main()
        # Need to set up time cycle
        time_cycle = TimeCycle()

        #self.generate()

    def add_famous_object(self, obj):
        self.famous_objects.add(obj)

    def remove_famous_object(self, obj):
        self.famous_objects.remove(obj)

    def add_to_site_index(self, site):
        if site.site_type not in self.site_index.keys():
            self.site_index[site.site_type] = [site]
        else:
            self.site_index[site.site_type].append(site)

    def generate(self):
        #### Setup actual world ####

        steps = 6
        render_handler.progressbar_screen('Generating World Map', 'creating regions', 1, steps)
        self.setup_world()
        ########################### Begin with heightmap ##################################
        render_handler.progressbar_screen('Generating World Map', 'generating heightmap', 2, steps)
        self.make_heightmap()
        ## Now, loop through map and check each land tile for its distance to water
        render_handler.progressbar_screen('Generating World Map', 'setting moisture', 3, steps)
        self.calculate_water_dist()

        ##### EXPERIMENTOIAENH ######
        #self.calculate_rainfall()
        ########################## Now, generate rivers ########################
        render_handler.progressbar_screen('Generating World Map', 'generating rivers', 4, steps)
        self.gen_rivers()
        ################################ Resources ##########################################
        render_handler.progressbar_screen('Generating World Map', 'setting resources and biome info', 5, steps)
        self.set_resource_and_biome_info()

        ##### End setup actual world #####

        ######## Add some buttons #######
        panel2.wmap_buttons = [
                          gui.Button(gui_panel=panel2, func=self.gen_history, args=[1],
                                     text='Generate History', topleft=(4, PANEL2_HEIGHT-11), width=20, height=5, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),
                          gui.Button(gui_panel=panel2, func=self.generate, args=[],
                                     text='Regenerate Map', topleft=(4, PANEL2_HEIGHT-6), width=20, height=5, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)
                          ]

    def is_val_xy(self, coords):
        return (0 < coords[0] < self.width) and (0 < coords[1] < self.height)

    def tile_blocks_mov(self, x, y):
        if self.tiles[x][y].blocks_mov:
            return True

    def draw_world_objects(self):
        # Just have all world objects represent themselves
        for figure in WORLD.all_figures:
            if not self.tiles[figure.wx][figure.wy].site:
                figure.w_draw()
        #for traveler in self.travelers:
        #    if traveler != player:
        #        traveler.w_draw()

        for site in self.sites:
            site.draw()

        if player is not None:
            player.w_draw()

    #####################################
    def get_astar_distance_to(self, x, y, target_x, target_y):
        libtcod.path_compute(self.path_map, x, y, target_x, target_y)
        new_path_len = libtcod.path_size(self.path_map)

        return new_path_len

    def make_world_road(self, x, y):
        ''' Add a road to the tile's features '''
        if not self.tiles[x][y].has_feature('road'):
            self.tiles[x][y].features.append(Feature(site_type='road', x=x, y=y))

    def set_road_tile(self, x, y):
        N, S, E, W = 0, 0, 0, 0
        if self.tiles[x+1][y].has_feature('road'):
            E = 1
        if self.tiles[x-1][y].has_feature('road'):
            W = 1
        if self.tiles[x][y+1].has_feature('road'):
            S = 1
        if self.tiles[x][y-1].has_feature('road'):
            N = 1

        if N and S and E and W:
            char = chr(197)
        elif N and S and E:
            char = chr(195)
        elif N and E and W:
            char = chr(193)
        elif S and E and W:
            char = chr(194)
        elif N and S and W:
            char = chr(180)
        elif E and W:
            char = chr(196)
        elif E and N:
            char = chr(192)
        elif N and S:
            char = chr(179)
        elif N and W:
            char = chr(217)
        elif S and W:
            char = chr(191)
        elif S and E:
            char = chr(218)
        elif N:
            char = chr(179)
        elif S:
            char = chr(179)
        elif E:
            char = chr(196)
        elif W:
            char = chr(196)
        elif not (N and S and E and W):
            return

        self.tiles[x][y].char = char
        self.tiles[x][y].char_color = libtcod.darkest_sepia


    def get_surrounding_tile_heights(self, coords):
        ''' Return a list of the tile heights surrounding this one, including this tile itself '''
        x, y = coords

        heights = []

        for xx in xrange(x-1, x+2):
            for yy in xrange(y-1, y+2):
                if self.is_val_xy((xx, yy)):
                    heights.append(self.tiles[xx][yy].height)

                # If map edge, just append this tile's own height
                else:
                    heights.append(self.tiles[x][y].height)

        return heights


    def get_surrounding_heights(self, coords):
        world_x, world_y = coords
        surrounding_heights = []
        for x in xrange(world_x-1, world_x+2):
            for y in xrange(world_y-1, world_y+2):
                surrounding_heights.append(self.tiles[x][y].height)

        return surrounding_heights

    def get_surrounding_rivers(self, coords):
        ''' Return a list of the tile heights surrounding this one, including this tile itself '''
        x, y = coords

        river_dirs = []

        for xx, yy in get_border_tiles(x, y):
            if self.is_val_xy((xx, yy)) and self.tiles[xx][yy].has_feature('river'):
                river_dirs.append((x-xx, y-yy))

        ## Quick hack for now - append oceans to rivers
        if len(river_dirs) == 1:
            for xx, yy in get_border_tiles(x, y):
                if self.is_val_xy((xx, yy)) and self.tiles[xx][yy].region == 'ocean':
                    river_dirs.append((x-xx, y-yy))
                    break

        return river_dirs

    def get_closest_city(self, x, y, max_range=1000):
        closest_city = None
        closest_dist = max_range + 1  #start with (slightly more than) maximum range

        for city in self.cities:
            dist = self.get_astar_distance_to(x, y, city.x, city.y)
            if 0 < dist < closest_dist: #it's closer, so remember it
                closest_city = city
                closest_dist = dist
        return closest_city, closest_dist

    def find_nearby_resources(self, x, y, distance):
        # Make a list of nearby resources at particular world coords
        nearby_resources = []
        nearby_resource_locations = []
        for wx in xrange(x - distance, x + distance + 1):
            for wy in xrange(y - distance, y + distance + 1):
                if self.is_val_xy( (wx, wy) ) and len(self.tiles[wx][wy].res.keys()):
                    # Make sure there's a path to get the resource from (not blocked by ocean or whatever)
                    path = libtcod.path_compute(self.rook_path_map, x, y, wx, wy)
                    new_path_len = libtcod.path_size(self.rook_path_map)

                    if new_path_len:
                        for resource in self.tiles[wx][wy].res.iterkeys():
                            ## Only add it if it's not already in it, and if we don't have access to it
                            if not resource in nearby_resources: # and not resource in self.native_res.keys():
                                nearby_resources.append(resource)
                                nearby_resource_locations.append((wx, wy))

                            elif resource in nearby_resources:
                                ## Check whether the current instance of this resource is closer than the previous one
                                cur_dist = self.get_astar_distance_to(x, y, wx, wy)

                                prev_res_ind = nearby_resources.index(resource)
                                px, py = nearby_resource_locations[prev_res_ind]
                                prev_dist = self.get_astar_distance_to(x, y, px, py)

                                if cur_dist < prev_dist:
                                    del nearby_resources[prev_res_ind]
                                    del nearby_resource_locations[prev_res_ind]

                                    nearby_resources.append(resource)
                                    nearby_resource_locations.append((wx, wy))

        return nearby_resources, nearby_resource_locations

    def setup_world(self):
        #fill WORLD with dummy regions
        self.tiles = [
            [Region(region=None, x=x, y=y, color=None, blocks_mov=False, char=' ', char_color=libtcod.black, blocks_vis=False)
             for y in xrange(self.height)]
            for x in xrange(self.width)]

        # Equator line - temperature depends on this. Varies slightly from map to map
        self.equator = int(round(self.height / 2)) + roll(-5, 5)

    def distance_to_equator(self, y):
        return abs(y - self.equator) / (self.height / 2)


    def make_heightmap(self):
        hm = libtcod.heightmap_new(self.width, self.height)
        # Start with a bunch of small, wide hills. Keep them relatively low
        for iteration in xrange(200):
            maxrad = roll(10, 50)

            x, y = roll(maxrad, self.width - maxrad), roll(maxrad, self.height - maxrad)
            if libtcod.heightmap_get_value(hm, x, y) < 80:
                libtcod.heightmap_add_hill(hm, x, y, roll(1, maxrad), roll(10, 25))
            if roll(1, 4) == 1:
                libtcod.heightmap_dig_hill(hm, x, y, roll(4, 20), roll(10, 30))

        # Then add mountain ranges. Should be tall and thin
        for iteration in xrange(100):
            maxrad = 5
            maxlen = 20 + maxrad
            minheight = 5
            maxheight = 10

            x = roll(maxlen, self.width - maxlen)
            y = roll(int(round(self.height / 10)), self.height - int(round(self.height / 10)))

            if libtcod.heightmap_get_value(hm, x, y) < 120:
                libtcod.line_init(x, y, roll(x - maxlen, x + maxlen), roll(y - maxlen, y + maxlen))
                nx, ny = x, y

                while nx is not None:
                    if libtcod.heightmap_get_value(hm, x, y) < 140:
                        libtcod.heightmap_add_hill(hm, nx, ny, roll(1, maxrad), roll(minheight, maxheight))
                    nx, ny = libtcod.line_step()


        ## Added 4/28/2014 - World size must be a power of 2 plus 1 for this to work
        #libtcod.heightmap_mid_point_displacement(hm=hm, rng=0, roughness=.5)

        # Erosion - not sure exactly what these params do
        libtcod.heightmap_rain_erosion(hm, self.width * self.height, .05, .05, rnd=0)
        # And normalize heightmap
        #libtcod.heightmap_normalize(hm, mi=1, ma=255)
        libtcod.heightmap_normalize(hm, mi=1, ma=220)
        #libtcod.heightmap_normalize(hm, mi=20, ma=170)

        ### Noise to vary wdist ### Experimental code ####
        mnoise = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)
        octaves = 20
        div_amt = 20

        thresh = .4
        thresh2 = .8
        scale = 130
        mvar = 30
        ### End experimental code ####

        self.mountains = []
        # Add the info from libtcod's heightmap to the world's heightmap
        for x in xrange(self.width):
            for y in xrange(self.height):
                ############# New ####################
                val = libtcod.noise_get_turbulence(mnoise, [x / div_amt, y / div_amt], octaves, libtcod.NOISE_SIMPLEX)
                #### For turb map, low vals are "peaks" for us ##############
                if val < thresh and self.height / 10 < y < self.height - (self.height / 10):
                    raise_terr = int(round(scale * (1 - val))) + roll(-mvar, mvar)
                elif val < thresh2:
                    raise_terr = int(round((scale / 2) * (1 - val))) + roll(-int(round(mvar / 2)), int(round(mvar / 2)))
                else:
                    raise_terr = 0

                self.tiles[x][y].height = int(round(libtcod.heightmap_get_value(hm, x, y))) + raise_terr
                self.tiles[x][y].height = min(self.tiles[x][y].height, 255)

                if not 5 < x < self.width - 5 and self.tiles[x][y].height >= WATER_HEIGHT:
                    self.tiles[x][y].height = 99
                    #######################################
                if self.tiles[x][y].height > 200:
                    self.mountains.append((x, y))

                #### While we're looping, we might as well add temperature information
                # weird formula for approximating temperature based on height and distance to equator

                ''' Original settings '''
                base_temp = 16
                height_mod = ((1.05 - (self.tiles[x][y].height / 255)) * 4)
                equator_mod = (1.3 - self.distance_to_equator(y)) ** 2

                ''' Newer expermiental settings '''
                #base_temp = 40
                #height_mod = 1
                #equator_mod = (1.3 - self.distance_to_equator(y)) ** 2

                self.tiles[x][y].temp = base_temp * height_mod * equator_mod

                #### And start seeding the water distance calculator
                if self.tiles[x][y].height < WATER_HEIGHT:
                    self.tiles[x][y].wdist = 0
                    self.tiles[x][y].moist = 0
                else:
                    self.tiles[x][y].wdist = None
                    self.tiles[x][y].moist = 100

        # Finally, delete the libtcod heightmap from memory
        libtcod.heightmap_delete(hm)


    '''
    def calculate_rainfall(self):
        # An ok way to calclate rainfall?

        for y in xrange(self.height):
            # Seed initial rainfall based on lattitude
            if 30 < y < self.height-30 or 20 < abs(y-self.equator):
                rainfall = -10
            else:
                rainfall = 10

            # West -> east winds
            for x in xrange(self.width):
                self.tiles[x][y].rainfall = rainfall

                if self.tiles[x][y].height <= WATER_HEIGHT:
                    rainfall += 1
                elif self.tiles[x][y].height <= MOUNTAIN_HEIGHT:
                    rainfall -= 1
                else:
                    rainfall = 0

            # East -> west winds
            #for x in xrange(self.width):
            #    self.tiles[self.width-x][y].rainfall = rainfall
            #
            #    if self.tiles[self.width-x][y].height <= WATER_HEIGHT:
            #        rainfall += 1
            #    elif self.tiles[self.width-x][y].height <= MOUNTAIN_HEIGHT:
            #        rainfall -= 1
            #    else:
            #        rainfall = 0
    '''

    def calculate_water_dist(self):
        ## Essentially a dijisktra map for water distance
        wdist = 0
        found_square = True
        while found_square:
            found_square = False
            wdist += 1

            for x in xrange(1, self.width - 1):
                for y in xrange(1, self.height - 1):

                    if self.tiles[x][y].wdist is None:
                        # Only check water distance at 4 cardinal directions
                        #side_dir = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
                        #corner_dir = [(x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)]
                        for dx, dy in get_border_tiles(x, y):
                            if self.tiles[dx][dy].wdist == wdist - 1:
                                self.tiles[x][y].wdist = self.tiles[dx][dy].wdist + 1
                                # calculate "moisture" to add a little variability - it's related to water dist but takes height into account
                                # Also, LOWER is MORE moist because I'm lazy
                                self.tiles[x][y].moist = self.tiles[x][y].wdist * (1.7 - (self.tiles[x][y].height / 255)) ** 2

                                found_square = True
                                break

    def gen_rivers(self):
        self.rivers = []
        water_bias = 10
        # Walk through all mountains tiles and make a river if there are none nearby
        while len(self.mountains) > 1:
            # Pop out a random mountain tile
            (x, y) = self.mountains.pop(roll(0, len(self.mountains) - 1) )
            # Check if another river already exists nearby, and abort if so
            make_river = True
            for riv_x in xrange(x - 4, x + 5):
                for riv_y in xrange(y - 4, y + 5):
                    if self.tiles[riv_x][riv_y].has_feature('river'):
                        make_river = False
                        break

            if make_river:
                # create a river
                #self.tiles[x][y].features.append(River(x=x, y=y))
                riv_cur = [(x, y)]

                new_x, new_y = x, y
                found_lower_height = True
                i = 0
                while self.tiles[new_x][new_y].height >= WATER_HEIGHT:
                    i += 1
                    if i >= 100:
                        print 'river loop exceeded 100 iterations'
                        break

                    cur_x, cur_y = new_x, new_y

                    # create 4 cardinal directions and set low_height value
                    directions = [(new_x - 1, new_y), (new_x + 1, new_y), (new_x, new_y - 1), (new_x, new_y + 1)]
                    # Rivers try to flow through lower areas, but take distance to oceans into account to avoid
                    # getting trapped in local minimum valleys
                    biased_height = self.tiles[new_x][new_y].wdist * water_bias
                    low_height = self.tiles[new_x][new_y].height + biased_height

                    if found_lower_height:
                        low_height = False
                        for rx, ry in directions:
                            if self.tiles[rx][ry].height + biased_height <= low_height: # and not (nx, ny) in riv_cur:
                                low_height = self.tiles[rx][ry].height + biased_height
                                new_x = rx
                                new_y = ry
                                low_height = True

                        if not low_height:
                            found_lower_height = False

                    # if it does get trapped in a local minimum, flow in the direction of the lowest distance to water
                    # and preferentially in the lowest height of these tiles
                    if not found_lower_height:
                        wdist = 1000
                        height = 1000

                        for nx, ny in directions:
                            if self.tiles[nx][ny].wdist <= wdist and self.tiles[nx][ny].height < height and not (nx, ny) in riv_cur:
                                wdist = self.tiles[nx][ny].wdist
                                height = self.tiles[nx][ny].height
                                new_x = nx
                                new_y = ny

                    if self.tiles[new_x][new_y].height < WATER_HEIGHT:
                        break
                        # Rivers can join existing ones
                    if self.tiles[new_x][new_y].has_feature('river'):
                        break

                    riv_cur.append((new_x, new_y))
                    ### Rivers cut through terrain if needed, and also make the areas around them more moist
                    # Try to lower the tile's height if it's higher than the previous tile, but don't go lower than 100
                    self.tiles[new_x][new_y].height = min(self.tiles[new_x][new_y].height, max(self.tiles[cur_x][cur_y].height - 1, WATER_HEIGHT))
                    directions = [(new_x - 1, new_y), (new_x + 1, new_y), (new_x, new_y - 1), (new_x, new_y + 1)]
                    for rx, ry in directions:
                        self.tiles[rx][ry].moist = self.tiles[rx][ry].moist / 2


                for i in xrange(len(riv_cur)):
                    (x, y) = riv_cur[i]
                    self.tiles[x][y].char_color = libtcod.Color(10, 35, int(round(self.tiles[x][y].height)))
                    river_feature = River(x=x, y=y)
                    self.tiles[x][y].features.append(river_feature)

                    N, S, E, W = 0, 0, 0, 0

                    if 0 < i:
                        px, py = riv_cur[i - 1]
                        if i < len(riv_cur) - 1:
                            nx, ny = riv_cur[i + 1]

                        d1x, d1y = px - x, py - y
                        if (d1x, d1y) == (-1, 0) or self.tiles[x - 1][y].height < WATER_HEIGHT: W = 1
                        if (d1x, d1y) == (1, 0) or self.tiles[x + 1][y].height < WATER_HEIGHT: E = 1
                        if (d1x, d1y) == (0, 1) or self.tiles[x][y + 1].height < WATER_HEIGHT: S = 1
                        if (d1x, d1y) == (0, -1) or self.tiles[x][y - 1].height < WATER_HEIGHT: N = 1

                        river_feature.add_connected_dir(direction=(d1x, d1y))

                        if i < len(riv_cur) - 1:
                            d2x, d2y = nx - x, ny - y
                            if (d2x, d2y) == (-1, 0) or self.tiles[x - 1][y].height < WATER_HEIGHT: W = 1
                            if (d2x, d2y) == (1, 0) or self.tiles[x + 1][y].height < WATER_HEIGHT: E = 1
                            if (d2x, d2y) == (0, 1) or self.tiles[x][y + 1].height < WATER_HEIGHT: S = 1
                            if (d2x, d2y) == (0, -1) or self.tiles[x][y - 1].height < WATER_HEIGHT: N = 1

                            river_feature.add_connected_dir(direction=(d2x, d2y))

                    elif i == 0:
                        if (x - 1, y) in riv_cur:
                            W = 1
                        elif (x + 1, y) in riv_cur:
                            E = 1
                        elif (x, y + 1) in riv_cur:
                            S = 1
                        elif (x, y - 1) in riv_cur:
                            N = 1

                    if E and W:
                        char = chr(196)
                    elif E and N:
                        char = chr(192)
                    elif N and S:
                        char = chr(179)
                    elif N and W:
                        char = chr(217)
                    elif S and W:
                        char = chr(191)
                    elif S and E:
                        char = chr(218)
                    elif N:
                        char = chr(179)
                    elif S:
                        char = chr(179)
                    elif E:
                        char = chr(196)
                    elif W:
                        char = chr(196)

                    self.tiles[x][y].char = char

                #self.tiles[x][y].char = river_dir[dx, dy]

                #(1, 0)        E    205 #(1, 1)     NE    201 #(0, 1)     N    182    #(-1, 1)    NW    187
                #(-1, 0)    W    205    #(-1, -1)    SW    188 #(0, -1)    S    182    #(1, -1)    SE    200
                #river_dir = {(1, 0):chr(205), (1, 1):chr(200), (0, 1):chr(186), (-1, 1):chr(188),
                #            (-1, 0):chr(205), (-1, -1):chr(187), (0, -1):chr(186), (1, -1):chr(201)}

                self.rivers.append(riv_cur)


        ## Experimental code to vary moisture and temperature a bit
        noisemap1 = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)
        noisemap2 = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)

        n1octaves = 12
        n2octaves = 10

        n1div_amt = 75
        n2div_amt = 50

        n1scale = 20
        n2scale = 15
        #1576
        ## Map edge is unwalkable
        for y in xrange(self.height):
            for x in xrange(self.width):
                # moist
                w_val = libtcod.noise_get_fbm(noisemap1, [x / n1div_amt, y / n1div_amt], n1octaves, libtcod.NOISE_SIMPLEX)
                w_val += .1
                self.tiles[x][y].moist =  max(0, self.tiles[x][y].moist + int(round(w_val * n1scale)) )
                # temp
                t_val = libtcod.noise_get_fbm(noisemap2, [x / n2div_amt, y / n2div_amt], n2octaves, libtcod.NOISE_SIMPLEX)
                self.tiles[x][y].temp =  self.tiles[x][y].temp + int(round(t_val * n2scale))
        ### End experimental code ####


    def set_resource_and_biome_info(self):
        ''' TODO NEW FUNCTION DEFINITION TO MODIFY FOR NEW RAIN CODE '''
        ''' Finally, use the scant climate info generated to add biome and color information '''
        for y in xrange(self.height):
            for x in xrange(self.width):
                sc = int(self.tiles[x][y].height) - 1
                mmod = int(round(40 - self.tiles[x][y].moist) / 1.4) - 25
                a = 3
                #mthresh = 1.04
                ## Ocean
                if self.tiles[x][y].height < WATER_HEIGHT:
                    self.tiles[x][y].region = 'ocean'
                    self.tiles[x][y].blocks_mov = True
                    if self.tiles[x][y].height < 75:
                        self.tiles[x][y].color = libtcod.Color(7, 13, int(round(sc * 2)) + 10)
                    else:
                        self.tiles[x][y].color = libtcod.Color(20, 60, int(round(sc * 2)) + 15)

                elif self.tiles[x][y].height > MOUNTAIN_HEIGHT:
                    self.tiles[x][y].blocks_mov = True
                    self.tiles[x][y].blocks_vis = True
                    self.tiles[x][y].region = 'mountain'
                    #WORLD.tiles[x][y].color = libtcod.Color(117+roll(-a,a), 130+roll(-a,a), 104+roll(-a,a))
                    #WORLD.tiles[x][y].color = libtcod.Color(43+roll(-a,a), 40+roll(-a,a), 34+roll(-a,a))
                    #WORLD.tiles[x][y].color = libtcod.Color(118+roll(-a,a), 90+roll(-a,a), 80+roll(-a,a))

                    ############################ Latest backup #######################################
                    #self.tiles[x][y].color = libtcod.Color(43+roll(-a,a), 45+roll(-a,a), 34+roll(-a,a))
                    #self.tiles[x][y].char_color = libtcod.Color(33+roll(-a,a), 30+roll(-a,a), 24+roll(-a,a))

                    c = int(round((self.tiles[x][y].height - 200) / 2))
                    d = -int(round(c / 2))
                    self.tiles[x][y].color = libtcod.Color(d + 43 + roll(-a, a), d + 50 + roll(-a, a),
                                                          d + 34 + roll(-a, a))
                    if self.tiles[x][y].height > 235:
                        self.tiles[x][y].char_color = libtcod.grey
                    else:
                        self.tiles[x][y].char_color = libtcod.Color(c + 38 + roll(-a, a), c + 25 + roll(-a, a),
                                                                   c + 21 + roll(-a, a))
                    self.tiles[x][y].char = chr(036)

                ## Tundra
                elif self.tiles[x][y].temp < 18 and not ( 25 < y < self.height-25):
                    self.tiles[x][y].region = 'tundra'
                    self.tiles[x][y].color = libtcod.Color(190 + roll(-a - 2, a + 2), 188 + roll(-a - 2, a + 2),
                                                          189 + roll(-a - 2, a + 2))

                elif self.tiles[x][y].temp < 23 and self.tiles[x][y].moist < 22 and not ( 30 < y < self.height-30):
                    self.tiles[x][y].region = 'taiga'
                    self.tiles[x][y].color = libtcod.Color(127 + roll(-a, a), 116 + roll(-a, a), 115 + roll(-a, a))

                    if not self.tiles[x][y].has_feature('river'):
                        self.tiles[x][y].char_color = libtcod.Color(23 + roll(-a, a), 58 + mmod + roll(-a, a),
                                                                   9 + roll(-a, a))
                        if roll(1, 2) == 1:
                            self.tiles[x][y].char = chr(5)
                        else:
                            self.tiles[x][y].char = '^'

                elif self.tiles[x][y].temp < 30 and self.tiles[x][y].moist < 18:
                    self.tiles[x][y].region = 'temperate forest'
                    self.tiles[x][y].color = libtcod.Color(53 + roll(-a, a), 75 + mmod + roll(-a, a), 32 + roll(-a, a))

                    if not self.tiles[x][y].has_feature('river'):
                        self.tiles[x][y].char_color = libtcod.Color(25 + roll(-a, a), 55 + mmod + roll(-a, a), 20 + roll(-a, a))
                        if roll(1, 2) == 1:
                            self.tiles[x][y].char = chr(5)
                        else:
                            self.tiles[x][y].char = chr(6)

                elif self.tiles[x][y].temp < 35:
                    self.tiles[x][y].region = 'temperate steppe'
                    self.tiles[x][y].color = libtcod.Color(65 + roll(-a, a), 97 + mmod + roll(-a, a), 41 + roll(-a, a))

                    if not self.tiles[x][y].has_feature('river'):
                        self.tiles[x][y].char_color = self.tiles[x][y].color * .85
                        self.tiles[x][y].char = chr(176)

                elif self.tiles[x][y].temp > 47 and self.tiles[x][y].moist < 18:
                    self.tiles[x][y].region = 'rain forest'
                    self.tiles[x][y].color = libtcod.Color(40 + roll(-a, a), 60 + mmod + roll(-a, a), 18 + roll(-a, a))

                    if not self.tiles[x][y].has_feature('river'):
                        self.tiles[x][y].char_color = libtcod.Color(16 + roll(-a, a), 40 + roll(-a - 5, a + 5),
                                                                   5 + roll(-a, a))
                        if roll(1, 2) == 1:
                            self.tiles[x][y].char = chr(6)
                        else:
                            self.tiles[x][y].char = '*'

                elif self.tiles[x][y].temp >= 35 and self.tiles[x][y].moist < 18:
                    self.tiles[x][y].region = 'tree savanna'
                    self.tiles[x][y].color = libtcod.Color(50 + roll(-a, a), 85 + mmod + roll(-a, a), 25 + roll(-a, a))
                    #self.tiles[x][y].color = libtcod.Color(209, 189, 126)  # grabbed from a savannah image
                    #self.tiles[x][y].color = libtcod.Color(139, 119, 56)

                    if not self.tiles[x][y].has_feature('river'):
                        if roll(1, 5) > 1:
                            self.tiles[x][y].char_color = self.tiles[x][y].color * .85
                            self.tiles[x][y].char = chr(176)
                        else:
                            self.tiles[x][y].char_color = self.tiles[x][y].color * .75
                            self.tiles[x][y].char = '*'

                elif self.tiles[x][y].temp >= 35 and self.tiles[x][y].moist < 34:
                    self.tiles[x][y].region = 'grass savanna'
                    self.tiles[x][y].color = libtcod.Color(91 + roll(-a, a), 110 + mmod + roll(-a, a), 51 + roll(-a, a))
                    #self.tiles[x][y].color = libtcod.Color(209, 189, 126) # grabbed from a savannah image
                    #self.tiles[x][y].color = libtcod.Color(179, 169, 96)

                    if not self.tiles[x][y].has_feature('river'):
                        self.tiles[x][y].char_color = self.tiles[x][y].color * .80
                        self.tiles[x][y].char = chr(176)

                elif self.tiles[x][y].temp <= 44:
                    self.tiles[x][y].region = 'dry steppe'
                    self.tiles[x][y].color = libtcod.Color(99 + roll(-a, a), 90 + roll(-a, a + 1), 59 + roll(-a, a + 1))

                elif self.tiles[x][y].temp > 44 and self.tiles[x][y].moist < 48:
                    self.tiles[x][y].region = 'semi-arid desert'
                    self.tiles[x][y].color = libtcod.Color(178 + roll(-a - 1, a + 2), 140 + roll(-a - 1, a + 2),
                                                          101 + roll(-a - 1, a + 2))

                elif self.tiles[x][y].temp > 44:
                    self.tiles[x][y].region = 'arid desert'
                    self.tiles[x][y].color = libtcod.Color(212 + roll(-a - 1, a + 1), 185 + roll(-a - 1, a + 1),
                                                          142 + roll(-a - 1, a + 1))

                # Hopefully shouldn't come to this
                else:
                    self.tiles[x][y].region = 'none'
                    self.tiles[x][y].color = libtcod.red


                #### New code - add resources
                for resource in economy.RESOURCES:
                    for biome, chance in resource.app_chances.iteritems():
                        if biome == self.tiles[x][y].region or (biome == 'river' and self.tiles[x][y].has_feature('river')):
                            if roll(1, 1200) < chance:
                                self.tiles[x][y].res[resource.name] = resource.app_amt

                                # Hack in the ideal locs and start locs
                                if resource.name == 'food':
                                    self.ideal_locs.append((x, y))
                                if self.tiles[x][y].temp >= 20:
                                    self.startlocs.append((x, y))


        # Need to calculate pathfinding
        self.initialize_fov()


        ## Try to shade the map
        max_alpha = .9
        for y in xrange(2, WORLD_HEIGHT-2):
            for x in xrange(2, WORLD_WIDTH-2):
                if self.tiles[x][y].region != 'ocean' and self.tiles[x+1][y].region != 'ocean':
                    hdif = self.tiles[x][y].height / self.tiles[x+1][y].height

                    if hdif <= 1:
                        alpha = max(hdif, max_alpha)
                        self.tiles[x][y].color = libtcod.color_lerp(libtcod.lightest_sepia, self.tiles[x][y].color, alpha )
                        if not self.tiles[x][y].has_feature('river'):
                            self.tiles[x][y].char_color = libtcod.color_lerp(libtcod.white, self.tiles[x][y].char_color, alpha )
                    elif hdif > 1:
                        alpha = max(2 - hdif, max_alpha)
                        self.tiles[x][y].color = libtcod.color_lerp(libtcod.darkest_sepia, self.tiles[x][y].color, alpha)
                        if not self.tiles[x][y].has_feature('river'):
                            self.tiles[x][y].char_color = libtcod.color_lerp(libtcod.darkest_sepia, self.tiles[x][y].char_color, alpha)

                    # Experimental badly placed code to add a "hill" character to hilly map spots
                    if alpha == max_alpha and not(self.tiles[x][y].region in ('mountain', 'temperate forest', 'rain forest') ) \
                                                 and not self.tiles[x][y].has_feature('river'):

                        self.tiles[x][y].char = chr(252)
                        if self.tiles[x][y].region in ('semi-arid desert', 'arid desert', 'dry steppe'):
                            self.tiles[x][y].char_color = self.tiles[x][y].color - libtcod.Color(12, 12, 12)

                ################## OUT OF PLACE CAVE GEN CODE ###############
                if self.tiles[x][y].region != 'mountain' and self.tiles[x][y].height > MOUNTAIN_HEIGHT-10 and roll(1, 100) <= 20:
                    cave = Site(world=self, site_type='cave', x=x, y=y, char=' ', name=None, color=libtcod.black, underground=1)
                    self.tiles[x][y].caves.append(cave)
                    self.tiles[x][y].char = 'C'



        exclude_smooth = ['ocean']
        # Smooth the colors of the world
        for y in xrange(2, self.height - 2):
            for x in xrange(2, self.width - 2):
                if not self.tiles[x][y].region in exclude_smooth:
                    neighbors = ((x - 1, y - 1), (x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1), (x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1))
                    #colors = [WORLD.tiles[nx][ny].color for (nx, ny) in neighbors]
                    if not self.tiles[x][y].region == 'mountain':
                        smooth_coef = .25
                    else:
                        smooth_coef = .1

                    #border_ocean = 0
                    used_regions = ['ocean'] #Ensures color_lerp doesn't try to interpolate with almost all of the neighbors
                    for nx, ny in neighbors:
                        if self.tiles[nx][ny].region != self.tiles[x][y].region and self.tiles[nx][ny].region not in used_regions:
                            used_regions.append(self.tiles[ny][ny].region)
                            self.tiles[x][y].color = libtcod.color_lerp(self.tiles[x][y].color, self.tiles[nx][ny].color, smooth_coef)
                        #if self.tiles[nx][ny].region == 'ocean':
                        #    border_ocean = 1
                    ## Give a little bit of definition to coast tiles
                    #if border_ocean:
                    #    self.tiles[x][y].color = libtcod.color_lerp(self.tiles[x][y].color, libtcod.Color(212, 185, 142), .1)

                '''
				# Smooth oceans too
				else:
					smooth_coef = .1
					neighbors = [(x-1, y-1), (x-1, y), (x, y-1), (x+1, y), (x, y+1), (x+1, y+1), (x+1, y-1), (x-1,y+1)]
					for nx, ny in neighbors:
						if self.tiles[nx][ny].region == self.tiles[x][y].region:
							self.tiles[x][y].color = libtcod.color_lerp(self.tiles[x][y].color, self.tiles[nx][ny].color, smooth_coef)
				'''


    def gen_history(self, years):
        self.gen_sentient_races()
        self.gen_cultures()
        self.create_civ_cradle()
        self.settle_cultures()
        self.run_history(years)

        ## Add a "start playing" button if there isn't already one
        for button in panel2.wmap_buttons:
            if button.text == 'Start Playing':
                break
        else:
            panel2.wmap_buttons.append(gui.Button(gui_panel=panel2, func=game.new_game, args=[],
                                    text='Start Playing', topleft=(4, PANEL2_HEIGHT-16), width=20, height=5, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True))


    def gen_sentient_races(self):
        ''' Generate some sentient races to populate the world. Very basic for now '''
        for i in xrange(5):
            # Throwaway language for now
            race_name_lang = lang.Language()
            creature_name = race_name_lang.gen_word(syllables=roll(1, 2), num_phonemes=(2, 20))
            # Shares physical components with humans for now
            phys_info = copy.deepcopy(phys.creature_dict['human'])

            description = gen_creatures.gen_creature_description(lang.spec_cap(creature_name))

            phys_info['name'] = creature_name
            phys_info['description'] = description

            phys.creature_dict[creature_name] = phys_info
            self.sentient_races.append(creature_name)

            game.add_message('{0} added'.format(lang.spec_cap(creature_name)))

        ## These guys will be less intelligent and more brute-ish. Generally live in lairs or move into existing empty structures
        for i in xrange(5):
            # Throwaway language for now
            race_name_lang = lang.Language()
            creature_name = race_name_lang.gen_word(syllables=roll(1, 2), num_phonemes=(2, 10))
            # Shares physical components with humans for now
            phys_info = copy.deepcopy(phys.creature_dict['human'])

            description = gen_creatures.gen_creature_description(creature_name=lang.spec_cap(creature_name), creature_size=3)

            phys_info['name'] = creature_name
            phys_info['description'] = description

            phys.creature_dict[creature_name] = phys_info
            self.brutish_races.append(creature_name)

            game.add_message('- {0} added'.format(lang.spec_cap(creature_name)))



    def gen_cultures(self):
        begin = time.time()

        ## Place some hunter-getherer cultures
        while len(self.startlocs) > 1:
            # Random coords
            cx, cy = random.choice(self.startlocs)
            # Make sure it's a legit tile and that no other culture owns it
            if not self.tiles[cx][cy].blocks_mov and self.tiles[cx][cy].culture == None:
                # spawn a band
                language = lang.Language()
                self.languages.append(language)
                if roll(1, 10) > 2:
                    races = [random.choice(self.sentient_races)]
                else:
                    # Pick more than one race to be a part of this culture
                    races = []
                    for i in xrange(2):
                        while 1:
                            race = random.choice(self.sentient_races)
                            if race not in races:
                                races.append(race)
                                break

                band = Culture(color=random.choice(civ_colors), language=language, world=self, races=races)

                ## Track neighbors
                neighbor_cultures = []

                original_region = self.tiles[cx][cy].region
                self.tiles[cx][cy].culture = band
                band.territory.append((cx, cy))

                filled_cells = [(cx, cy)]
                edge = [(cx, cy)]
                expansions = roll(10, 25)
                while edge and expansions:
                    expansions -= 1
                    newedge = []
                    for (x, y) in edge:
                        for (s, t) in get_border_tiles(x, y):
                            if self.is_val_xy((s, t)) and not self.tiles[s][t].blocks_mov and not self.tiles[s][t].culture:
                                ## Not very efficient but sort of helps prevent cultures from looking too "square"
                                ## We'll always expand into our original region, but only a chance of expanding if not
                                if roll(1, 5) >= 4 or self.tiles[s][t].region == original_region:
                                    self.tiles[s][t].culture = band
                                    band.territory.append((s, t))

                                    filled_cells.append((s, t))
                                    newedge.append((s, t))
                                ## If we didn't expand, put the original tile back in so it gets another chance
                                elif not (x, y) in newedge:
                                    newedge.append((x, y))
                            # If we bump into a neighbor, remember that
                            elif self.tiles[s][t].culture and self.tiles[s][t].culture != band:
                                neighbor_cultures.append(self.tiles[s][t].culture)

                    edge = newedge

                # Smaller cultures get absorbed
                if len(filled_cells) <= 2 and len(neighbor_cultures):
                    absorber = random.choice(neighbor_cultures)

                    for (s, t) in filled_cells:
                        self.tiles[s][t].culture = absorber
                        absorber.territory.append((s, t))
                        # Make sure neighbors transfer correctly
                    for culture in neighbor_cultures:
                        if culture not in absorber.neighbor_cultures:
                            absorber.neighbor_cultures.append(culture)
                            culture.neighbor_cultures.append(absorber)

                # Smaller cultures with no neighbors can die out
                elif len(filled_cells) < 10 and roll(1, 5) >= 2 and len(neighbor_cultures) == 0:
                    for (q, r) in band.territory:
                        self.tiles[q][r].culture = None

                # Normal case - nothing happens, and we meet our neighbors
                else:
                    self.bands.append(band)

                    for culture in neighbor_cultures:
                        band.neighbor_cultures.append(culture)
                        culture.neighbor_cultures.append(band)

                # After growing, remove the spot from the master "while" loop
                self.startlocs.remove((cx, cy))

            else:
                # not a good location, so delete
                self.startlocs.remove((cx, cy))

        ## Clean up ideal_locs a bit, so that cities can't start where there's no culture
        ## Reverse to avoid skipping ahead if something gets deleted
        for x, y in reversed(self.ideal_locs):
            if (not self.tiles[x][y].culture) or self.tiles[x][y].blocks_mov:
                self.ideal_locs.remove((x, y))

        game.add_message('Cultures created in %.2f seconds' %(time.time() - begin))

        render_handler.render_all()

    def settle_cultures(self):
        '''Right now, a really simple and bad way to get some additional settlements'''
        for band in self.bands:
            if roll(1, 5) == 1:
                band.add_villages()

                # Now that the band has some villages, it can change its subsistence strageties
                band.set_subsistence(random.choice(('Horticulturalist', 'Pastoralist')))
                band.create_culture_weapons()


    def create_civ_cradle(self):
        ''' Create a bundle of city states'''
        begin = time.time()

        ## Find an area where all resource types are available
        unavailable_resource_types = ['initial_dummy_value']
        while unavailable_resource_types:
            x, y = random.choice(self.ideal_locs)
            if self.is_valid_site(x, y, None, MIN_SITE_DIST):
                # Check for economy
                nearby_resources, nearby_resource_locations = self.find_nearby_resources(x=x, y=y, distance=MAX_ECONOMY_DISTANCE)
                ## Use nearby resource info to determine whether we can sustain an economy
                unavailable_resource_types = economy.check_strategic_resources(nearby_resources)

        # Seed with initial x, y value
        city_sites = [(x, y)]
        # Running list of created cities
        created_cities = []
        # Running list of cultures who have created cities
        civilized_cultures = []

        while city_sites != []:
            nx, ny = random.choice(city_sites)
            city_sites.remove((nx, ny))
            ########## :( #################
            # Make sure the chosen site has a path to the rest of the cities
            # Should prevent stray cities on islands or whatever
            road_path = libtcod.path_compute(self.rook_path_map, x, y, nx, ny)
            new_path_len = libtcod.path_size(self.rook_path_map)
            if (x, y) == (nx, ny):
                new_path_len = 1
            elif not new_path_len:
                print 'new_path_len', new_path_len, ', so looks like this did something'
            ########## :( ###############

            if not new_path_len or self.tiles[nx][ny].culture == None or self.tiles[nx][ny].site != None:
                continue

            ## Ugly hack for now - but we don't want a city to start with JUST food
            if self.tiles[nx][ny].res.keys() == ['food']:
                self.tiles[nx][ny].res['flax'] = 2000
            #################
            # This will later civilize the cultures that cities start in
            if self.tiles[nx][ny].culture not in civilized_cultures:
                civilized_cultures.append(self.tiles[nx][ny].culture)
            ################
            civ_color = random.choice(civ_colors)
            name = lang.spec_cap(self.tiles[nx][ny].culture.language.gen_word(syllables=roll(1, 2), num_phonemes=(2, 20)))

            profession = Profession(name='King', category='noble')
            city_faction = Faction(leader_prefix='King', faction_name='City of %s'%name, color=civ_color, succession='dynasty')

            city = self.make_city(cx=nx, cy=ny, char=chr(10), color=civ_color, name=name, faction=city_faction)

            ### Add initial leader and dynasty ####
            leader, all_new_figures = city.create_initial_dynasty(wife_is_new_dynasty=1)
            city_faction.set_leader(leader)
            profession.give_profession_to(figure=leader)
            profession.set_building(building=city.get_building(building_name='City Hall'))

            created_cities.append(city)
            ####################################

            # Setup satellites around the city #
            for resource_loc in nearby_resource_locations:
                wx, wy = resource_loc
                distance_to_city = self.get_astar_distance_to(nx, ny, wx, wy)
                ## Occasionally they can colonize an area where no culture actively exists, this should fix that
                if self.tiles[wx][wy].culture is None:
                    self.tiles[wx][wy].culture = city.culture

                if self.tiles[wx][wy].culture not in civilized_cultures:
                    civilized_cultures.append(self.tiles[wx][wy].culture)
                ## Now, create colonies
                if self.tiles[wx][wy].site == None and distance_to_city <= 3:
                    ## TITLE INFO ##
                    ## Creating a village which will be vassal to the original city
                    vname = lang.spec_cap(self.tiles[nx][ny].culture.language.gen_word(syllables=roll(1, 2), num_phonemes=(2, 20)))

                    profession = Profession(name='Chief', category='noble')
                    new_faction = Faction(leader_prefix='Chief', faction_name='Chiefdom of %s'%vname, color=civ_color, succession='dynasty')
                    city.faction.set_subfaction(new_faction)

                    village = self.make_city(cx=wx, cy=wy, char='+', color=civ_color, name=vname, faction=new_faction)

                    ## New dynasty here too
                    leader, all_new_figures = village.create_initial_dynasty(wife_is_new_dynasty=1)
                    new_faction.set_leader(leader)
                    profession.give_profession_to(figure=leader)
                    profession.set_building(building=village.get_building(building_name='City Hall'))

                    created_cities.append(village)
                    #########################
                    for resource, amount in self.tiles[wx][wy].res.iteritems():
                        city.add_import(village, resource)
                        village.add_export(city, resource)
                        # Add the resource to the city's access
                        #city.obtain_resource(resource, amount-10)

                elif self.tiles[wx][wy].site == None and distance_to_city > 3:
                    ## add any site which if greater than a certain distance
                    city_sites.append((wx, wy))

        ## We assume the domestication of food has spread to all nearby cities
        for city in created_cities:
            if not 'food' in city.native_res.keys():
                city.native_res['food'] = 2000
                self.tiles[city.x][city.y].res['food'] = 2000

            if self.tiles[city.x][city.y].culture.subsistence != 'Agriculture':
                self.tiles[city.x][city.y].culture.set_subsistence('Agriculture')

            # Make sure the cultures the cities are a part of gain access to the resource
            for resource in self.tiles[city.x][city.y].res.keys():
                if resource not in self.tiles[city.x][city.y].culture.access_res:
                    self.tiles[city.x][city.y].culture.access_res.append(resource)
        ## The cultures surrounding the cities now fill in with villages, sort of
        for culture in civilized_cultures:
            # Add some more gods to their pantheons, and update the relationships between them
            culture.pantheon.create_misc_gods(num_misc_gods=roll(4, 6))
            culture.pantheon.update_god_relationships()

            #### Give the culture's pantheon a holy object ####
            object_blueprint = phys.object_dict['holy relic']
            material = phys.materials['copper']
            initial_location = random.choice(culture.territory)
            obj = assemble_object(object_blueprint=object_blueprint, creature=None, sapient=None, local_brain=None, world_brain=None, force_material=material, wx=initial_location[0], wy=initial_location[1])
            culture.pantheon.add_holy_object(obj)
            self.add_famous_object(obj=obj)

            # Object will be put inside a temple
            housed_city = random.choice(filter(lambda city: city.culture == culture, created_cities))
            temple = housed_city.get_building('Temple')
            obj.set_current_building(building=temple)

            # Object will be owned by the High Priest
            for worker in temple.current_workers:
                if worker.sapient.profession.name == 'High Priest':
                    obj.set_current_owner(worker)
                    break

            # The culture can add some other villages nearby
            culture.add_villages()


        ## Add appropriate imports and exports (can be re-written to be much more efficient...)
        for city in created_cities:
            # At this point, we should have no imports, but just in case... flatten the list
            flattened_import_list = [item for sublist in city.imports.values() for item in sublist]
            ## Make a list of other cities by distance, so you can import from the closer cities first
            cities_and_distances = [(city.distance_to(c), c) for c in created_cities if c != city]
            cities_and_distances.sort()

            for distance, other_city in cities_and_distances:
                for resource in other_city.native_res.keys():
                    # If they have stuff we don't have access to and are not currently importing...
                    if resource not in city.native_res.keys() and resource not in flattened_import_list:
                        # Import it!
                        city.add_import(other_city, resource)
                        other_city.add_export(city, resource)
                        ## Update the import list because we are now importing stuff
                        flattened_import_list.append(resource)

        ## Ugly ugly road code for now
        for city in created_cities:

            closest_ucity = self.get_closest_city(city.x, city.y, 100)[0]
            if closest_ucity not in city.connected_to:
                city.build_road_to(closest_ucity.x, closest_ucity.y)
                city.connect_to(closest_ucity)

        ###################################
        ###### This code makes me cry   ###
        ###################################
        city_list = created_cities[:]
        clumped_cities = []

        # Keep going until city list is empty
        while len(city_list):
            # Pick the first city
            city_clump = []
            untested_cities = [city_list[0]]
            while len(untested_cities):

                ucity = untested_cities.pop(0)
                city_list.remove(ucity)
                city_clump.append(ucity)

                for ccity in ucity.connected_to:
                    if ccity not in city_clump and ccity in city_list:

                        untested_cities.append(ccity)

            # Once there are no more connections,they form a clump
            clumped_cities.append(city_clump)

        ## Time to create the actual network. Here we search for clumps of cities
        ## which have not been joined together, and join them at their closest cities
        networked_cities = clumped_cities.pop(0)

        while len(clumped_cities):
            other_clump = clumped_cities.pop(0)

            c1, c2 = self.find_closest_clumped_cities(networked_cities, other_clump)

            if c1 is not None:
                c1.build_road_to(c2.x, c2.y)
                c1.connect_to(c2)

                for ocity in other_clump:
                    networked_cities.append(ocity)
        ################################################################################

        # Make libtcod path map, where only roads are walkable
        self.refresh_road_network(networked_cities)

        # Time to go through and see if we can create slightly more efficient paths from city to city
        for city in networked_cities:
            for other_city in [c for c in networked_cities if c != city]:

                current_path_len = max(len(city.path_to[other_city]), 1)

                new_path_len = self.get_astar_distance_to(city.x, city.y, other_city.x, other_city.y)

                ratio = new_path_len/current_path_len

                if ratio <= .65:
                    # Build a new road
                    city.build_road_to(other_city.x, other_city.y, libtcod.darker_sepia)
                    city.connect_to(other_city)
                    # Translate and save libtcod paths
                    path_to_other_city = libtcod_path_to_list(path_map=self.road_path_map)

                    # Kill 2 birds with one stone (sort of)
                    other_city_path_to_us = path_to_other_city[:]
                    other_city_path_to_us.reverse()

                    city.path_to[other_city] = path_to_other_city
                    other_city.path_to[city] = other_city_path_to_us
                    # Now that the road has been built, other cities can use it to path to yet more cities
                    self.refresh_road_network(networked_cities)

        for city in networked_cities:
            for other_city in [c for c in networked_cities if c != city]:
                path = city.path_to[other_city]
                for (x, y) in path:

                    if self.tiles[x][y].has_feature('road'):
                        self.set_road_tile(x, y)

                    for xx, yy in get_border_tiles(x, y):
                        if self.tiles[xx][yy].has_feature('road'):
                            self.set_road_tile(xx, yy)

        ## Now setup the economy since we have all import/export info
        for city in created_cities:
            mine_added = 0
            shrine_added = 0
            # This doesn't necessaryily have to be done here, but we should add farms around the city
            for x in xrange(city.x-5, city.x+6):
                for y in xrange(city.y-5, city.y+6):
                    # Try to add a mine somewhere near the city
                    if not mine_added and MOUNTAIN_HEIGHT-20 < self.tiles[x][y].height < MOUNTAIN_HEIGHT and self.is_valid_site(x=x, y=y, civ=city):
                        self.add_mine(x, y, city)
                        mine_added = 1
                        continue

                    # Add farms around the city
                    if get_distance_to(city.x, city.y, x, y) < 2.5 and self.is_valid_site(x, y, city):
                        self.add_farm(x, y, city)
                        continue
                    # Loop should only get here if no site is added, due to the continue syntax
                    if not shrine_added and self.is_valid_site(x=x, y=y, civ=city) and roll(1, 100) >= 97:
                        self.add_shrine(x, y, city)
                        shrine_added = 1

            ### v original real reason for this loop - I thought it would make sense to add farms and mines before the economy stuff
            city.prepare_native_economy()
            # Use the data to actually add agents to the city
        for city in created_cities:
            city.setup_native_economy()

        for city in created_cities:
            city.setup_imports()

        for city in created_cities:
            city.faction.create_faction_weapons()

        ## Make sure succession gets set up
        for faction in self.factions:
            faction.get_heirs(3)

        # For now, just add some ruins in some unused possible city slots
        for x, y in self.ideal_locs:
            if self.is_valid_site(x, y, None, MIN_SITE_DIST):
                self.add_ruins(x, y)


        # Each city gets a few bandits near it
        self.add_bandits(city_list=networked_cities, lnum=0, hnum=2, radius=10)



        # Some timing and debug info
        #game.add_message('Civs created in %.2f seconds' %(time.time() - begin))
        #game.add_message('%i dynasties so far...' %len(self.dynasties), libtcod.grey)

        render_handler.render_all()


    def refresh_road_network(self, cities):
        #for i, city in enumerate(networked_cities):
        #    for other_city in networked_cities[i+1:]:
        for city in cities:
            for other_city in [c for c in cities if c != city]:
                # Compute path to other
                road_path = libtcod.path_compute(self.road_path_map, city.x, city.y, other_city.x, other_city.y)
                # Walk through path and save as a list
                x = 1
                path_to_other_city = []

                while x != None:
                    x, y = libtcod.path_walk(self.road_path_map, True)

                    if x != None:
                        path_to_other_city.append((x, y))

                #other_city_path_to_us = path_to_other_city[:]
                #other_city_path_to_us.reverse()

                # Now we know how to get from one city to another
                city.path_to[other_city] = path_to_other_city
                #other_city.path_to[city] = other_city_path_to_us


    def find_closest_clumped_cities(self, clump1, clump2):
        ''' For 2 lists of cities, find the two closest ones '''
        cities = (None, None)
        dist = 10000

        for city in clump1:
            for ocity in clump2:
                road_path = libtcod.path_compute(self.path_map, city.x, city.y, ocity.x, ocity.y)
                ## Why the hell do you have to use the path map variable here?
                pdist = libtcod.path_size(self.path_map)

                if pdist < dist:
                    dist = pdist
                    cities = (city, ocity)

        return cities

    def add_bandits(self, city_list, lnum, hnum, radius):
        ''' Bandits will search for a suitable site to move into, or else they will build their own '''

        force_steal = 1
        for city in city_list:
            # Bandits may try to steal holy objects
            possible_obj_to_steal = None
            temple = city.get_building('Temple')
            for obj in self.famous_objects:
                if obj in temple.housed_objects:
                    possible_obj_to_steal = obj
                    break

            # Each city gets a certain number of nearby hideouts
            hideout_num = roll(lnum, hnum)

            # Build a list of possible sites to move into
            possible_sites = []
            for x in xrange(city.x-radius, city.x+radius):
                for y in xrange(city.y-radius, city.y+radius):
                    # Make sure there is a valid path to the city
                    if self.get_astar_distance_to(x, y, city.x, city.y) is not None:
                        # Add caves and ruins
                        possible_sites.extend(self.tiles[x][y].caves)
                        if self.tiles[x][y].site and self.tiles[x][y].site.site_type == 'ruins':
                            possible_sites.append(self.tiles[x][y].site)

            # Attempt to place them in existing sites
            while len(possible_sites) and hideout_num:
                possible_site = possible_sites.pop(roll(0, len(possible_sites)-1 ))

                if possible_site.faction is None:
                    ## Right now creating a dummy building. Eventually we won't need to do this, since sites will have their own buildings already present
                    possible_site.create_building(zone='residential', b_type='hideout', template='TEST', professions=[], inhabitants=[], tax_status=None)
                    leader, hideout_building = self.create_and_move_bandits_to_site(wx=possible_site.x, wy=possible_site.y, hideout_site=possible_site)

                    game.add_message('Bandits moving to %s'%possible_site.site_type, libtcod.dark_grey)

                    # For now, chance of stealing holy relic and taking it to the site
                    if possible_obj_to_steal and (roll(0, 1) or (force_steal and possible_site.site_type == 'cave')):
                        # Flip off flag so future steals are left to chance0
                        force_steal = 0

                        possible_obj_to_steal.set_current_owner(leader)
                        possible_obj_to_steal.set_current_building(hideout_building)
                        #game.add_message('%s, Bandit leader moved to %s and has stolen %s' %(leader.fullname(), possible_site.get_name(), possible_obj_to_steal.fullname()), libtcod.orange)
                        possible_obj_to_steal = None
                    else:
                        pass
                        #game.add_message('%s, Bandit leader moved to %s' %(leader.fullname(), possible_site.get_name()), libtcod.orange)

                    hideout_num -= 1

            # Otherwise, they can build their own little shacks
            for i in xrange(hideout_num):
                # Pick a good spot
                iter = 0
                while True:
                    iter += 1
                    if iter > 20:
                        print ' couldn\'t find good spot for bandits'
                        break
                    # Hideout is min 4 distance away
                    xd = roll(4, 8) * random.choice((-1, 1))
                    yd = roll(4, 8) * random.choice((-1, 1))
                    x, y = city.x + xd, city.y + yd
                    # If it's a valid spot, place the hideout
                    if self.is_val_xy((x, y)) and self.is_valid_site(x, y) and not self.tiles[x][y].has_feature('road') and self.get_astar_distance_to(city.x, city.y, x, y):
                        # Will add a hideout building here
                        self.create_and_move_bandits_to_site(wx=x, wy=y, hideout_site=None)
                        game.add_message('Bandits moving to their own site', libtcod.dark_grey)
                        break



    def run_history(self, weeks):
        ## Some history...
        #begin = time.time()
        for i in xrange(weeks * 7):
            time_cycle.day_tick(1)
        #game.add_message('History run in %.2f seconds' %(time.time() - begin))
        # List the count of site types
        game.add_message(', '.join(['{0} {1}s'.format(len(self.site_index[site_type]), site_type) for site_type in self.site_index.keys()]))


    def initialize_fov(self):
        ## Field of view / pathfinding modules
        self.fov_recompute = True

        self.fov_map = libtcod.map_new(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                libtcod.map_set_properties(self.fov_map, x, y, not self.tiles[x][y].blocks_vis, not self.tiles[x][y].blocks_mov)
        self.path_map = libtcod.path_new_using_map(self.fov_map)

        # New map that disallows diagonals - used for roads
        self.rook_path_map = libtcod.path_new_using_map(self.fov_map, 0.0)

        # Build FOV map - only roads are walkable here! (will refresh each time a road is built)
        self.road_fov_map = libtcod.map_new(self.width, self.height)

        for x in xrange(self.width):
            for y in xrange(self.height):
                #libtcod.map_set_properties(self.road_fov_map, x, y, 1, 'road' in self.tiles[x][y].features)
                libtcod.map_set_properties(self.road_fov_map, x, y, 1, 0)
        self.road_path_map = libtcod.path_new_using_map(self.road_fov_map)
    #libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)

    def display(self):
        ''' Display the world '''
        if game.world_map_display_type == 'normal':
            #buffer = libtcod.ConsoleBuffer(CAMERA_WIDTH, CAMERA_HEIGHT)

            for y in xrange(camera.height):
                for x in xrange(camera.width):
                    (wmap_x, wmap_y) = camera.cam2map(x, y)
                    libtcod.console_put_char_ex(map_con.con, x, y, self.tiles[wmap_x][wmap_y].char, self.tiles[wmap_x][wmap_y].char_color, self.tiles[wmap_x][wmap_y].color)
                    #bc = WORLD.tiles[wmap_x][wmap_y].color
                    #fc = WORLD.tiles[wmap_x][wmap_y].char_color
                    #buffer.set(x=x, y=y, back_r=WORLD.tiles[wmap_x][wmap_y].color.r, back_g=WORLD.tiles[wmap_x][wmap_y].color.g, back_b=WORLD.tiles[wmap_x][wmap_y].color.b, \
                    #            fore_r=WORLD.tiles[wmap_x][wmap_y].char_color.r, fore_g=WORLD.tiles[wmap_x][wmap_y].char_color.g, fore_b=WORLD.tiles[wmap_x][wmap_y].char_color.b, char=WORLD.tiles[wmap_x][wmap_y].char)

            #buffer.blit(con.con)

        elif game.world_map_display_type == 'culture':
            for y in xrange(camera.height):
                for x in xrange(camera.width):
                    (wmap_x, wmap_y) = camera.cam2map(x, y)
                    if self.tiles[wmap_x][wmap_y].culture is not None:
                        color = self.tiles[wmap_x][wmap_y].culture.color
                        #libtcod.console_put_char_ex(con.con, x, y, chr(178), color, WORLD.tiles[wmap_x][wmap_y].color)
                        libtcod.console_put_char_ex(map_con.con, x, y, chr(177), color, color * 1.2)

                    else:
                        libtcod.console_put_char_ex(map_con.con, x, y, self.tiles[wmap_x][wmap_y].char, self.tiles[wmap_x][wmap_y].char_color, self.tiles[wmap_x][wmap_y].color)

        ######################### Territories ##################################
        elif game.world_map_display_type == 'territory':
            for y in xrange(camera.height):
                for x in xrange(camera.width):
                    (wmap_x, wmap_y) = camera.cam2map(x, y)
                    if self.tiles[wmap_x][wmap_y].territory is not None:
                        color = self.tiles[wmap_x][wmap_y].territory.color
                        #libtcod.console_put_char_ex(con.con, x, y, chr(178), color, WORLD.tiles[wmap_x][wmap_y].color)
                        libtcod.console_put_char_ex(map_con.con, x, y, chr(177), color, color * 1.5)

                    else:
                        libtcod.console_put_char_ex(map_con.con, x, y, self.tiles[wmap_x][wmap_y].char, self.tiles[wmap_x][wmap_y].char_color, self.tiles[wmap_x][wmap_y].color)
        ######################### Resources ##################################
        elif game.world_map_display_type == 'resource':
            for y in xrange(camera.height):
                for x in xrange(camera.width):
                    (wmap_x, wmap_y) = camera.cam2map(x, y)
                    libtcod.console_put_char_ex(map_con.con, x, y, self.tiles[wmap_x][wmap_y].char, self.tiles[wmap_x][wmap_y].char_color, self.tiles[wmap_x][wmap_y].color)

                    if len(self.tiles[wmap_x][wmap_y].res.keys()) and not 'wood' in self.tiles[wmap_x][wmap_y].res.keys():
                        char = self.tiles[wmap_x][wmap_y].res.keys()[0][0].capitalize()
                        libtcod.console_put_char_ex(map_con.con, x, y, char, libtcod.green, libtcod.black)
        ###########################################################################

        self.draw_world_objects()
        #blit the contents of "con.con" to the root console
        map_con.blit()


    def is_valid_site(self, x, y, civ=None, min_dist=None):
        # Checks if site is a valid spot to build a city
        # Can't build if too close to another city, and if the territory alread belongs to someone else
        if min_dist is not None:
            for site in self.sites:
                if site.distance(x, y) < min_dist:
                    return False

        return not (self.tiles[x][y].blocks_mov) and (not self.tiles[x][y].site) and (self.tiles[x][y].territory is None or self.tiles[x][y].territory == civ)


    def closest_city(self, user, max_range, target_faction=None):
        closest_city = None
        closest_dist = max_range + 1  #start with (slightly more than) maximum range

        for city in self.cities:
            if target_faction == None or city.owner == target_faction:
                dist = self.get_astar_distance_to(user.x, user.y, city.x, city.y)
                if dist < closest_dist:  #it's closer, so remember it
                    closest_city = city
                    closest_dist = dist
        return closest_city


    def goto_scale_map(self):
        ''' Create battle map from player's world coords '''
        global M
        game.switch_map_scale(map_scale='human')

        x, y = player.wx, player.wy

        ## Set size of map
        if self.tiles[x][y].site and self.tiles[x][y].site.site_type == 'city':
            M = Wmap(world=self, wx=x, wy=y, width=CITY_MAP_WIDTH, height=CITY_MAP_HEIGHT)
        else:
            M = Wmap(world=self, wx=x, wy=y, width=MAP_WIDTH, height=MAP_HEIGHT)



        # Make map
        if self.tiles[x][y].site and self.tiles[x][y].site.site_type == 'city':
            hm = M.create_heightmap_from_surrounding_tiles(minh=1, maxh=4, iterations=20)
            base_color = self.tiles[x][y].get_base_color()
            M.create_map_tiles(hm, base_color, explored=1)

            M.make_city_map(city_class=self.tiles[x][y].site, num_nodes=22, min_dist=30, disorg=6)

        else:
            hm = M.create_heightmap_from_surrounding_tiles()
            base_color = self.tiles[x][y].get_base_color()
            M.create_map_tiles(hm, base_color, explored=1)



        M.run_cellular_automata(cfg=MCFG[self.tiles[x][y].region])
        M.add_minor_sites_to_map()

        if not self.tiles[x][y].site:
            M.add_world_features(x, y)

        ########### NATURE #################
        M.color_blocked_tiles(cfg=MCFG[self.tiles[x][y].region])
        M.add_vegetation(cfg=MCFG[self.tiles[x][y].region])
        M.set_initial_dmaps()

        M.add_sapients_from_world()

        camera.center(player.x, player.y)
        game.handle_fov_recompute()


    def make_cave_map(self, wx, wy, cave):
        global M

        base_color = libtcod.color_lerp(libtcod.darkest_grey, libtcod.darker_sepia, .5)

        cfg ={
             'initial_blocks_mov_chance':550,
             'repetitions':2,
             'walls_to_floor':3,
             'walls_to_wall':5,
             'blocks_mov_color':libtcod.darkest_grey,
             'blocks_mov_surface':'cave wall',
             'shade':1,
             'blocks_mov_height':189,

             'small_tree_chance':0,
             'small_stump_chance':0,
             'large_tree_chance':0,
             'large_stump_chance':0,
             'shrub_chance':10,
             'unique_ground_tiles':(()),
             'map_pad':6,
             'map_pad_type':1
             }


        width, height = 150, 150

        target_unfilled_cells = int(width*height/3)
        num_remaining_open_tiles = 0
        rejections = -1
        # Sometimes cellular automata will generate small pockets of unconnected regions; here we will ensure a certain amount of contiguous open cells
        while num_remaining_open_tiles < target_unfilled_cells:
            rejections += 1

            M = None
            M = Wmap(world=self, wx=wx, wy=wy, width=width, height=height)
            hm = M.create_and_vary_heightmap(initial_height=110, mborder=20, minr=20, maxr=35, minh=-6, maxh=8, iterations=50)
            M.create_map_tiles(hm=hm, base_color=base_color, explored=0)

            M.run_cellular_automata(cfg=cfg)

            ## Add some drunk walkers!
            dcfg = {'bias':None, 'color':base_color, 'empty_stop':False, 'tile_limit':1000}
            for i in xrange(5):
                walker = DrunkWalker(umap=M, x=roll(20, M.width-21), y=roll(20, M.height-21), cfg=dcfg)
                walker.drunk_walk()

            ### This step fills in every pocket of open ground that's not connected to the largest open pocket
            remaining_open_tiles, fill_counter = M.fill_open_pockets(target_unfilled_cells)
            num_remaining_open_tiles = len(remaining_open_tiles)

        game.add_message('%i rejections; filled %i openings' %(rejections, fill_counter), libtcod.dark_green)

        ############ Cave entrance - generated by drunk walker ######################
        entry_dict = {
                      'n':{'coords':(roll(10, M.width-11), 1), 'bias_dir':0},
                      'e':{'coords':(M.width-2, roll(10, M.height-11) ), 'bias_dir':3},
                      's':{'coords':(roll(10, M.width-11), M.height-2), 'bias_dir':2},
                      'w':{'coords':(1, roll(10, M.height-11) ), 'bias_dir':1}
                      }

        entry_dir = random.choice(entry_dict.keys())
        x, y = entry_dict[entry_dir]['coords']
        bias_dir = entry_dict[entry_dir]['bias_dir']

        dcfg = {'bias':(bias_dir, 200), 'color':base_color, 'empty_stop':True, 'tile_limit':-1}
        walker = DrunkWalker(umap=M, x=x, y=y, cfg=dcfg)
        walker.drunk_walk()
        ##############################################################################
        M.add_dmap(key='exit', target_nodes=[(x, y)], dmrange=5000)

        distance_from_exit = 100


        # Add each building to the cave
        for building in cave.buildings:
            # Pick a random area until one is not blocks_mov and at least distance_from_exit from the exit
            while 1:
                bx, by = roll(5, M.width-6), roll(5, M.height-6)
                if (not M.tile_blocks_mov(bx, by)) and M.dijmaps['exit'].dmap[bx][by] > distance_from_exit :

                    def do_fill(tile, building):
                        tile.building = building
                        tile.set_color(libtcod.color_lerp(tile.color, libtcod.grey, .1))

                    filled = floodfill(fmap=M, x=bx, y=by, do_fill=do_fill, do_fill_args=[building], is_border=lambda tile: tile.blocks_mov or tile.building, max_tiles=100)

                    for xx, yy in filled:
                        building.physical_property.append((xx, yy))
                    break

            # Add building garrisons
            for army in building.garrison:
                army.add_to_map(startrect=None, startbuilding=building, patrol_locations=[random.choice(building.physical_property)])

            # Finally add any housed objects to the map
            building.add_housed_objects_to_map()

        ########### NATURE #################
        M.color_blocked_tiles(cfg=cfg)
        M.add_vegetation(cfg=cfg)
        M.set_initial_dmaps()
        M.add_object_to_map(x=x, y=y, obj=player)

        ## DIJMAP
        M.cache_factions_for_dmap()
        ######################################

        M.initialize_fov()
        camera.center(player.x, player.y)
        game.handle_fov_recompute()

    def make_city(self, cx, cy, char, color, name, faction):
        # Make a city
        city = City(world=self, site_type='city', x=cx, y=cy, char=char, name=name, color=color, culture=self.tiles[cx][cy].culture, faction=faction)

        self.tiles[cx][cy].site = city
        self.make_world_road(cx, cy)

        self.sites.append(city)
        self.cities.append(city)

        return city

    def add_mine(self, x, y, city):
        name = '{0} mine'.format(city.name)
        mine = self.tiles[x][y].add_minor_site(world=self, site_type='mine', x=x, y=y, char='#', name=name, color=city.faction.color, culture=city.culture, faction=city.faction)
        mine.create_building(zone='residential', b_type='hideout', template='TEST', professions=[], inhabitants=[], tax_status=None)
        #self.tiles[x][y].char = "#"
        #self.tiles[x][y].char_color = city.faction.color
        return mine

    def add_farm(self, x, y, city):
        name = '{0} farm'.format(city.name)
        farm = self.tiles[x][y].add_minor_site(world=self, site_type='farm', x=x, y=y, char='#', name=name, color=city.faction.color, culture=city.culture, faction=city.faction)
        farm.create_building(zone='residential', b_type='hideout', template='TEST', professions=[], inhabitants=[], tax_status=None)
        #self.tiles[x][y].char = "#"
        #self.tiles[x][y].char_color = city.faction.color
        return farm

    def add_shrine(self, x, y, city):
        name = '{0} shrine'.format(city.culture.pantheon.name)
        shrine = self.tiles[x][y].add_minor_site(world=self, site_type='shrine', x=x, y=y, char='^', name=name, color=libtcod.black, culture=None, faction=None)
        shrine.create_building(zone='residential', b_type='hideout', template='TEST', professions=[], inhabitants=[], tax_status=None)
        self.tiles[x][y].char = "^"
        self.tiles[x][y].char_color = libtcod.black

        city.culture.pantheon.add_holy_site(shrine)

        return shrine

    def add_ruins(self, x, y):
        # Make ruins
        site_name = self.tiles[x][y].culture.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
        name = 'Ruins of {0}'.format(lang.spec_cap(site_name))

        ruin_site = self.tiles[x][y].add_minor_site(world=self, site_type='ruins', x=x, y=y, char=259, name=name, color=libtcod.black, culture=None, faction=None)
        self.tiles[x][y].char = 259
        self.tiles[x][y].char_color = libtcod.black
        for i in xrange(roll(1, 3)):
            building = ruin_site.create_building(zone='residential', b_type='hideout', template='TEST', professions=[], inhabitants=[], tax_status=None)

        # Move some unintelligent creatures in if it's near cities
        if 0 < self.get_astar_distance_to(x, y, self.site_index['city'][0].x, self.site_index['city'][0].y) < 45: #roll(0, 1):
            race_name = random.choice(self.brutish_races)
            name = '{0} raiders'.format(race_name)
            faction = Faction(leader_prefix='Chief', faction_name='{0}s of {1}'.format(race_name, site_name), color=libtcod.black, succession='strongman')
            culture = Culture(color=libtcod.black, language=random.choice(self.languages), world=self, races=[race_name])

            leader = culture.create_being(sex=1, born=time_cycle.years_ago(20, 45), char='u', dynasty=None, important=0, faction=faction, wx=x, wy=y, armed=1, save_being=1, intelligence_level=2)
            faction.set_leader(leader)

            sentients = {leader.sapient.culture:{leader.creature.creature_type:{'Swordsmen':10}}}
            self.create_population(char='u', name=name, faction=faction, creatures={}, sentients=sentients, goods={'food':1}, wx=x, wy=y, site=ruin_site, commander=leader)
            # Set the headquarters and update the title to the building last created.
            #building.add_garrison(army)
            if roll(1, 10) >= 2:
                closest_city = self.get_closest_city(x, y)[0]
                closest_city.culture.pantheon.add_holy_site(ruin_site)

        return ruin_site


    def add_cave(self, cx, cy, name):
        cave = Site(world=self, site_type='cave', x=cx, y=cy, char='#', name=name, color=libtcod.black)

        self.tiles[cx][cy].site = cave
        self.sites.append(cave)


    def create_and_move_bandits_to_site(self, wx, wy, hideout_site):
        ''' Creates a group of bandits to move to an uninhabited site '''

        closest_city = self.get_closest_city(wx, wy)[0]
        if closest_city is None:
            closest_city = random.choice(self.cities)
            print 'Bandits could not find closest city'

        bname = lang.spec_cap(closest_city.culture.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20)) + ' bandits')
        bandit_faction = Faction(leader_prefix='Bandit', faction_name=bname, color=libtcod.black, succession='strongman')

        # Make enemies with all other factions
        for faction in self.factions:
            if faction != bandit_faction:
                faction.set_enemy_faction(faction=bandit_faction)

        ## Choose building for site
        if hideout_site is None:
            hideout_site = self.tiles[wx][wy].add_minor_site(world=self, site_type='hideout', x=wx, y=wy, char='#', name='Hideout', color=libtcod.black, culture=closest_city.culture, faction=bandit_faction)
            hideout_building = hideout_site.create_building(zone='residential', b_type='hideout', template='TEST', professions=[], inhabitants=[], tax_status=None)
        else:
            hideout_building = random.choice(hideout_site.buildings)
        ##########################
        bandit_faction.set_headquarters(hideout_building)

        # Create a bandit leader from nearby city
        leader = closest_city.create_inhabitant(sex=1, born=time_cycle.years_ago(18, 35), char='o', dynasty=None, important=1, house=None)
        bandit_faction.set_leader(leader)
        # Set profession, weirdly enough
        profession = Profession(name='Bandit', category='bandit')
        profession.give_profession_to(figure=leader)
        profession.set_building(building=hideout_building)

        # Give him the house
        leader.sapient.change_citizenship(new_city=None, new_house=hideout_building)
        # Have him actually go there
        leader.w_teleport(wx, wy)

        sentients = {leader.sapient.culture:{leader.creature.creature_type:{'Bandit':10}}}
        self.create_population(char='u', name='Bandit band', faction=faction, creatures={}, sentients=sentients, goods={'food':1}, wx=wx, wy=wy, site=hideout_site, commander=leader)

        ## Prisoner
        #prisoner = closest_city.create_inhabitant(sex=1, born=time_cycle.current_year-roll(18, 35), char='o', dynasty=None, important=0, house=None)
        #bandits.add_captive(figure=prisoner)
        ############

        return leader, hideout_building


    def create_population(self, char, name, faction, creatures, sentients, goods, wx, wy, site=None, commander=None):
        population = Population(char, name, faction, creatures, sentients, goods, wx, wy, site, commander)

        return population


class DrunkWalker:
    def __init__(self, umap, x, y, cfg):
        self.umap = umap
        self.x = x
        self.y = y
        self.cfg = cfg

    def drunk_walk(self):
        x, y = self.x, self.y

        walked_tiles = []

        while 1:
            neighbors = get_border_tiles(x, y)

            # Chance of giving into the bias (if it exists), else, pick at random
            if self.cfg['bias'] and roll(1, 1000) < self.cfg['bias'][1]:
                xx, yy = neighbors[self.cfg['bias'][0]]
            else:
                xx, yy = random.choice(neighbors)
            # If the choice is valid, set the tile as unblocked
            if self.umap.is_val_xy((xx, yy)):
                # if blocked, unblock it
                if self.umap.tiles[xx][yy].blocks_mov and self.umap.tiles[xx][yy].height > WATER_HEIGHT:
                    self.umap.tiles[xx][yy].blocks_mov = 0
                    self.umap.tiles[xx][yy].blocks_vis = 0
                    self.umap.tiles[xx][yy].colorize(self.cfg['color'])
                    self.umap.tiles[xx][yy].surface = 'ground'

                    walked_tiles.append((xx, yy))

                # If config stops on first empty tile, this stops
                elif self.cfg['empty_stop'] and (not self.umap.tiles[xx][yy].blocks_mov) and (xx, yy) not in walked_tiles:
                    return walked_tiles
                # Refresh the x and y values
                x, y = xx, yy

            # Else handle tile limits
            if self.cfg['tile_limit'] > 0 and len(walked_tiles) >= self.cfg['tile_limit']:
                return walked_tiles


class Feature:
    def __init__(self, site_type, x, y):
        self.site_type = site_type
        self.x = x
        self.y = y
        self.name = None

    def set_name(self, name):
        self.name = name

    def get_name(self):
        if self.name:
            return self.name
        else:
            return self.site_type

class River(Feature):
    def __init__(self, x, y):
        self.site_type = 'river'
        self.x = x
        self.y = y
        self.name = None

        # Stores which directions the river is connected from
        self.connected_dirs = []

    def get_connected_dirs(self):
        return self.connected_dirs

    def add_connected_dir(self, direction):
        self.connected_dirs.append(direction)

class Site:
    def __init__(self, world, site_type, x, y, char, name, color, culture=None, faction=None, underground=0):
        self.world = world
        self.site_type = site_type
        self.x = x
        self.y = y
        self.underground = underground
        self.char = char
        self.name = name
        self.color = color

        self.culture = culture
        self.faction = faction
        if self.faction:
            self.faction.set_site(self)

        self.departing_merchants = []
        self.goods = {}
        self.caravans = []

        #structures
        self.buildings = []
        # major figures who are citizens
        self.citizens = []

        # Manage the world's dict of site types
        self.world.add_to_site_index(self)
        self.is_holy_site_to = []
        # For resources
        self.native_res = {}

        self.nearby_resources, self.nearby_resource_locations = self.world.find_nearby_resources(self.x, self.y, 6)

    def create_building(self, zone, b_type, template, professions, inhabitants, tax_status):
        building = Building(zone=zone, b_type=b_type, template=template, site=self, faction=self.faction, professions=professions, inhabitants=inhabitants, tax_status=tax_status, wx=self.x, wy=self.y)
        self.buildings.append(building)
        return building

    def get_name(self):
        if self.name:
            return self.name
        else:
            return self.site_type

    def create_inhabitant(self, sex, born, char, dynasty, important, race=None, armed=0, house=None):
        ''' Add an inhabitant to the site '''

        # First things first - if this happens to be a weird site without a culture, inherit the closest city's culture (and pretend it's our hometown)
        if self.culture is None:
            city = WORLD.get_closest_city(x=self.x, y=self.y, max_range=1000)[0]
            culture = city.culture
            hometown = city
        else:
            culture = self.culture
            hometown = self

        human = culture.create_being(sex=sex, born=born, char=char, dynasty=dynasty, important=important, faction=self.faction, wx=self.x, wy=self.y, armed=armed, race=race, save_being=1)

        # Make sure our new inhabitant has a house
        if house is None:
            house = self.create_building(zone='residential', b_type='house', template='TEST', professions=[], inhabitants=[human], tax_status='commoner')
        else:
            house.add_inhabitant(human)

        human.sapient.change_citizenship(new_city=self, new_house=house)
        human.sapient.hometown = hometown

        return human

    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def draw(self):
        #only show if it's visible to the player
        #if libtcod.map_is_in_fov(fov_map, self.x, self.y):
        (x, y) = camera.map2cam(self.x, self.y)

        if x is not None:
            #set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(map_con.con, self.color)
            #libtcod.console_set_default_background(con.con, self.color)
            libtcod.console_put_char(map_con.con, x, y, self.char, libtcod.BKGND_NONE)
            #libtcod.console_put_char_ex(con.con, x, y, self.char, libtcod.black, self.color)

    def clear(self):
        #erase the character that represents this object
        (x, y) = camera.map2cam(self.x, self.y)
        if x is not None:
            libtcod.console_put_char(map_con.con, x, y, ' ', libtcod.BKGND_NONE)


class City(Site):
    def __init__(self, world, site_type, x, y, char, name, color, culture, faction):
        ## Initialize site ##
        Site.__init__(self, world, site_type, x, y, char, name, color, culture, faction)

        self.connected_to = []
        self.path_to = {}

        self.war = []
        self.former_agents = []
        self.treasury = 500

        # For tracking how well food is being produced in the city
        self.food_supply = [0, 0, 0, 0, 0]
        self.food_demand = [0, 0, 0, 0, 0]
        self.granary_supply = [0, 0, 0, 0, 0]

        # Start with radius 3, gets immediately expanded to 4
        self.territory = []
        self.old_territory = [] # formerly owned tiles added here
        self.territory_radius = 1

        self.imports = {}
        self.exports = {}

        self.warehouses = {}
        self.warehouse_types = {}
        self.unique_warehouses = []
        for commodity_type, token_list in economy.COMMODITY_TYPES.iteritems():
            warehouse = Warehouse(name=commodity_type + ' warehouse', city=self, type_of_commodity=commodity_type,
                                  total_capacity=500)

            self.unique_warehouses.append(warehouse)
            # Be able to look up goods by type
            self.warehouse_types[commodity_type] = warehouse
            for token in token_list:
                self.warehouses[token.name] = warehouse

        # Add resources to the city, for the purposes of the economy
        for resource, amount in WORLD.tiles[self.x][self.y].res.iteritems():
            self.obtain_resource(resource, amount - 10)

        self.increase_radius()
        ## A package of buildings to start with
        self.setup_initial_buildings()


    def connect_to(self, other_city):
        self.connected_to.append(other_city)
        other_city.connected_to.append(self)

    def get_population(self):
        return (len(self.econ.resource_gatherers) * 100) + (len(self.econ.good_producers) * 20) + (
            len(self.econ.buy_merchants) * 20)

    def add_import(self, city, good):
        # Add other city as an importer if it's not already
        if not city in self.imports.keys():
            self.imports[city] = []
            # Add the good that is being imported
        self.imports[city].append(good)

    def add_export(self, city, good):
        # Add other city as an exporter if it's not already
        if not city in self.exports.keys():
            self.exports[city] = []
            # Add the good that is being exported
        self.exports[city].append(good)

    def remove_import(self, city, good):
        # Remove the import
        self.imports[city].remove(good)
        # And if we no longer import antything from them, remove from dict
        if self.imports[city] == []:
            del self.imports[city]

    def remove_export(self, city, good):
        # Remove the export
        self.exports[city].remove(good)
        # And if we no longer export antything to them, remove from dict
        if self.exports[city] == []:
            del self.exports[city]


    def prepare_native_economy(self):
        # Add economy to city
        self.econ = economy.Economy(native_resources=self.native_res.keys(), local_taxes=2, owner=self)

        self.resource_slots = {}
        for resource_type, amount in economy.CITY_RESOURCE_SLOTS.iteritems():
            for resource_class in economy.RESOURCE_TYPES[resource_type]:
                if resource_class.name in self.native_res.keys():
                    self.resource_slots[resource_class.name] = amount

        self.industry_slots = {}
        good_tokens_we_can_produce = economy.list_goods_from_strategic(self.native_res.keys())
        for good_type, amount in economy.CITY_INDUSTRY_SLOTS.iteritems():
            for good_class in economy.GOOD_TYPES[good_type]:
                if good_class.name in good_tokens_we_can_produce:
                    self.industry_slots[good_class.name] = amount


    def setup_native_economy(self):
        # Add gatherers and producers based on the slots allocated when we prepared the economy
        for resource, amount in self.resource_slots.iteritems():
            for i in xrange(amount):
                self.econ.add_resource_gatherer(resource)

        for good, amount in self.industry_slots.iteritems():
            for i in xrange(amount):
                self.econ.add_good_producer(good)

    def setup_imports(self):
        for city, import_list in self.imports.iteritems():

            for item in import_list:
                ## It's coming up with good in the import list...
                if item in economy.GOODS_BY_RESOURCE_TOKEN.keys():
                    ## Add merchants to the other city, who sell stuff in this city
                    city.create_merchant(sell_economy=self.econ, traded_item=item)
                    city.create_merchant(sell_economy=self.econ, traded_item=item)
                    ## Add extra resource gatherers in the other city
                    city.econ.add_resource_gatherer(item)
                    city.econ.add_resource_gatherer(item)
                    #city.econ.add_resource_gatherer(item)
                    #city.econ.add_resource_gatherer(item)

                    ## Add some specialists who can now make use of the imported goods
                    good_tokens_this_resource_can_produce = economy.list_goods_from_strategic([item])
                    for good in good_tokens_this_resource_can_produce:
                        self.econ.add_good_producer(good)
                        self.econ.add_good_producer(good)

                        # Other city too!
                        city.econ.add_good_producer(good)
                        city.econ.add_good_producer(good)
                        city.econ.add_good_producer(good)
                        city.econ.add_good_producer(good)

                    ## Add some merchants who will sell whatever good is created from those resources
                    if item in economy.GOODS_BY_RESOURCE_TOKEN.keys():
                        for good_class in economy.GOODS_BY_RESOURCE_TOKEN[item]:
                            city.create_merchant(sell_economy=self.econ, traded_item=good_class.name)
                            city.create_merchant(sell_economy=self.econ, traded_item=good_class.name)
                            #city.create_merchant(sell_economy=self.econ, traded_item=good_class.name)
                            #city.create_merchant(sell_economy=self.econ, traded_item=good_class.name)
                            self.add_import(city, good_class.name)
                            city.add_export(self, good_class.name)


    def build_road_to(self, x, y, color=libtcod.darkest_sepia):
        road_path = libtcod.path_compute(WORLD.rook_path_map, self.x, self.y, x, y)

        x, y = self.x, self.y
        old_x, old_y = None, None
        while x != None:
            # Update the road path map to include this road
            libtcod.map_set_properties(WORLD.road_fov_map, x, y, 1, 1)

            if old_x:
                road_count = 0
                for xx, yy in ( (old_x + 1, old_y), (old_x - 1, old_y), (old_x, old_y + 1), (old_x, old_y - 1) ):
                    if WORLD.tiles[xx][yy].has_feature('road'):
                        road_count += 1

                if road_count <= 3 :
                    WORLD.make_world_road(old_x, old_y)
            old_x, old_y = x, y
            x, y = libtcod.path_walk(WORLD.rook_path_map, True)

    def create_merchant(self, sell_economy, traded_item):
        ## Create a human to attach an economic agent to
        human = self.create_inhabitant(sex=1, born=time_cycle.years_ago(20, 60), char='o', dynasty=None, important=0, house=None)
        human.set_world_brain(BasicWorldBrain())

        ## Actually give profession to the person ##
        market = self.get_building('Market')
        market.add_profession(Profession(name=traded_item + ' Merchant', category='merchant'))
        market.professions[-1].give_profession_to(human)

        merchant = self.econ.add_merchant(sell_economy=sell_economy, traded_item=traded_item, attached_to=human)
        location = merchant.current_location.owner

        # A bit of a hack to make sure the merchant starts in the appropriate city
        if location != self:
            # Send him off
            market.remove_worker(human)
            # Teleport the merchant to the other location
            human.w_teleport(location.x, location.y)
            location.get_building('Market').add_worker(human)

        ## Now add the caravan to a list
        #caravan_goods = Counter(merchant.buy_inventory)
        sentients = {self.culture:{random.choice(self.culture.races):{'Caravan Guard':20}}}
        WORLD.create_population(char='M', name=self.name + ' caravan', faction=self.faction, creatures={}, sentients=sentients, goods={}, wx=self.x, wy=self.y, commander=human)

        self.caravans.append(human)

    def dispatch_caravans(self):
        market = self.get_building('Market')

        for caravan_leader, destination in self.departing_merchants:
            for figure in caravan_leader.sapient.commanded_figures:
                if figure in market.current_workers:
                    market.remove_worker(figure)
                else:
                    game.add_message('{0} tried to dispatch with the caravan but was not in {1}\'s list of figures'.format(figure.fulltitle(), self.name), DEBUG_MSG_COLOR)

            # Remove from city's list of caravans
            if caravan_leader in self.caravans:
                self.caravans.remove(caravan_leader)
            # Add back to civ, world, and region armies
            #WORLD.travelers.append(caravan_leader)
            # WORLD.tiles[self.x][self.y].entities.append(caravan_leader)
            caravan_leader.world_brain.next_tick = time_cycle.next_day()
            # Tell the ai where to go
            #caravan_leader.world_brain.set_destination(origin=self, destination=destination)
            caravan_leader.world_brain.add_goal(priority=1, goal_type='move_trade_goods_to_city', reason='I need to make a living you know', target_city=destination)

        self.departing_merchants = []

    def receive_caravan(self, caravan_leader):
        market = self.get_building('Market')

        # Unload the goods
        if self.econ == caravan_leader.sapient.economy_agent.sell_economy:
            unloaded = 0
            for i in xrange(caravan_leader.sapient.economy_agent.travel_inventory.count(caravan_leader.sapient.economy_agent.traded_item)):
                caravan_leader.sapient.economy_agent.travel_inventory.remove(caravan_leader.sapient.economy_agent.traded_item)
                caravan_leader.sapient.economy_agent.sell_inventory.append(caravan_leader.sapient.economy_agent.traded_item)
                unloaded = 1
            if unloaded:
                game.add_message('{0} unloaded {1} {2} in {3}'.format(caravan_leader.fulltitle(), i, caravan_leader.sapient.economy_agent.traded_item, self.name), libtcod.darker_green)
            else:
                game.add_message('{0} had no {1} to unload in {2}'.format(caravan_leader.fulltitle(), caravan_leader.sapient.economy_agent.traded_item, self.name), libtcod.darker_red)

        # Add workers to the market
        for figure in caravan_leader.sapient.commanded_figures + [caravan_leader]:
            if figure.sapient.economy_agent:
                figure.sapient.economy_agent.current_location = self.econ
                market.add_worker(figure)

                ## cheap trick for now - add a little of the resource to the city stockpile
                if figure.sapient.economy_agent.traded_item in economy.GOODS_BY_RESOURCE_TOKEN.keys():
                    self.warehouses[figure.sapient.economy_agent.traded_item].add(figure.sapient.economy_agent.traded_item, 2)
        #WORLD.tiles[caravan_leader.wx][caravan_leader.wy].entities.remove(caravan_leader)
        #WORLD.travelers.remove(caravan_leader)
        self.caravans.append(caravan_leader)

    def increase_radius(self):
        # Increase the territory held by the city
        self.territory_radius += 1
        for x in range(self.x - self.territory_radius, self.x + self.territory_radius + 1):
            for y in range(self.y - self.territory_radius, self.y + self.territory_radius + 1):
                if in_circle(center_x=self.x, center_y=self.y, radius=self.territory_radius, x=x, y=y) and not WORLD.tiles[x][y].blocks_mov:
                    if WORLD.tiles[x][y].territory is None:
                        WORLD.tiles[x][y].territory = self
                        self.territory.append((x, y))

                    if WORLD.tiles[x][y].culture is None:
                        WORLD.tiles[x][y].culture = self.culture

                elif WORLD.tiles[x][y].territory != self and self.distance(x, y) < 2:
                    self.acquire_tile(x, y)

    def obtain_resource(self, resource, amount):
        if resource not in self.native_res.keys():
            self.native_res[resource] = amount

    def acquire_tile(self, x, y):
        # acquire a single tile for the city
        if WORLD.tiles[x][y].culture is None:
            WORLD.tiles[x][y].culture = self.culture

        if WORLD.tiles[x][y].territory is not None:
            # If owned, add to civ/city's memory of territory, and remove from actual territory
            oldcity = WORLD.tiles[x][y].territory

            oldcity.old_territory.append((x, y))
            oldcity.territory.remove((x, y))

        WORLD.tiles[x][y].territory = self
        if (x, y) not in self.territory:
            self.territory.append((x, y))

    def abandon_site(self):
        if self in self.owner.cities:
            self.owner.cities.remove(self)
            #Collapse the civ if this was the last city
        if len(self.owner.cities) == 0:
            self.owner.collapse()

        WORLD.cities.remove(self)
        self.owner = None

        self.color = libtcod.dark_grey
        self.name = self.name + ' (abandoned)'
        # Clear up the territory, and save info about the territory it used to own
        for (x, y) in self.territory:
            WORLD.tiles[x][y].territory = None
            self.old_territory.append((x, y))
        self.territory = []

    def setup_initial_buildings(self):
        """Start the city off with some initial buildings"""
        city_hall_professions = [Profession(name='Scribe', category='commoner'),
                                 Profession(name='Scribe', category='commoner'),
                                 Profession(name='General', category='noble'),
                                 Profession(name='Tax Collector', category='commoner'),
                                 Profession(name='Spymaster', category='commoner'),
                                 Profession(name='Vizier', category='noble'),
                                 Profession(name='Militia Captain', category='commoner')]
        self.create_building(zone='municipal', b_type='City Hall', template='TEST', professions=city_hall_professions, inhabitants=[], tax_status='noble')

        temple_professions = [Profession(name='High Priest', category='religion')]
        self.create_building(zone='municipal', b_type='Temple', template='TEST', professions=temple_professions, inhabitants=[], tax_status='religious')

        market_professions = []
        self.create_building(zone='market', b_type='Market', template='TEST', professions=market_professions, inhabitants=[], tax_status='general')

        # Some nobles and estates
        #for i in xrange(roll(2, 4)):
        #    estate_professions = [Profession(name='Noble', category='noble')]
        #    self.create_building(name='Estate', professions=estate_professions, tax_status='noble')

        for i in xrange(roll(4, 6)):
            if roll(0, 1):
                tavern_professions = [Profession(name='Tavern Keeper', category='commoner'),
                                      Profession(name='Assassin', category='commoner')]
            else:
                tavern_professions = [Profession(name='Tavern Keeper', category='commoner')]

            self.create_building(zone='commercial', b_type='Tavern', template='TEST', professions=tavern_professions, inhabitants=[], tax_status='commoner')

        ######### Fill positions #########
        for building in self.buildings:
            building.fill_initial_positions()


    def create_initial_dynasty(self, wife_is_new_dynasty=0):
        ''' Spits out a dynasty or two, used for a quick setup type thing '''
        # Create's a dynasty for the leader and his wife
        new_dynasty = Dynasty(lang.spec_cap(random.choice(self.culture.language.vocab_n.values())), race=random.choice(self.culture.races))

        if wife_is_new_dynasty:
            wife_dynasty = Dynasty(lang.spec_cap(random.choice(self.culture.language.vocab_n.values())), race=new_dynasty.race)
        else:
            wife_dynasty = None

        leader = self.create_inhabitant(sex=1, born=time_cycle.years_ago(28, 40), char='o', dynasty=new_dynasty, important=1, race=new_dynasty.race, house=None)
        wife = self.create_inhabitant(sex=0, born=time_cycle.years_ago(28, 35), char='o', dynasty=wife_dynasty, important=1, race=new_dynasty.race, house=leader.sapient.house)
        # Make sure wife takes husband's name
        wife.sapient.lastname = new_dynasty.lastname

        leader.sapient.spouse = wife
        wife.sapient.spouse = leader

        all_new_figures = [leader, wife]


        # Leader's siblings
        leader_siblings = []
        for i in xrange(roll(0, 3)):
            sex = roll(0, 1)
            sibling = self.create_inhabitant(sex=sex, born=leader.sapient.born + roll(-8, 8), char='o', dynasty=new_dynasty,
                                             race=new_dynasty.race, important=1, house=None)
            leader_siblings.append(sibling)
            all_new_figures.append(sibling)

        # Wife's siblings
        if wife_is_new_dynasty:
            wife_siblings = []
            for i in xrange(roll(0, 3)):
                sex = roll(0, 1)
                sibling = self.create_inhabitant(sex=sex, born=wife.sapient.born + roll(8, 8), char='o',
                                                 dynasty=wife_dynasty, race=new_dynasty.race, important=1, house=None)
                wife_siblings.append(sibling)
                all_new_figures.append(sibling)

            wife.sapient.siblings = wife_siblings
            for sibling in wife_siblings:
                sibling.sapient.siblings.append(wife)

        # children
        children = []
        for i in xrange(roll(1, 3)):
            sex = roll(0, 1)
            child = self.create_inhabitant(sex=sex, born=time_cycle.years_ago(1, 10), char='o', dynasty=new_dynasty,
                                           race=new_dynasty.race, important=1, house=leader.sapient.house)
            children.append(child)
            all_new_figures.append(child)

        leader.sapient.siblings = leader_siblings
        for sibling in leader_siblings:
            sibling.sapient.siblings.append(leader)

        leader.sapient.children = children
        wife.sapient.children = children

        for child in children:
            child.sapient.mother = wife
            child.sapient.father = leader
            for other_child in children:
                if other_child != child and other_child not in child.sapient.siblings:
                    child.sapient.siblings.append(other_child)

        return leader, all_new_figures


    def get_building(self, building_name):
        for building in self.buildings:
            if building.name == building_name:
                return building

    def get_building_type(self, building_type):
        return [building for building in self.buildings if building.b_type == building_type]


    def get_available_materials(self):
        available_materials = []
        for material in self.native_res.keys():
            available_materials.append(material)

        for import_list in self.imports.values():
            for material in import_list:
                if material not in available_materials:
                    available_materials.append(material)

        return available_materials


class Warehouse:
    def __init__(self, name, city, type_of_commodity, total_capacity):
        self.name = name
        self.city = city
        self.total_capacity = total_capacity

        self.in_history = [0, 0, 0, 0, 0]
        self.out_history = [0, 0, 0, 0, 0]

        self.stockpile = {}
        for token in economy.COMMODITY_TYPES[type_of_commodity]:
            self.stockpile[token.name] = 0

    def add(self, commodity, amount):
        if sum(self.stockpile.values()) + amount <= self.total_capacity:
            self.stockpile[commodity] += amount

    def remove(self, commodity, amount):
        if self.stockpile[commodity] - amount >= 0:
            self.stockpile[commodity] -= amount



class Building:
    '''A building'''

    def __init__(self, zone, b_type, template, site, faction, professions, inhabitants, tax_status, wx, wy):
        self.zone = zone
        self.template = template
        self.b_type = b_type
        self.name = b_type

        self.site = site
        self.faction = faction
        self.wx = wx
        self.wy = wy

        self.professions = []
        self.inhabitants = []
        self.tax_staus = tax_status

        for profession in professions:
            self.add_profession(profession)

        for inhabitant in inhabitants:
            self.add_inhabitant(inhabitant)

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


    def add_garrison(self, army):
        self.garrison.append(army)
        army.garrisoned = self

    def remove_garrison(self, army):
        self.garrison.remove(army)
        army.garrisoned = None

    def add_inhabitant(self, inhabitant):
        inhabitant.sapient.house = self
        self.inhabitants.append(inhabitant)

    def remove_inhabitant(self, figure):
        figure.sapient.house = None
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
            # First choose a tile that is not blocks_mov
        while 1:
            x, y = random.choice(self.physical_property)
            if not M.tiles[x][y].blocks_mov:
                break

        M.add_object_to_map(x=x, y=y, obj=obj)


    def set_name(self):
        if self.b_type == 'Tavern':
            num = roll(1, 3)
            if num == 1:
                front = 'The ' + random.choice(TAVERN_ADJECTIVES) + ' ' + random.choice(TAVERN_NOUNS)
                ending = random.choice(['', '', '', ' Inn', ' Tavern', ' Lodge', ' Bar and Inn'])
            elif num == 2:
                front = 'The ' + random.choice(TAVERN_NOUNS) + '\'s ' + random.choice(TAVERN_OBJECTS)
                ending = ''
            elif num == 3:
                front = self.site.name + '\'s ' + random.choice(TAVERN_OBJECTS)
                ending = ''

            self.name = front + ending

    def get_name(self):
        return self.name

    def add_worker(self, worker):
        self.current_workers.append(worker)
        worker.sapient.profession.current_work_building = self

    def remove_worker(self, worker):
        self.current_workers.remove(worker)
        worker.sapient.profession.current_work_building = None

    def add_profession(self, profession):
        profession.building = self
        profession.current_work_building = self
        self.professions.append(profession)

    def fill_position(self, profession):
        # Give temples and nobles and stuff an initial dynasty to begin with
        potential_employees = [figure for figure in WORLD.tiles[self.site.x][self.site.y].entities if
                               figure.sapient.profession == None and figure.creature.sex == 1 and figure.sapient.get_age() > MIN_MARRIAGE_AGE]
        if profession.name in ('High Priest', 'General'):
            # Check if we have people available to fill the position
            if roll(1, 3) >= 3 and len(potential_employees) > 0:
                human = random.choice(potential_employees)
                all_new_figures = [human]
            # Or, chance of creating new dynasty
            else:
                human, all_new_figures = self.site.create_initial_dynasty()


        else:
            # Mostly try to use existing folks to fill the position
            if not profession.name in ('Assassin') and roll(1, 4) >= 2 and len(potential_employees) > 0:
                human = random.choice(potential_employees)
                all_new_figures = [human]
            # Otherwise, create a new person
            else:
                human = self.site.create_inhabitant(sex=1, born=time_cycle.years_ago(18, 40), char='o', dynasty=None, important=0, house=None)
                all_new_figures = [human]

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
                M.tiles[q][r].building = self
                self.physical_property.append((q, r))
                ## Add wall or floor
                if q in [building_center[0], building_center[0] + building_size[0]] or r in [building_center[1], building_center[1] + building_size[1]]:
                    M.tiles[q][r].make_wall(libtcod.darkest_grey)
                else:
                    M.tiles[q][r].make_floor(floor_type='dirt')

        door_coords = (int(building_center[0] + (building_size[0] / 2)), building_center[1] + building_size[1])

        M.make_door(x=door_coords[0], y=door_coords[1], floor_type='dirt')
        '''
        bx, by = building_center[0], building_center[1]
        for i, row in enumerate(building_templates.buildings[self.template]):
            for j, tile in enumerate(row):
                x, y = bx+j, by+i
                self.physical_property.append((x, y))

                if tile == '#':
                    M.tiles[x][y].make_wall(libtcod.darkest_grey)
                elif tile == ' ':
                    M.tiles[x][y].make_floor(floor_type='stone')
                elif tile in ('d', '-'):
                    M.make_door(x=x, y=y, floor_type='stone')


    def add_building_from_rect_lot(self, rect, building_color, floor, door_dir):

        w, h = rect.x2-rect.x1, rect.y2-rect.y1
        if (w, h) in building_templates.buildings['houses'].keys():

            bx, by = rect.x1, rect.y1
            template = random.choice(building_templates.buildings['houses'][(w, h)])
            for i, row in enumerate(template):
                for j, tile in enumerate(row):
                    x, y = bx+j, by+i
                    self.physical_property.append((x, y))

                    if tile == '#':
                        M.tiles[x][y].make_wall(libtcod.darkest_sepia)
                    elif tile == ' ':
                        M.tiles[x][y].make_floor(floor_type='dirt')
                    elif tile in ('d', '-'):
                        M.make_door(x=x, y=y, floor_type='dirt')

        else:
            for x in xrange(rect.x1, rect.x2 + 1):
                for y in xrange(rect.y1, rect.y2 + 1):
                    self.physical_property.append((x, y))
                    self.usemap.tiles[x][y].building = self

                    if x in (rect.x1, rect.x2) or y in (rect.y1, rect.y2):
                        self.usemap.tiles[x][y].make_wall(building_color)
                    else:
                        self.usemap.tiles[x][y].make_floor(floor_type=floor)


    def create_door_and_outside_road(self, rect, door_dir):
        pass


class Profession:
    '''A profession for historical figures to have'''

    def __init__(self, name, category):
        self.name = name
        self.category = category

        self.holder = None
        self.building = None
        # This was mostly created due to merchants, who can be at work on one of two markets
        # This means the self.building is not sufficient. Might be able to drop self.building entirely?
        self.current_work_building = None

    def set_building(self, building):
        self.building = building
        self.current_work_building = building

    def set_current_work_building(self, building):
        self.current_work_building = building

    def give_profession_to(self, figure):
        # Remove current holder from buildings, and the profession
        if self.holder:
            game.add_message(figure.fullname() + ' is now ' + self.name + ' in ' + self.building.site.name + ' (formerly ' + self.holder.fullname() + ')', libtcod.light_green)
            if self.current_work_building:
                self.current_work_building.remove_worker(self.holder)
            self.holder.sapient.profession.remove_profession_from(self.holder)

        figure.sapient.profession = self
        self.holder = figure
        # Has to be done afterward, so the profession's current building can be set
        if self.current_work_building:
            self.current_work_building.add_worker(figure)

        figure.sapient.set_opinions()

    def remove_profession_from(self, figure):
        figure.sapient.profession = None
        self.holder = None
        figure.sapient.set_opinions()



class Faction:
    def __init__(self, leader_prefix, faction_name, color, succession):
        self.leader_prefix = leader_prefix # What the person will be referred to as, "Mayor" "governor" etc
        self.faction_name = faction_name
        self.color = color

        self.leader = None
        # Eventually will be more precide? Just a way to keep track of when the current leader became leader
        self.leader_change_year = time_cycle.current_year
        # So far:
        # 'dynasty' for a city type faction
        # 'strongman' for bandit factions
        self.succession = succession
        self.heirs = []

        self.faction_leader = None
        self.headquarters = None

        WORLD.factions.append(self)

        # Information about ranking
        self.parent = None
        self.subfactions = []
        self.members = []

        self.weapons = []

        self.faction_relations = {}
        # Factions whom we would openly fight
        self.enemy_factions = set([])

    def set_enemy_faction(self, faction):
        self.enemy_factions.add(faction)
        faction.enemy_factions.add(self)

    def unset_enemy_faction(self, faction):
        self.ememy_factions.remove(faction)
        faction.enemy_factions.remove(self)

    def set_headquarters(self, building):
        self.headquarters = building

        self.headquarters.faction = self

        if self.headquarters.site and self.headquarters.site.faction is None:
            self.headquarters.site.faction = self

    def set_site(self, site):
        self.site = site

        if self.site.faction is None:
            self.site.faction = self

    def add_member(self, figure):
        figure.sapient.faction = self
        figure.set_color(self.color)

        self.members.append(figure)

    def remove_member(self, figure):
        figure.sapient.faction = None
        self.members.remove(figure)

    def set_leader(self, leader):
        if self.leader:
            self.leader.sapient.unset_as_faction_leader(self)
        # Now install new leader
        self.leader = leader
        self.leader.sapient.set_as_faction_leader(self)
        # Keep track of when leader became leader
        self.leader_change_year = time_cycle.current_year

    def get_leader(self):
        return self.leader


    def modify_faction_relations(self, faction, reason, amount):
        if faction in self.faction_relations.keys():
            if reason in self.faction_relations[faction].keys():
                self.faction_relations[faction][reason] += amount

            elif reason not in self.faction_relations[faction].keys():
                self.faction_relations[faction][reason] = amount

        elif faction not in self.faction_relations.keys():
            self.faction_relations[faction] = {reason:amount}

    def get_faction_relations(self, other_faction):

        reasons = {}

        if other_faction in self.faction_relations.keys():
            for reason, amount in self.faction_relations[other_faction]:
                reasons[reason] = amount

        # Culture
        if other_faction.get_leader().sapient.culture != self.get_leader().sapient.culture:
            reasons['Different culture'] = -10

        if other_faction in self.subfactions or self in other_faction.subfactions:
            reasons['Same political entity'] = 10

        return reasons

    def set_subfaction(self, other_faction):
        # Adds another title as vassal
        other_faction.parent = self
        self.subfactions.append(other_faction)



    def standard_succession(self):
        ''' Leadership will pass to the firstborn son of the current holder.
        If none, it will pass to the oldest member of the dynasty'''
        if self.heirs != []:
            heir = self.heirs.pop(0)
            # Now that they're in the new position, remove them from the list of heirs
            self.unset_heir(heir)
            self.set_leader(heir)
            game.add_message('{0} has is now {1} of {2}'.format(heir.fullname(), self.leader_prefix, self.faction_name))
            # Re-calculate succession
            self.get_heirs(3)

        # Not sure if title should immediately pass onto someone, or have None be a valid holder for the title
        # while others fight it out.
        else:
            game.add_message('{0} now has no heir!'.format(self.faction_name))


    def set_heir(self, heir, number_in_line):
        self.heirs.append(heir)
        heir.sapient.inheritance[self] = number_in_line

    def unset_heir(self, heir):
        assert self in heir.sapient.inheritance.keys(), '%s not in %s\'s inheritance' %(self.faction_name, heir.fulltitle())
        del heir.sapient.inheritance[self]

    def get_heirs(self, number):
        # First, make sure to clear the knowledge of inheritance from all heirs
        for heir in self.heirs:
            self.unset_heir(heir)

        if self.leader and self.succession == 'dynasty':
            self.heirs = []

            child_heirs = [child for child in self.leader.sapient.children if child.creature.sex == 1 and not child.creature.status == 'dead']
            child_heirs = sorted(child_heirs, key=lambda child: child.sapient.born)
            ## Look at other heirs - make sure it does not include the title holder himself or his children, since they're already accounted for
            if self.leader.sapient.dynasty is not None:
                other_heirs = [member for member in self.leader.sapient.dynasty.members if member.creature.sex == 1 and member != self.leader and member not in child_heirs and not member.creature.status == 'dead']
                other_heirs = sorted(other_heirs, key=lambda member: member.sapient.born)

            else:
                print 'BUG:', self.leader.fullname(), ' has no dynasty'
                other_heirs = []
            # Child heirs will be given priority
            merged_list = child_heirs + other_heirs

            for i, heir in enumerate(merged_list[:number]):
                self.set_heir(heir=heir, number_in_line=i+1)

            return merged_list[:number]


        elif self.leader and self.succession == 'strongman':
            self.heirs = []

            heir = random.choice(self.members)
            if heir is None:
                heir = self.headquarters.site.culture.create_being(sex=1, born=time_cycle.years_ago(20, 45), char='o', dynasty=None,
                                                                   important=0, faction=self, wx=self.headquarters.site.x, wy=self.headquarters.site.y, armed=1, save_being=1)
                self.set_heir(heir=heir, number_in_line=1)

            return [heir]

        else:
            print self.faction_name, 'was queried for heirs but has no holder'
            return []




    def create_faction_weapons(self):
        ''' Culturally specific weapons '''

        weapon_types = phys.blueprint_dict.keys()
        #materials = self.site.get_available_materials()
        ## TODO - check union of weapon materials/available materials
        materials = ('iron', 'copper', 'bronze')

        ''' Create a few types of unique weapons for this culture '''
        for wtype in weapon_types:
            material_name = random.choice(materials)
            material = phys.materials[material_name]

            special_properties = {random.choice(phys.PROPERTIES): random.choice( (5, 10) ) }

            # Send it over to the item generator to generate the weapon
            weapon_info_dict = phys.wgenerator.generate_weapon(wtype=wtype, material=material, special_properties=special_properties)

            weapon_name = self.site.culture.gen_word(syllables=roll(1, 2), num_phonemes=(2, 8))

            name = '%s %s' %(weapon_name, wtype)
            weapon_info_dict['name'] = name

            # Finally, append to list of object dicts
            self.weapons.append(name)

            phys.object_dict[name] = weapon_info_dict


class HistoricalEvent():
    def __init__(self, date, location, characters, related_buildings, related_sites):
        pass

class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (int(round(center_x)), int(round(center_y)))

    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

    def expand(self, dx, dy):
        if dx > 0:
            self.x2 += dx
        elif dx < 0:
            self.x1 += dx

        if dy > 0:
            self.y2 += dy
        elif dy < 0:
            self.y1 += dy

    def get_size(self):
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def get_dimensions(self):
        return self.x2 - self.x1, self.y2 - self.y1

    def middle_point(self, side):
        if side == 'n':
            return int(round((self.x1 + self.x2) / 2)), self.y1
        elif side == 's':
            return int(round((self.x1 + self.x2) / 2)), self.y2
        elif side == 'e':
            return self.x2, int(round((self.y1 + self.y2) / 2))
        elif side == 'w':
            return self.x1, int(round((self.y1 + self.y2) / 2))


## The object itself is basically a list of components
class Object:
    def __init__(self, name, char, color, components, blocks_mov, blocks_vis, description,
                 creature=None, sapient=None, local_brain=None, world_brain=None,
                 weapon=None, wearable=None,
                 x=None, y=None, wx=None, wy=None):

        self.name = name
        self.char = char

        self.set_color(color)

        ## (Physical) components of the object; and then run a routine to put them all together
        self.components = components
        self.set_initial_attachments()
        # blocks = block pathing, blocks_vis = blocks vision
        self.blocks_mov = blocks_mov
        self.blocks_vis = blocks_vis

        self.description = description

        self.creature = creature
        if self.creature:  #let the creature component know who owns it
            self.creature.owner = self

        self.sapient = sapient
        if self.sapient:
            self.sapient.owner = self

        # For the local map
        self.set_local_brain(local_brain)
        # For the world map
        self.set_world_brain(world_brain)

        # If this thing was designed as a weapon, this flag keeps track of it
        self.weapon = weapon

        self.wearing = []
        self.wearable = wearable
        self.being_worn = 0

        # x and y coords in battle-map game world
        self.x = x
        self.y = y
        # x and y coords in overworld map
        self.wx = wx
        self.wy = wy
        self.world_last_dir = (0, 0)

        # Will be set to an interact_obj class instance if used
        self.interactable = 0

        #self.momentum = 0
        #self.height = 1.6

        # The being that owns the object - will probably be the last to touch it?
        self.current_owner = None
        # Building that the object is currently in
        self.current_building = None
        # If the object is currently on someone's person
        self.current_holder = None


        self.inside = None  # Keeps track of objects we're inside of
        self.being_grasped_by = None # body part grasping it


        self.cached_astar_path = None

    def set_local_brain(self, brain):
        self.local_brain = brain
        if self.local_brain:  #let the AI component know who owns it
            self.local_brain.owner = self

    def set_world_brain(self, brain):
        self.world_brain = brain
        if self.world_brain:  #let the AI component know who owns it
            self.world_brain.owner = self


    def set_color(self, color):
        self.color = color
        # Color which gets displayed:
        self.display_color = color
        self.shadow_color = self.color * .5
        # Set special colors for different states of the object
        self.pass_out_color = libtcod.color_lerp(self.color, libtcod.black, .5)
        self.death_color = libtcod.black


    def set_current_owner(self, figure):
        ''' Sets someone as the owner of an object (must run set_current_holder to make sure they're carrying it)'''
        ## Remove from current owner
        if self.current_owner:
            self.current_owner.sapient.possessions.remove(self)
            self.current_owner.sapient.former_possessions.add(self)

            #game.add_message('%s has taken possession of %s from %s' %(figure.fullname(), self.fullname(), self.current_owner.fullname()), libtcod.orange)
        else:
            pass
            #game.add_message('%s has taken possession of %s' %(figure.fullname(), self.fullname()), libtcod.orange)

        ## Give to new owner
        self.current_owner = figure
        figure.sapient.possessions.add(self)


    def clear_current_owner(self):
        self.current_owner.sapient.possessions.remove(self)
        self.current_owner.sapient.former_possessions.add(self)

        self.current_owner = None


    def set_current_building(self, building):
        ''' Moves it to a building, but preserves the owner '''
        self.current_holder = None
        self.current_building = building

        building.add_housed_object(obj=self)
        self.wx, self.wy = building.site.x, building.site.y

    def set_current_holder(self, figure):
        ''' Moves it from a building to a person, preserving the owner '''
        if self.current_building:
            self.current_building.remove_housed_object(obj=self)
            self.current_building = None

        self.current_holder = figure

    def clear_current_holder(self):
        ''' Clears from current holder '''
        self.current_holder = None


    def clear_current_building_and_location(self):
        self.current_building.remove_housed_object(obj=self)
        self.current_building = None
        self.current_location = None

    def set_initial_attachments(self):
        ''' Once the object is created, handle stuff which should be attached to each other.
        The first component should always be the "center" to which other things should be attached
        (and thus have no attachment info). Every other component should have a tuple containing
        attachment info. Unfortunately we have to store the string of the name of the component that
        it should be attaching to, since we won't have the actual component object created at the time
        that the component list is populated '''
        for component in self.components:
            # Make sure the component knows what object it belongs to!
            component.owner = self
            # Handle attachments
            if component.attachment_info != (None, None):
                name_of_target_component, attach_strength = component.attachment_info
                target_component = self.get_component_by_name(component_name=name_of_target_component)

                component.attach_to(target_component, attach_strength)

    def set_display_color(self, color):
        self.display_color = color


    def remove_from_map(self):
        ''' For when objs need to be removed from rendering info, but still exist.
        Mostly useful with clothing, and storing items, for now '''
        if self.x:
            M.tiles[self.x][self.y].objects.remove(self)

        self.x = None
        self.y = None

        if self in M.objects:
            M.objects.remove(self)

        if self in M.sapients:
            M.sapients.remove(self)

    def put_on_clothing(self, clothing):
        ''' Add this clothing to a parent object '''
        # Remove it from the map and handle some info about it
        ## TODO - fix awkward check about M
        if M is not None and clothing in M.objects:
            clothing.remove_from_map()

        clothing.being_worn = 1
        self.wearing.append(clothing)

        # Loops through all components in the wearable item,
        # and adds those layers onto the person wearing them
        for component in clothing.components:

            ## THIS FLAG IS ONLY FOR CLOTHING WHICH ADDS TO THE LAYERS
            if component.bodypart_covered:
                our_bodypart = self.get_component_by_name(component.name)

                ## This should add the clothing layers to whatever it covers
                ## TODO - unsure how to handle clothing with multiple components
                for layer in component.layers:
                    our_bodypart.add_material_layer(layer=layer, layer_is_inherent_to_object_component=0)

            ## THIS FLAG IS ONLY FOR WEARABLE THINGS WHICH DO NOT ADD TO LAYERS (like a backpack)
            elif component.bodypart_attached:
                attaches_to = component.bodypart_attached
                attach_strength = component.bodypart_attach_strength

                if attaches_to:
                    our_bodypart = self.get_component_by_name(component_name=attaches_to)
                    component.attach_to(our_bodypart, attach_strength)


    def take_off_clothing(self, clothing):
        ''' Remove this clothing from the parent object '''
        clothing.being_worn = 0
        # Remove from list of things parent is wearing
        self.wearing.remove(clothing)

        for component in clothing.components:

            ## THIS FLAG IS ONLY FOR CLOTHING WHICH ADDS TO THE LAYERS
            if component.bodypart_covered:
                our_bodypart = self.get_component_by_name(component.name)

                ## This should add the clothing layers to whatever it covers
                ## TODO - unsure how to handle clothing with multiple components
                for layer in reversed(component.layers):
                    our_bodypart.remove_material_layer(layer=layer)

            ## THIS FLAG IS ONLY FOR WEARABLE THINGS WHICH DO NOT ADD TO LAYERS (like a backpack)
            elif component.bodypart_attached:
                attaches_to = component.bodypart_attached
                attach_strength = component.bodypart_attach_strength

                if attaches_to:
                    our_bodypart = component.attached_to
                    component.disattach_from(our_bodypart)

        # Add it to the map
        M.add_object_to_map(x=self.x, y=self.y, obj=clothing)


    def get_component_by_name(self, component_name):
        ''' Given the name of a component, return the actual component '''
        for component in self.components:
            if component.name == component_name:
                return component

    def initial_give_object_to_hold(self, obj):
        ''' A bit of a hack for now, just to get the object holding a weapon '''
        for component in self.components:
            if 'grasp' in component.functions and not component.grasped_item:
                # Give 'em a sword
                self.pick_up_object(own_component=component, obj=obj)
                break


    def pick_up_object(self, own_component, obj):
        ''' Use the specified component to grasp an object '''
        own_component.grasp_item(obj)

        obj.set_current_owner(self)
        obj.set_current_holder(self)

        ''' TODO - this is causing the game to freak out on worldmap view before a scale map has been created '''
        if game.map_scale == 'human':
            obj.remove_from_map()


    def drop_object(self, own_component, obj):
        ''' Drop an item, it will show up on the map '''
        own_component.remove_grasp_on_item(obj)
        # Add to the map wherever the owner is
        M.add_object_to_map(x=self.x, y=self.y, obj=obj)

        obj.clear_current_holder()

    def place_inside(self, own_component, other_object, grasping_component=None):

        available_volume = own_component.get_storage_volume()

        if other_object.get_volume() > available_volume:
            game.add_message(''.join([other_object.name, ' is too big to fit in the ', own_component.name]))

        else:
            other_object.remove_from_map()
            # If we put something inside that we're already grasping, remove it
            # (otherwise, it's assumed we're gonna pick it up without the hastle of
            # clicking to grasp it, then clicking again to put it away
            if grasping_component is not None:
                grasping_component.remove_grasp_on_item(other_object)

            own_component.add_object_to_storage(other_object)

            game.add_message(''.join(['You place the ', other_object.name, ' in the ', own_component.name]))

            # This statement helps with menu items
            return 'success'

    def take_out_of_storage(self, other_object, grasping_component):
        other_object.inside.remove_object_from_storage(other_object)

        grasping_component.grasp_item(other_object)


    def get_stored_items(self):
        ''' Get everything stored inside us '''
        stored_items = []
        for component in self.components:
            if component.storage is not None:
                for obj in component.storage:
                    stored_items.append(obj)

        return stored_items

    def get_storage_items(self):
        ''' Returns a list of all items on our character which can store something '''
        storage_items = []
        for component in player.components:
            for attached_obj_comp in component.attachments:
                # Loop through objs to find components with storage
                if attached_obj_comp.storage is not None:
                    storage_items.append(attached_obj_comp)

        return storage_items

    def get_inventory(self):
        ''' return inventory
        Includes stuff we're wearing, and stuff we're grasping '''

        inventory = {'clothing':[], 'stored':[], 'grasped':[]}
        # Gather worn clothing
        #worn_clothing = []
        for clothing in self.wearing:
            inventory['clothing'].append(clothing)
            # Find if anything's stored within
            for item in clothing.get_stored_items():
                inventory['stored'].append(item)

        # Gather any items we're wearing
        #worn_items = []
        #for component in self.components:
        #    for obj_component in component.attachments:
        #        if obj_component.owner != component.owner:
        #            inventory['worn items'].append(obj_component.owner)

        # Build a list of things we're grasping
        graspers = self.creature.get_graspers()
        for component in graspers:
            if component.grasped_item is not None:
                inventory['grasped'].append(component.grasped_item)

                for item in component.grasped_item.get_stored_items():
                    inventory['stored'].append(item)

        return inventory

    def get_base_attack_value(self):
        # Base attack value is the object's mass. However,
        # if it wasn't specifically designed as a weapon,
        # that will be halved.
        if self.weapon:
            return self.get_mass()
        else:
            return self.get_mass() / 2

    def get_mass(self):
        mass = 0
        for component in self.components:
            mass += component.get_mass()

        return mass

    def get_volume(self):
        volume = 0
        for component in self.components:
            volume += component.get_volume()

        return volume

    def get_density(self):
        mass = 0
        volume = 0
        for component in self.components:
            mass += component.get_mass()
            volume += component.get_volume()

        return mass / volume

    def destroy_component(self, component):
        ''' destroy a component of this object '''
        if component.attached_to is not None:
            component.disattach_from(component.attached_to)

        # Object kind of disintigrates... ???
        if component.attached_to is None:
            # Check if anything is in the list of attachments
            for other_component in component.attachments:
                other_component.disattach_from(component)
                game.add_message(other_component.name + ' has disattached from ' + component.name)

                # Each other component it's attached to becomes its own object
                other_component.attaches_to = None
                self.create_new_object_from_component(original_component=other_component)

        # This function should create a new object featuring the remains of this component
        # (and any other component attached to this one)
        self.create_new_object_from_component(original_component=component)

        # After creating the new object, destroy ourself
        # Some objects like wearable ones aren't in the list of objects on the map, so ignore those
        if self in M.objects and len(self.components) == 0:
            self.remove_from_map()


    def create_new_object_from_component(self, original_component):
        ''' If a component gets knocked off and we want to build a new object
        out of it, this is how we would do it '''

        # First, build a list of all components attached to the current one
        component_list = [original_component]

        found_additional_component = True
        while found_additional_component:
            found_additional_component = False

            for component in component_list:
                # Check if component is attached to anything
                if component.attached_to is not None and component.attached_to not in component_list:
                    found_additional_component = True
                    component_list.append(component.attached_to)
                # Check attachments
                for attached_component in component.attachments:
                    if attached_component not in component_list:
                        found_additional_component = True
                        component_list.append(attached_component)

        ## Make sure the component itself isn't set to attach to anything
        ## This prevents arms from trying to attach to phantom torsos, for example
        original_component.attaches_to = None

        # Now remove all of the components from the original object
        for component in component_list:
            self.components.remove(component)

        # Finally, create a new object at this location containing the components
        if self.name.endswith('remains'):
            print 'Creating new object from %s' %self.name
            new_name = self.name
        else:
            new_name = self.name + ' remains'
        #new_char = '%'
        new_char = self.char
        new_color = libtcod.color_lerp(libtcod.black, self.color, .5)

        ############# TODO - cleanup item location code so we don't need this verbose check for this item's location
        if self.x is None:
            if self.current_holder:
                # OK - no current location, but it has an owner we can piggyback from
                print 'Creating new object - %s has no location, so using location of %s.' %(self.fullname(), self.fullname())
                x, y = self.current_holder.x, self.current_holder.y
            else:
                # Bad - there is no location info for object, and it does not have someone currently holding it
                print 'Creating new object - %s has no location and no current holder!' %self.fullname()
                x, y = 10, 10
        # This would ideally always happen - this object has a concrete location
        else:
            x, y = self.x, self.y
        ###############################################################################################################

        obj = Object(name=new_name, char=new_char, color=new_color,components=[],
                     blocks_mov=0, blocks_vis=0, description='This is a piece of %s'%self.fullname(), creature=None,
                     sapient=None, weapon=None, wearable=None)
        # I think this was done to prevent components trying to attach in weird ways when passed to the obj
        for component in component_list:
            obj.components.append(component)
            component.owner = obj

        M.add_object_to_map(x=x, y=y, obj=obj)


    def move(self, dx, dy): #DON'T USE WITH A*,
        #move by the given amount, if the destination is not blocked
        blocks_mov = self.abs_pos_move(x=self.x+dx, y=self.y+dy)


    def move_and_face(self, dx, dy):
        #DON'T USE WITH A*,
        #move by the given amount, if the destination is not blocked
        blocks_mov = self.abs_pos_move(x=self.x+dx, y=self.y+dy)

        if not blocks_mov and (dx, dy) != (0, 0):
            # Face (index of direction we moved in)
            self.creature.facing = NEIGHBORS.index((dx, dy))

    '''
    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def move_towards_f(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move_and_face(dx, dy)
    '''


    def abs_pos_move(self, x, y): #USE WITH A*
        ''' The x and y vals here are actual x and y vals on the map '''
        blocks_mov = 1
        if not M.tile_blocks_mov(x, y):
            blocks_mov = 0

            M.tiles[self.x][self.y].objects.remove(self)
            libtcod.map_set_properties(M.fov_map, self.x, self.y, True, True)
            self.x = x
            self.y = y
            libtcod.map_set_properties(M.fov_map, self.x, self.y, True, False)
            #libtcod.map_set_properties(M.fov_map, next_step[0], next_step[1], True, False)
            M.tiles[self.x][self.y].objects.append(self)

            ## For now, give other objects X and Y vals
            # TODO - make sure these are set when initially added to map
            for obj in self.wearing:
                obj.x = self.x
                obj.y = self.y

        return blocks_mov

    def set_astar_target(self, target_x, target_y):
        game.add_message('%s setting astar target'%self.fullname(), self. color)
        ''' Sets a target using A*, includes flipping the target tile to unblocks_mov if it's a creature '''
        flip_target_tile = False
        # If the target is blocked, we need to temporarily set it to unblocked so A* can work
        if M.tile_blocks_mov(target_x, target_y) and get_distance_to(self.x, self.y, target_x, target_y) > 1:
            flip_target_tile = True
            libtcod.map_set_properties(M.fov_map, target_x, target_y, True, True)

        ai_move_path = libtcod.path_compute(M.path_map, self.x, self.y, target_x, target_y)
        ## v Old code from when this method actually moved the object
        #if ai_move_path and not libtcod.path_is_empty(M.path_map):
        #    x, y = libtcod.path_walk(M.path_map, True)
        #    blocks_mov = self.abs_pos_move(x=x, y=y)

        if flip_target_tile:
            # Flip the target's cell back to normal
            libtcod.map_set_properties(M.fov_map, target_x, target_y, True, False)

        self.cached_astar_path = libtcod_path_to_list(path_map=M.path_map)

    def move_with_stored_astar_path(self, path):
        #next_step = path.pop(0)
        #blocks_mov = self.abs_pos_move(x=next_step[0], y=next_step[1])
        if len(path):
            blocks_mov = self.abs_pos_move(x=path[0][0], y=path[0][1])
            if not blocks_mov:
                del path[0]

            return blocks_mov

        return 'path_end'


    def closest_creature(self, max_range, target_faction='enemies'):
        closest_enemy = None
        closest_dist = max_range + 1  #start with (slightly more than) maximum range

        if target_faction == 'enemies':
            for actor in M.sapients:
                if actor.creature.status == 'alive' and actor.sapient.faction in self.sapient.enemy_factions: #and libtcod.map_is_in_fov(fov_map, object.x, object.y):
                    dist = self.distance_to(actor)
                    if dist < closest_dist:
                        closest_enemy = actor
                        closest_dist = dist

        else:
            for actor in M.sapients:
                if actor.creature.status == 'alive' and actor.creature and actor.sapient.faction == target_faction: #and libtcod.map_is_in_fov(fov_map, object.x, object.y):
                    #calculate distance between this object and the player
                    dist = self.distance_to(actor)
                    if dist < closest_dist:  #it's closer, so remember it
                        closest_enemy = actor
                        closest_dist = dist

        return closest_enemy, closest_dist

    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    ##### World-coords style ##############
    def w_distance_to(self, other):
        #return the distance to another object
        dx = other.wx - self.wx
        dy = other.wy - self.wy
        return math.sqrt(dx ** 2 + dy ** 2)

    def w_distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.wx) ** 2 + (y - self.wy) ** 2)

    def w_teleport(self, x, y):
        WORLD.tiles[self.wx][self.wy].entities.remove(self)
        self.wx = x
        self.wy = y
        WORLD.tiles[self.wx][self.wy].entities.append(self)

        # Army status stuff
        self.world_last_dir = (0, 0)
        self.turns_since_move = 0

        if self.sapient and self.sapient.is_commander():
            for commanded_figure_or_population in self.sapient.commanded_figures + self.sapient.commanded_populations:
                commanded_figure_or_population.w_teleport(x, y)


    def w_move(self, dx, dy): #DON'T USE WITH A*,
        ''' Moves the army by the given xy coords, and handles updating the army's map info '''
        #self.check_for_army_dispatch()

        #move by the given amount, if the destination is not blocked
        if not WORLD.tile_blocks_mov(self.wx + dx, self.wy + dy):
            WORLD.tiles[self.wx][self.wy].entities.remove(self)
            self.wx += dx
            self.wy += dy
            WORLD.tiles[self.wx][self.wy].entities.append(self)

            # Army status stuff
            self.world_last_dir = (-dx, -dy)
            self.turns_since_move = 0

            # Make sure to also move any units commanded with us
            if self.sapient:
                for commanded_figure_or_population in self.sapient.commanded_figures + self.sapient.commanded_populations:
                    commanded_figure_or_population.w_move(dx=dx, dy=dy)

        #self.update_figures_and_check_for_city()

    def w_move_to(self, target_x, target_y):
        ''' Computes A* path and makes move '''
        ai_move_path = libtcod.path_compute(WORLD.path_map, self.wx, self.wy, target_x, target_y)
        if ai_move_path and not libtcod.path_is_empty(WORLD.path_map):
            x, y = libtcod.path_walk(WORLD.path_map, True)

            dx, dy = x - self.wx, y - self.wy

            self.move(dx, dy)

    def w_move_along_path(self, path):
        ''' Move along a predefined path (like roads between cities) '''
        # The path will be a list of tuples
        (x, y) = path.pop(0)
        dx, dy = x-self.wx, y-self.wy

        self.w_move(dx, dy)

    def w_draw(self):
        #only show if it's visible to the player
        #if libtcod.map_is_in_fov(fov_map, self.x, self.y):
        (x, y) = camera.map2cam(self.wx, self.wy)

        if x is not None:
            #set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(map_con.con, self.color)
            libtcod.console_put_char(map_con.con, x, y, self.char, libtcod.BKGND_NONE)

    #### End moving world-coords style ########

    def draw(self):
        #only show if it's visible to the player
        if libtcod.map_is_in_fov(M.fov_map, self.x, self.y):
            (x, y) = camera.map2cam(self.x, self.y)

            if x is not None:
                #set the color and then draw the character that represents this object at its position
                libtcod.console_set_default_foreground(map_con.con, self.display_color)
                libtcod.console_put_char(map_con.con, x, y, self.char, libtcod.BKGND_NONE)

        elif not self.local_brain:
            (x, y) = camera.map2cam(self.x, self.y)

            if x is not None:
                libtcod.console_set_default_foreground(map_con.con, self.shadow_color)
                #libtcod.console_set_default_foreground(con.con, self.dark_color)
                libtcod.console_put_char(map_con.con, x, y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        #erase the character that represents this object
        (x, y) = camera.map2cam(self.x, self.y)
        if x is not None:
            libtcod.console_put_char(map_con.con, x, y, ' ', libtcod.BKGND_NONE)

    def firstname(self):
        if self.sapient:
            return self.sapient.firstname
        else:
            return self.name

    def lastname(self):
        if self.sapient:
            return self.sapient.lastname
        else:
            return self.name

    def fullname(self):
        if self.sapient and self.sapient.epithet: # and self.creature.status != 'dead':
            return '{0} \"{1}\" {2}'.format(self.sapient.firstname, self.sapient.epithet, self.sapient.lastname)
        if self.sapient:
            return '{0} {1}'.format(self.sapient.firstname, self.sapient.lastname)
        else:
            return self.name

    def fulltitle(self):
        if self.sapient and self.creature.intelligence_level == 3:
            return '{0}, {1} {2}'.format(self.fullname(), lang.spec_cap(self.creature.creature_type), self.sapient.get_profession())
        if self.sapient and self.creature.intelligence_level == 2:
            return '{0}, {1} savage'.format(self.fullname(), lang.spec_cap(self.creature.creature_type))
        else:
            return self.name

    def get_weapon_properties(self):
        if self.weapon:
            return self.weapon['properties']
        # Empty properties if no weapon
        return {}



def attack_menu(actor, target):
    width = 70
    height = 32

    bwidth = width - (4 * 2)

    xb, yb = 0, 0
    transp = .8
    # Make the console window
    wpanel = gui.GuiPanel(width=width, height=height, xoff=xb, yoff=yb, interface=interface, is_root=0, append_to_panels=1, transp=.8)


    def button_refresh_func(target):
        width = 70
        height = 32

        bwidth = 20

        left_x = 2
        mid_x = 24
        right_x = 46

        left_y = 14
        mid_y = 14
        right_y = 14

        atx, aty = 4, 14
        # Setup buttons
        i = aty
        buttons = [gui.Button(gui_panel=wpanel, func=show_object_info, args=[target],
                                  text='Obj info', topleft=(mid_x, i), width=bwidth, height=4, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),
                   gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                          text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

        ## Make a button for each component
        for component in target.components:
            #for (layer, coverage) in component.get_coverage_layers():
                #dispinfo = ''.join([component.name, '\n (', layer.get_name(), ': ', str(int(coverage * 100)), ')'])
                #dispinfo = ''.join([component.name, ' (', layer.get_name(), ')\n', str(int(layer.get_health() * 100)), ' hlth, ', str(int(coverage * 100)), ' cvg'])

            if 'left' in component.name: #.startswith('left'):
                xval = left_x
                left_y += 4
                yval = left_y
            elif 'right' in component.name: #.startswith('right_x'):
                xval = right_x
                right_y += 4
                yval = right_y
            else:
                xval = mid_x
                mid_y += 4
                yval = mid_y


            weapon = player.creature.get_current_weapon()

            attack_mods, defend_mods = player.creature.get_attack_odds(attacking_object_component=weapon.components[0],
                                                                    force=weapon.get_base_attack_value(), target=target, target_component=component)

            attack_chance = sum(attack_mods.values())
            defend_chance = sum(defend_mods.values())

            ############## Info for mouseover ##############
            h_header = [' -* Attack {0} *-'.format(component.name.capitalize()), '{0}/{1} = {2:.02f} perc. chance'.format(attack_chance, defend_chance, (attack_chance/(attack_chance+defend_chance))*100)]

            h_info = ['Attack Score (%i)'%attack_chance]
            for mod, amt in attack_mods.iteritems():
                h_info.append('%s: %i'%(mod, amt) )
            h_info.append('')

            h_info.append('Defense Score (%i)'%defend_chance)
            for mod, amt in defend_mods.iteritems():
                h_info.append('%s: %i'%(mod, amt) )
            ###############################################

            button_disp_info = '{0}\n{1:.02f} chance'.format(component.name, (attack_chance/(attack_chance+defend_chance))*100)

            buttons.append(gui.Button(gui_panel=wpanel, func=player.creature.standard_combat_attack, args=[weapon.components[0], weapon.get_base_attack_value(), target, component],
                                   text=button_disp_info, topleft=(xval, yval), width=20, height=4, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True,
                                   hover_header=h_header, hover_text=h_info) )


        mid_y += 4
        buttons.append(gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                                  text='Cancel', topleft=(mid_x, mid_y), width=bwidth, height=4, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True))

        wpanel.gen_buttons = buttons


    def render_text_func(target):
        atx, aty = 4, 18
        ## Target and curent weapon info

        weapon = player.creature.get_current_weapon()
        attack_mods, defend_mods = player.creature.get_attack_odds(attacking_object_component=weapon.components[0],
                                                                    force=weapon.get_base_attack_value(), target=target, target_component=None)


        libtcod.console_print(wpanel.con, atx, 2, 'Target: ' + target.fullname())


        atk_tot = sum(attack_mods.values())
        dfn_tot = sum(defend_mods.values())

        libtcod.console_print(wpanel.con, atx, 4, 'General odds: %i (atk) and %i (dfn) = %01f ' \
                              %(atk_tot, dfn_tot, atk_tot / (atk_tot + dfn_tot) )  )

        y = 6
        libtcod.console_print(wpanel.con, atx, y, 'Attack - total: ' + str(sum(attack_mods.values())) )
        for mod, amt in attack_mods.iteritems():
            y += 1
            libtcod.console_print(wpanel.con, atx, y, mod + ': ' + str(amt) )


        y = 6
        libtcod.console_print(wpanel.con, atx + 35, y, 'Defense - total: ' + str(sum(defend_mods.values())))
        for mod, amt in defend_mods.iteritems():
            y += 1
            libtcod.console_print(wpanel.con, atx + 35, y, mod + ': ' + str(amt) )


    wpanel.update_button_refresh_func(button_refresh_func, [target])
    wpanel.update_render_text_func(render_text_func, [target])


def talk_screen(actor, target):
    width = 35

    xb, yb = 0, 0
    transp = .8
    # gui.Button 1 and 2 x vals
    b1x, b2x = 3, 15
    # gui.Button row 1 and 2 y vals
    row1y, row2y = 10, 14
    # Menu iten x and y vals
    atx, aty = 4, 15

    height = 40

    # Make the console window
    wpanel = gui.GuiPanel(width=width, height=height, xoff=xb, yoff=yb, interface=interface, name='talk_screen')

    def refresh_buttons():
        aty = 15
        buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                          text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

        talk_options = player.sapient.get_valid_questions(target)

        for option in talk_options:
            button = gui.Button(gui_panel=wpanel, func=player.sapient.ask_question, args=(target, option),
                                text=option, topleft=(atx, aty), width=16, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)

            buttons.append(button)
            aty += 3

        #buttons.append(gui.Button(gui_panel=wpanel, func=recruit, args=[target], text='Recruit', origin=(atx, aty), width=6, tall=1, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True))
        buttons.append(gui.Button(gui_panel=wpanel, func=attack_menu, args=[player, target],
                                  text='Attack!', topleft=(atx, aty+3), width=16, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1))

        buttons.append(gui.Button(gui_panel=wpanel, func=order_menu, args=[player, target],
                                  text='Order', topleft=(atx, aty+6), width=16, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1))

        buttons.append(gui.Button(gui_panel=wpanel, func=render_handler.debug_dijmap_view, args=[target],
                                  text='See DMap', topleft=(atx, aty+9), width=16, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True))
        buttons.append(gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                                  text='Done', topleft=(atx, aty+12), width=16, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True))

        wpanel.gen_buttons = buttons


    def render_panel_text():

        # Character name + title
        libtcod.console_print(wpanel.con, b1x, 2, target.fullname())
        libtcod.console_print(wpanel.con, b1x, 3, target.sapient.get_profession())

        # Dynasty
        if target.sapient.dynasty:
            dynasty_info = ''.join([target.sapient.dynasty.lastname, ' dynasty'])
            libtcod.console_put_char_ex(wpanel.con, b1x, 4, target.sapient.dynasty.symbol, target.sapient.dynasty.symbol_color, target.sapient.dynasty.background_color)
        else:
            dynasty_info = 'No major dynasty'
            libtcod.console_put_char_ex(wpanel.con, b1x, 4, target.sapient.lastname[0], PANEL_FRONT, libtcod.darker_grey)

        libtcod.console_print(wpanel.con, b1x + 2, 4, dynasty_info)

        # Age
        libtcod.console_print(wpanel.con, b1x, 6, 'Age ' + str(target.sapient.get_age()))
        libtcod.console_print(wpanel.con, b1x, 7, str(len(target.sapient.children)) + ' children')

    # Ugly ugly...
    wpanel.update_button_refresh_func(refresh_buttons, () )

    wpanel.update_render_text_func(render_panel_text, [] )



def order_menu(player, target):
    ''' Order for individual unit '''
    atx, aty = 4, 5

    height = 40
    width = 28

    bwidth = width - (4 * 2)

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    bx = 4
    by = 5

    wpanel.add_button(func=interface.prepare_to_delete_panel, args=[wpanel], text='Done', topleft=(bx, height-5), width=bwidth, height=3)
    wpanel.add_button(func=interface.prepare_to_delete_panel, args=[wpanel], text='X', topleft=(width-4, 1), width=3, height=3)


    wpanel.add_button(func=player_give_order, args=[target, 'move_to'], text='Move to...', topleft=(atx, aty), width=bwidth, height=3, closes_menu=1)
    wpanel.add_button(func=player_give_order, args=[target, 'follow'], text='Follow me', topleft=(atx, aty+3), width=bwidth, height=3 , closes_menu=1)


def player_give_order(target, order):
    ''' Interface to give the actual order selected from the menu '''
    if order == 'move_to':
        while 1:
            event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
            mx, my = mouse.cx, mouse.cy
            x, y = camera.cam2map(mx, my)

            render_handler.render_all(do_flush=False)

            libtcod.console_print(con=map_con.con, x=int(map_con.width/2)-30, y=8, fmt='Click where you would like %s to move (right click to cancel)'%target.sapient.firstname)
            ## Draw the path that the guy will take
            path = libtcod.path_compute(p=M.path_map, ox=target.x, oy=target.y, dx=x, dy=y)
            while not libtcod.path_is_empty(p=M.path_map):
                px, py = libtcod.path_walk(M.path_map, True)
                cpx, cpy = camera.map2cam(px, py)
                libtcod.console_put_char_ex(con=map_con.con, x=cpx, y=cpy, c='*', fore=libtcod.light_grey, back=libtcod.BKGND_NONE)
            # Draw the final location
            libtcod.console_put_char_ex(con=map_con.con, x=mx, y=my, c='X', fore=libtcod.grey, back=libtcod.black)

            if mouse.lbutton:
                player.sapient.say('%s, move over there'%target.fullname())
                target.local_brain.set_state('moving', target_location=(x, y))
                break
            elif mouse.rbutton:
                break

            map_con.blit()
            libtcod.console_flush()

            game.handle_fov_recompute()

    elif order == 'follow':
        target.local_brain.set_state('following', target_figure=player)
        player.sapient.say('%s, follow me!'%target.fullname())

def player_order_follow():
    ''' Player orders all nearby allies to follow him '''
    player.sapient.say('Everyone, follow me!')
    for figure in filter(lambda figure: figure.sapient.commander == player and figure != player and figure.distance_to(player) <= 50 and figure.local_brain.perception_info['closest_enemy'] is None, M.sapients):
        figure.local_brain.set_state('following', target_figure=player)

def player_order_move():

    figures = filter(lambda figure: figure.local_brain and figure.creature.status == 'alive' and figure.sapient.commander == player, M.sapients)
    sq_size = int(round(math.sqrt(len(figures))))
    offset = int(sq_size/2)

    while 1:
        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        mx, my = mouse.cx, mouse.cy
        x, y = camera.cam2map(mx, my)

        render_handler.render_all(do_flush=False)

        libtcod.console_print(con=map_con.con, x=int(map_con.width/2)-30, y=8, fmt='Click where you would like your army to move (right click to cancel)')

        # Draw the final location
        locs = []
        for i in xrange(mx-offset, mx+sq_size+1):
            for j in xrange(my-offset, my+sq_size+1):
                ii, jj = camera.cam2map(i, j)
                if not M.tile_blocks_mov(ii, jj):
                    locs.append((ii, jj))
                    libtcod.console_put_char_ex(con=map_con.con, x=i, y=j, c='X', fore=libtcod.grey, back=libtcod.black)

        if mouse.lbutton_pressed and len(locs) >= len(figures):
            player.sapient.say('Everyone, move over there')
            for i, figure in enumerate(figures):
                figure.local_brain.set_state('moving', target_location=locs[i])
            break

        elif mouse.lbutton_pressed:
            game.add_message('Location has too much blocking it to order entire group there', libtcod.darker_red)

        elif mouse.rbutton_pressed:
            break

        map_con.blit()
        libtcod.console_flush()

        game.handle_fov_recompute()

def pick_up_menu():

    objs = [obj for obj in M.tiles[player.x][player.y].objects if obj != player]

    if len(objs) == 0:
        game.add_message('No objects to pick up at your location')
        return 'done'

    atx, aty = 4, 5

    height = 40
    width = 28

    bwidth = width - (4 * 2)

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    bx = 4
    by = 5

    wpanel.add_button(func=interface.prepare_to_delete_panel, args=[wpanel], text='Done', topleft=(bx, height-5), width=bwidth, height=3)
    wpanel.add_button(func=interface.prepare_to_delete_panel, args=[wpanel], text='X', topleft=(width-4, 1), width=3, height=3)

    i = 0
    for obj in objs:
        i += 5

        wpanel.add_button(func=storage_menu, args=[obj], text='Store ' + obj.name + '...',
                                          topleft=(atx, i), width=bwidth, height=4, closes_menu=1)
        # Hold in one of the hands
        for grasper in player.creature.get_graspers():
            if grasper.grasped_item is None:
                i += 5

                wpanel.add_button(func=player.pick_up_object, args=[grasper, obj], text='Hold ' + obj.name + ' in ' + grasper.name,
                                          topleft=(atx, i), width=bwidth, height=4, closes_menu=1)

        # Wear it, if possible
        if obj.wearable:
            i += 5

            wpanel.add_button(func=player.put_on_clothing, args=[obj], text='Wear the ' + obj.name,
                                      topleft=(atx, i), width=bwidth, height=4, closes_menu=1)


def manage_inventory():

    height = 40
    width = 28

    bx = 4
    by = 5

    b_width = width - (4 * 2)

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    def update_button_func():
        wpanel.gen_buttons = []

        inventory = player.get_inventory()

        # Setup buttons
        wpanel.add_button(func=interface.prepare_to_delete_panel, args=[wpanel], text='Done', topleft=(bx, height-5), width=b_width, height=3)
        wpanel.add_button(func=interface.prepare_to_delete_panel, args=[wpanel], text='X', topleft=(width-4, 1), width=3, height=3)

        i = 0
        for obj in inventory['clothing']:
            i += 3
            wpanel.add_button(func=player.take_off_clothing, args=[obj], text='Take off ' + obj.name, topleft=(bx, by+i), width=b_width, height=3)

        #draw_box(panel=root_con.con, x=bx-2, x2=bx+7+2, y=by-1, y2=i+1, color=libtcod.red)

        i += 3
        for obj in inventory['grasped']:
            i += 3
            wpanel.add_button(func=storage_menu, args=[obj], text='Store ' + obj.name + '...', topleft=(bx, by+i), width=b_width, height=3)
            i += 3
            wpanel.add_button(func=player.drop_object, args=[obj.being_grasped_by, obj], text='Drop ' + obj.name, topleft=(bx, by+i), width=b_width, height=3)

        i += 3
        for obj in inventory['stored']:
            for grasper in player.creature.get_graspers():
                if grasper.grasped_item is None:
                    i += 3
                    wpanel.add_button(func=player.take_out_of_storage, args=[obj, grasper], text='Hold ' + obj.name + '\n in ' + grasper.name, topleft=(bx, by+i), width=b_width, height=3)

        # Update gui panel buttons
        #wpanel.gen_buttons = buttons


    wpanel.update_button_refresh_func(update_button_func, () )


def storage_menu(obj):
    height = 40
    width = 28

    bx = 4
    by = 5

    b_width = width - (4 * 2)

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    ### Get a list of storage devices player might have
    storage_items = player.get_storage_items()

    buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel], text='Done',
                          topleft=(bx, height-5), width=b_width, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),
               gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                          text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

    # Store item
    i = 0
    for component_with_storage in storage_items:
        i += 5
        buttons.append(gui.Button(gui_panel=wpanel, func=component_with_storage.owner.place_inside, args=[component_with_storage, obj],
                                  text='Place ' + obj.name + ' in ' + component_with_storage.name, topleft=(bx, i),
                                  width=b_width, height=4, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1))

    wpanel.gen_buttons = buttons


def choose_object_to_interact_with(objs, x, y):
    ''' There may be multiple objects to interact with on a given tile
    This function handles that. '''

    # If there's only one object, either talk to it or attack it (for now)
    if len(objs) == 1 and (not M.tiles[x][y].interactable):

        obj = objs[0]
        if obj.creature and obj.sapient and obj.creature.status == 'alive':
            talk_screen(actor=player, target=obj)
        else:
            attack_menu(actor=player, target=obj)

    # Else, a button menu which shows the interactions
    elif len(objs) > 1:

        (x, y) = camera.map2cam(x, y)

        height = 30
        width = 28

        bx = 4
        by = 5

        b_width = width - (4 * 2)

        wpanel = gui.GuiPanel(width=width, height=height, xoff=x, yoff=y, interface=interface)

        buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel], text='Done',
                              topleft=(bx, height-5), width=b_width, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),
                   gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                          text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

        i = 0
        for obj in objs:
            i += 4

            if obj.creature and obj.creature.status == 'alive':
                buttons.append(gui.Button(gui_panel=wpanel, func=talk_screen, args=[player, obj],
                                  text='Talk to ' + obj.fullname(), topleft=(bx, i),
                                  width=b_width, height=4, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1))
            else:
                buttons.append(gui.Button(gui_panel=wpanel, func=attack_menu, args=[player, obj],
                                  text='Interact with ' + obj.fullname(), topleft=(bx, i),
                                  width=b_width, height=4, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1))

        wpanel.gen_buttons = buttons

    # Specific tile interaction...
    if M.tiles[x][y].interactable:

        func = M.tiles[x][y].interactable['func']
        args = M.tiles[x][y].interactable['args']
        text = M.tiles[x][y].interactable['text']

        (x, y) = camera.map2cam(x, y)

        height = 12
        width = 22

        bx = 4
        by = 5

        b_width = width - (4 * 2)

        wpanel = gui.GuiPanel(width=width, height=height, xoff=x, yoff=y, interface=interface)


        buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel], text='Cancel',
                              topleft=(bx, height-5), width=b_width, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),
                   gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                          text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]


        buttons.append(gui.Button(gui_panel=wpanel, func=func, args=args, text=text,
                                   topleft=(bx, 2), width=b_width, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1))

        wpanel.gen_buttons = buttons


def debug_menu():
    height = 50
    width = 30

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    if game.map_scale == 'world':
        buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                 text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),

                   gui.Button(gui_panel=wpanel, func=list_people, args=[],
                 text='People', topleft=(3, 5), width=width-4, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1),

                    gui.Button(gui_panel=wpanel, func=list_factions, args=[],
                 text='Factions', topleft=(3, 8), width=width-4, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1)
                   ]
    elif game.map_scale == 'human':
        buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
                 text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True),

                 gui.Button(gui_panel=wpanel, func=list_people, args=[],
                 text='People', topleft=(3, 5), width=width-4, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True, closes_menu=1)
                   ]

    wpanel.gen_buttons = buttons


def list_people():
    height = 50
    width = 30

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
             text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

    y = 5
    for faction in WORLD.factions:

        leader = faction.get_leader()
        if leader is not None:
            y += 1
            buttons.append(gui.Button(gui_panel=wpanel, func=leader.sapient.die, args=[],
                 text=leader.fulltitle(), topleft=(2, y), width=width-4, height=1, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=False) )

    wpanel.gen_buttons = buttons


def list_factions():
    height = 50
    width = 30

    wpanel = gui.GuiPanel(width=width, height=height, xoff=0, yoff=0, interface=interface)

    buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
             text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

    y = 5
    for faction in WORLD.factions:

        y += 1
        buttons.append(gui.Button(gui_panel=wpanel, func=dbg_faction_relations, args=[faction],
             text='%s (%i)' % (faction.faction_name, len(faction.members) ), topleft=(2, y), width=width-4, height=1, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=False) )

    wpanel.gen_buttons = buttons


def dbg_faction_relations(faction):
    height = 50
    width = 30

    wpanel = gui.GuiPanel(width=width, height=height, xoff=30, yoff=0, interface=interface)

    buttons = [gui.Button(gui_panel=wpanel, func=interface.prepare_to_delete_panel, args=[wpanel],
             text='X', topleft=(width-4, 1), width=3, height=3, color=PANEL_FRONT, hcolor=libtcod.white, do_draw_box=True)]

    def render_text_func():
        y = 2

        libtcod.console_print(con=wpanel.con, x=2, y=y, fmt=faction.faction_name)

        y += 3
        for other_faction in WORLD.factions:
            y += 1
            libtcod.console_print(con=wpanel.con, x=2, y=y, fmt=' - ' + other_faction.faction_name + ' - ')

            relations = faction.get_faction_relations(other_faction)

            if relations != {}:
                for reason, amt in relations.iteritems():
                    y += 1
                    libtcod.console_print(con=wpanel.con, x=2, y=y, fmt='   -' + reason + ': ' + str(amt))

            else:
                y += 1
                libtcod.console_print(con=wpanel.con, x=2, y=y, fmt='No real relationship')

            y += 1

    wpanel.update_render_text_func(func=render_text_func, args=())
    wpanel.gen_buttons = buttons


class Population:
    def __init__(self, char, name, faction, creatures, sentients, goods, wx, wy, site=None, commander=None):
        self.char = char
        self.name = name
        self.faction = faction
        self.creatures = creatures
        # {culture:{race:{profession: amount}}}
        self.sentients = sentients
        self.goods = goods

        self.wx = wx
        self.wy = wy
        WORLD.tiles[wx][wy].populations.append(self)

        self.world_last_dir = (0, -1)
        self.turns_since_move = 0

        self.site = site
        self.commander = commander
        if self.commander:
            self.commander.sapient.add_commanded_population(self)

    def w_teleport(self, x, y):
        WORLD.tiles[self.wx][self.wy].populations.remove(self)
        self.wx = x
        self.wy = y
        WORLD.tiles[self.wx][self.wy].populations.append(self)
        # Army status stuff
        self.world_last_dir = (0, 0)
        self.turns_since_move = 0


    def w_move(self, dx, dy):
        ''' Moves the population by the given xy coords, and handles updating the map info '''
        #move by the given amount, if the destination is not blocked
        if not WORLD.tile_blocks_mov(self.wx + dx, self.wy + dy):
            WORLD.tiles[self.wx][self.wy].populations.remove(self)
            self.wx += dx
            self.wy += dy
            WORLD.tiles[self.wx][self.wy].populations.append(self)

            # Army status stuff
            self.world_last_dir = (-dx, -dy)
            self.turns_since_move = 0


    def add_to_map(self, startrect, startbuilding, patrol_locations):
        ''' Add this population to the map '''
        allmembers = []

        for culture in self.sentients.keys():
            for race in self.sentients[culture].keys():
                for profession_name in self.sentients[culture][race].keys():
                    for i in xrange(self.sentients[culture][race][profession_name]):
                        born = roll(time_cycle.current_year - 45, time_cycle.current_year - 20)
                        human = culture.create_being(sex=1, born=born, char='o', dynasty=None, important=0, faction=self.faction, wx=self.wx, wy=self.wy, armed=1)
                        # TODO - this should be improved
                        human.sapient.commander = self.commander

                        profession = Profession(name=profession_name, category='commoner')
                        profession.give_profession_to(figure=human)

                        #if self.origin_city:
                        #    human.sapient.change_citizenship(new_city=self.origin_city, new_house=None)
                        allmembers.append(human)

        ####### PATROLS ####################
        for (lx, ly) in patrol_locations:
            radius = roll(35, 50)
            patrol_route = M.get_points_for_circular_patrol_route(center_x=lx, center_y=ly, radius=radius)
            game.add_message('Patrol route with radius of %i and length of %i generated'%(radius, len(patrol_route)), libtcod.orange)
            px, py = patrol_route[0]

            for i in xrange(3):
                figure = allmembers.pop(0)
                # Adding obj initializes the AI, so we can be ready to be setup for patrolling
                unblocked_locations = []
                for x in xrange(px-5, px+6):
                    for y in xrange(py-5, py+6):
                        if not M.tile_blocks_mov(x, y):
                            unblocked_locations.append((x, y))

                x, y = random.choice(unblocked_locations)
                M.add_object_to_map(x=x, y=y, obj=figure)

                figure.local_brain.set_state('patrolling', patrol_route=patrol_route)
        ####################################

        # Place somewhere in startling location that isn't blocked
        for figure in allmembers: #+ self.captives[:]:
            # Try 200 times to find a good spot in the starting area..
            found_spot = 0
            for counter in xrange(200):
                if startrect:
                    x, y = roll(startrect.x1, startrect.x2), roll(startrect.y1, startrect.y2)
                elif startbuilding:
                    x, y = random.choice(startbuilding.physical_property)
                if not M.tile_blocks_mov(x, y):
                    found_spot = 1
                    break
            ####### Safety step - couldn't find a valid location ########
            if not found_spot:
                print 'Could not place', figure.fulltitle(), 'attempting to place nearby'
                # Now keep picking vals at random across the entire map ... one's bound to work
                while 1:
                    x, y = roll(10, M.width-11), roll(10, M.height-11)
                    if not M.tile_blocks_mov(x, y):
                        break
            ###### end safety step #####################################
            #if figure in self.captives:
            #    game.add_message('{0} is a captive and at {1}, {2}'.format(figure.fulltitle(), figure.x, figure.y))

            M.add_object_to_map(x=x, y=y, obj=figure)




class Dynasty:
    def __init__(self, lastname, race):
        self.lastname = lastname
        self.race = race

        WORLD.dynasties.append(self)

        self.members = []

        self.symbol = None
        self.primary_color = None
        self.background_color = None
        self.create_crest()

    def create_crest(self):
        # A crest to display as the dynasty symbol
        if roll(1, 10) == 1:
            self.symbol = self.lastname[0]
        else:
            self.symbol = chr(random.choice(DYNASTY_SYMBOLS))

        self.symbol_color = random.choice(DARK_COLORS)
        self.background_color = random.choice(LIGHT_COLORS)

        #def display_symbol(self, panel, x, y):
        #libtcod.console_put_char_ex(panel, x, y, self.symbol, self.symbol_color, self.background_color)
        #libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

class Meeting:
    def __init__(self, name, leader, invitees, days_ahead, world_coords, place, reason, secret, importance):
        self.name = name
        self.leader = leader
        self.invitees = invitees
        self.world_coords = world_coords
        self.place = place
        self.reason = reason # tuple, index 0 is type (plot, etc), 1 is subtype (kill etc), 2 is target
        self.secret = secret
        self.importance = importance

        self.attending = [self.leader]

        (future_year, future_month, future_day) = time_cycle.days_to_date(days_in_advance=days_ahead)
        self.date = (future_year, future_month, future_day)
        time_cycle.add_event(date=(future_year, future_month, future_day), event=self.hold_meeting)
        ## Add to the leader's calendar too
        self.leader.sapient.add_event(date=(future_year, future_month, future_day), event=self)

        for figure in self.invitees:
            self.respond_to_meeting(figure)

    def respond_to_meeting(self, figure):
        # Really barebones for now
        self.attending.append(figure)


    def hold_meeting(self):
        game.add_message(''.join([self.leader.fullname(), ' is holding a meeting at ', self.place.get_name()]))
        if self.reason[0] == 'plot':
            if self.reason[1] == 'kill':
                name = ''.join(['Plot to kill ', self.reason[2].fullname()])

                plot = Plot(name=name, leader=self.leader, action=self.reason[1], target=self.reason[2],
                            members=self.attending)


class Plot:
    def __init__(self, name, leader, action, target, members):
        self.name = name
        self.leader = leader
        self.action = action
        self.target = target
        self.members = members

        self.chance_to_fire = 5
        self.chance_to_succeed = 20

        # Other init stuff
        self.target.sapient.targeted_plots.append({self: 0})
        WORLD.plots.append(self)

        for member in self.members:
            member.sapient.involved_plots.append(self)


    def check_for_fire(self):
        if roll(1, 100) <= self.chance_to_fire:
            game.add_message(''.join([self.name, 'has fired!']), libtcod.light_red)
            self.fire()

    def fire(self):
        success = 0
        if roll(1, 100) <= self.chance_to_succeed:
            success = 1

        if success:
            game.add_message(''.join([self.name, ' was successful!']), libtcod.light_red)
            if self.action == 'kill':
                self.target.sapient.die()

        else:
            game.add_message(''.join([self.name, ' was unsuccessful']), libtcod.red)

        for member in self.members:
            member.sapient.involved_plots.remove(self)
        WORLD.plots.remove(self)


class Goal:
    ''' This is the container for behaviors. It controls
    when each behavior becomes active (serially) '''
    def __init__(self, behavior_list, priority, reason):
        self.behavior_list = behavior_list
        for behavior in self.behavior_list:
            behavior.goal = self
        self.priority = priority
        self.reason = reason

    def get_name(self):
        return self.behavior_list[0].get_name()

    def take_goal_action(self):
        ''' Picks the behavior which is currently active and executes it'''
        behavior = self.behavior_list[0]

        if not behavior.is_active and not behavior.is_completed():
            behavior.initialize_behavior()

        # TODO - improve flow. Currently checks if it's complete before and
        # after taking the behavior action - the first time is to catch if
        # the behavior happens to occur at a time where it's already completed
        if not behavior.is_completed():
            behavior.take_behavior_action()
        # Important to put this here, so that it can again check the behavior after the action
        if behavior.is_completed():
            behavior.is_active= 0
            self.behavior_list.remove(behavior)

    def is_completed(self):
        return not(len(self.behavior_list))


class WaitBehavior:
    ''' Used anytime a figure wants to wait somewhere and do some activity '''
    def __init__(self, figure, location, num_days, travel_verb, activity_verb):
        self.goal = None # will be set when added to a Goal
        self.figure = figure
        self.location= location
        self.num_days = num_days
        self.num_days_left = num_days
        self.travel_verb = travel_verb
        self.activity_verb = activity_verb

        self.is_active = 0

    def get_name(self):
        if (self.figure.wx, self.figure.wy) != self.location:
            goal_name = '{0} to {1} to {2} for {3} days'.format(self.travel_verb, WORLD.tiles[self.location[0]][self.location[1]].get_location_description(), self.activity_verb, self.num_days)
        else:
            goal_name = '{0} in {1} for {2} days'.format(self.activity_verb, WORLD.tiles[self.location[0]][self.location[1]].get_location_description(), self.num_days)

        return goal_name

    def initialize_behavior(self):
        # If we're not in the location, travel there
        if (self.figure.wx, self.figure.wy) != self.location:
            self.goal.behavior_list.insert(0, MovLocBehavior(location=self.location, figure=self.figure, travel_verb=self.travel_verb))
            self.goal.behavior_list[0].initialize_behavior()

            game.add_message('{0} has decided to {1}'.format(self.figure.fulltitle(), self.get_name()), libtcod.color_lerp(PANEL_FRONT, self.figure.color, .5))
        else:
            self.is_active = 1

    def is_completed(self):
        return self.num_days_left == 0

    def take_behavior_action(self):
        self.num_days_left -= 1


class MovLocBehavior:
    ''' Specific behavior component for moving to an area.
    Will use road paths if moving from city to city '''
    def __init__(self, location, figure, travel_verb='travel'):
        self.x = location[0]
        self.y = location[1]
        # The object
        self.figure = figure
        self.travel_verb = travel_verb
        self.is_active = 0


    def get_name(self):
        goal_name = '{0} to {1}'.format(self.travel_verb, WORLD.tiles[self.x][self.y].get_location_description())
        return goal_name

    def initialize_behavior(self):
        ''' Will be run as soon as this behavior is activated '''
        self.is_active = 1
        ## Find path
        targeting_city = 0
        target_site = WORLD.tiles[self.x][self.y].site
        current_site = WORLD.tiles[self.figure.wx][self.figure.wy].site
        if target_site is not None and target_site in WORLD.cities:
            targeting_city = 1
        if targeting_city and (current_site is not None and current_site in WORLD.cities):
            # Pathfinding bit
            self.figure.world_brain.path = current_site.path_to[target_site][:]

        else:
            # Default - use libtcod's A* to create a path to destination
            path = libtcod.path_compute(p=WORLD.path_map, ox=self.figure.wx, oy=self.figure.wy, dx=self.x, dy=self.y)
            self.figure.world_brain.path = libtcod_path_to_list(path_map=WORLD.path_map)

        #self.name = 'move to {0}.'.format(WORLD.tiles[self.x][self.y].get_location_description())
        #game.add_message('{0} has decided to {1}'.format(self.figure.fulltitle(), self.get_name()), libtcod.color_lerp(PANEL_FRONT, self.figure.color, .5))

    def is_completed(self):
        return (self.figure.wx, self.figure.wy) == (self.x, self.y)

    def take_behavior_action(self):
        self.figure.w_move_along_path(path=self.figure.world_brain.path)


class MovTargBehavior:
    ''' Behavior for moving to something that's not a city (a historical figure, perhaps)'''
    def __init__(self, target, figure):
        self.target = target
        # The object
        self.figure = figure

        self.is_active = 0

    def initialize_behavior(self):
        ''' Will be run as soon as this behavior is activated '''
        self.is_active= 1
        if (self.figure.wx, self.figure.wy) == (self.target.x, self.target.y):
            game.add_message(self.figure.fulltitle() + ' tried moving to ' + self.target.fulltitle() + ' but was already there')

    def is_completed(self):
        return self.figure.wx == self.target.wx and self.figure.wy == self.target.wy

    def take_behavior_action(self):
        # TODO - not magically knowing where the target is....
        path = libtcod.path_compute(p=WORLD.path_map, ox=self.figure.wx, oy=self.figure.wy, dx=self.target.wx, dy=self.target.wy)

        x, y = libtcod.path_walk(WORLD.path_map, True)
        if x != None:
            self.figure.w_move_to(x, y)

class UnloadGoodsBehavior:
    def __init__(self, target_city, figure):
        self.target_city = target_city
        self.figure = figure
        self.is_active = 0

    def initialize_behavior(self):
        self.is_active= 1

    def is_completed(self):
        return self.figure in self.target_city.caravans

    def take_behavior_action(self):
        if self.figure not in self.target_city.caravans:
            self.target_city.receive_caravan(self.figure)
        else:
            game.add_message('{0} tried to unload caravan goods and was already in {1}.caravans'.format(self.figure.fulltitle(), self.target_city.name), libtcod.red)

class KillTargBehavior:
    ''' Behavior for moving to something that's not a city (a historical figure, perhaps)'''
    def __init__(self, target, figure):
        self.target = target
        # The object
        self.figure = figure

        self.is_active = 0

    def initialize_behavior(self):
        self.is_active= 1

    def is_completed(self):
        return self.target.creature.status == 'dead'

    def take_behavior_action(self):
        if roll(0, 1):
            self.target.sapient.die()


class CaptureTargBehavior:
    ''' Behavior for capturing a target '''
    def __init__(self, target, figure):
        self.target = target
        # The object
        self.figure = figure

        self.is_active = 0

    def initialize_behavior(self):
        self.is_active= 1

    def is_completed(self):
        return self.target in self.figure.sapient.captives

    def take_behavior_action(self):
        pass

class ImprisonTargBehavior:
    ''' Behavior for moving a captive from an ary into a building '''
    def __init__(self, target, figure, building):
        self.target = target
        # The object
        self.figure = figure
        self.building = building

        self.is_active = 0

    def initialize_behavior(self):
        self.is_active= 1

    def is_completed(self):
        if self.target in self.building.captives:
            game.add_message('WOOT', libtcod.dark_chartreuse)

        return self.target in self.building.captives

    def take_behavior_action(self):
        pass
        #self.figure.sapient.army.transfer_captive_to_building(figure=self.target, target_building=self.building)


class SapientComponent:
    def __init__(self, firstname, lastname, culture, born, dynasty, important=0):
        self.culture = culture
        self.born = born

        self.dynasty = dynasty

        self.important = important
        self.generation = 0

        # Relationships with others beyond trait clashes
        self.extra_relations = {}
        self.knowledge = {}
        # People we've recently conversed with
        self.recent_interlocutors = []
        # Pending conversation responses
        self.pending_conversations = []

        # Stuff for capturing people
        self.captor = None
        # Keeps track of people who are captive, even if they're not directly with us
        # (like they're in our house or something)
        self.captives = []

        self.faction = None
        # Sort of ugly, but a sapient needs to know if they are a faction leader
        self.is_faction_leader = 0

        #self.army = None
        self.commander = None
        self.commanded_populations = []
        self.commanded_figures = []

        self.economy_agent = None

        self.enemy_factions = set([])

        self.hometown = None # Where we originally were from
        self.current_citizenship = None # The city where our house is currently located
        self.current_lodging = None # The place where we are currently staying - will be None when travelling,
        # our house if we're in our home city, or can be an inn

        self.firstname = firstname
        self.lastname = lastname
        self.epithet = None

        # Family stuff
        self.mother = None
        self.father = None
        self.spouse = None
        self.children = []
        self.siblings = []
        self.inheritance = {} # dict

        self.house = None
        self.profession = None

        self.traits = {}
        self.skills = {'Charisma': 5, 'Command': 5, 'Management': 5, 'Piety': 5, 'Subterfuge': 5}
        self.goals = []

        self.targeted_plots = [] # List of dicts for plots targeting us, key = plot, val = 0 or 1, whether we know about it or not
        self.involved_plots = [] # List of plots

        self.events = {}
        self.is_plotting = 0

        self.gold = 1000
        # Objects that we own
        self.possessions = set([])
        self.former_possessions = set([])

        # Pick some traits
        self.set_initial_traits()
        ## Set initial opinions - this is without having a profession
        self.set_opinions()

    def add_enemy_faction(self, faction):
        self.enemy_factions.add(faction)

    def remove_enemy_faction(self, faction):
        self.enemy_factions.remove(faction)

    def set_as_faction_leader(self, faction):
        self.is_faction_leader = faction

    def unset_as_faction_leader(self, faction):
        self.is_faction_leader = None


    def is_commander(self):
        return len(self.commanded_figures) or len(self.commanded_populations)

    def get_total_number_of_commanded_beings(self):
        ''' Returns the number of beings under tis character's command'''
        if self.is_commander():
            number_of_figures = len(self.commanded_figures)
            total_number = number_of_figures + 1 #(add 1, which is ourself)
            # Dig down into the population breakdown to get the total number
            for population in self.commanded_populations:
                for culture in population.sentients.keys():
                    for race in population.sentients[culture].keys():
                        for profession_name in population.sentients[culture][race].keys():
                            total_number += population.sentients[culture][race][profession_name]
        # If we're not a commander, return 0, meaning no men under our command
        else:
            total_number = 0

        return total_number

    def add_commanded_figure(self, figure):
        figure.sapient.commander = self.owner
        self.commanded_figures.append(figure)

    def remove_commanded_figure(self, figure):
        figure.sapient.commander = None
        self.commanded_figures.remove(figure)

    def add_commanded_population(self, population):
        population.commander = self.owner
        self.commanded_populations.append(population)

    def remove_commanded_population(self, population):
        population.commander = None
        self.commanded_populations.remove(population)

    #def handle_question(self, asker, target, question_type):
    #    ''' Handles all functions relating to asking questions '''
    #    # First determine answer ('no response', 'truth', later will implement 'lie')
    #    # This also handles updating knowledge
    #    answer_type = self.ask_question(asker=asker, target=target, question_type=question_type)
    #    # Verbal responses to the questions
    #    if player in self.participants:
    #        self.verbalize_question(asker=asker, target=target, question_type=question_type)
    #        self.verbalize_answer(asker=asker, target=target, question_type=question_type, answer_type=answer_type)

    def ask_question(self, target, question_type):
        ''' Handles the information transfer between questions.
        The verbalization component is handled in the "verbalize" functions '''
        # Send the prompt over to the target
        self.verbalize_question(target, question_type)

        target.sapient.pending_conversations.append((self.owner, question_type))

        # TODO - move this player-specific bit somewhere where it makes more sense?
        if self.owner == player:
            game.player_advance_time(ticks=1)


    def verbalize_question(self, target, question_type):
        # Ask the question
        game.add_message(self.owner.fullname() + ': ' + CONVERSATION_QUESTIONS[question_type], libtcod.color_lerp(self.owner.color, PANEL_FRONT, .5))


    def verbalize_answer(self, asker, question_type, answer_type):
        ''' Sending the answer through the game messages '''

        if answer_type == 'no answer':
            self.say('I don\'t want to tell you that.')

        elif answer_type == 'truth':
            if question_type == 'name':
                self.say('My name is %s.' % self.owner.fullname() )

            elif question_type == 'profession':
                if self.profession:
                    self.say('I am a %s.' % self.profession.name)
                else:
                    self.say('I do not have any profession.')

            elif question_type == 'age':
                age = self.get_age()
                self.say('I am %i.' % age)

            elif question_type == 'city':
                current_citizen_of = self.current_citizenship

                if current_citizen_of:
                    self.say('I currently live in %s.' % current_citizen_of.name)
                else:
                    self.say('I currently do not hold any citizenship.')

            elif question_type == 'goals':
                if len(self.owner.world_brain.goals):
                    if len(self.owner.world_brain.goals) == 1:
                        self.say('My current goal is to {0}.'.format(self.owner.world_brain.goals[0].get_name()) )
                    elif len(self.owner.world_brain.goals) > 1:
                        goal_names = join_list([g.get_name() for g in self.owner.world_brain.goals[1:]])
                        self.say('My current plan is to {0}. Later, I\'m going to {1}'.format(self.owner.world_brain.goals[0].get_name(), goal_names))
                # IF we're travelling under someone's command
                elif self.commander and len(self.commander.world_brain.goals):
                    if len(self.commander.world_brain.goals) == 1:
                        self.say('I\'m with {0}. Our current plan is to {1}.'.format(self.commander.fullname(), self.commander.world_brain.goals[0].get_name()) )
                    elif len(self.commander.world_brain.goals) > 1:
                        goal_names = join_list([g.get_name() for g in self.commander.world_brain.goals[1:]])
                        self.say('I\'m with {0}. Our current plan is to {1}. Later, we\'ll {2}'.format(self.commander.fullname(), self.commander.world_brain.goals[0].get_name(), goal_names))
                else:
                    self.say('I don\'t really have any goals at the moment.')

        ## Shouldn't break the mold here... but answer_type is different
        if question_type == 'recruit':
            if answer_type == 'yes':
                self.say('I will gladly join you!')
                ### TODO - put this into a function!
                self.profession = Profession('Adventurer', 'commoner')
                player.sapient.add_commanded_figure(self.owner)

            elif answer_type == 'no':
                ## Decline, with a reason why
                if self.commander:
                    self.say('I am already a member of %s.' % self.commander.name)
                elif self.get_profession:
                    self.say('As a %s, I cannot join you.' % self.get_profession() )
                else:
                    self.say('I cannot join you.')

        # Same with greetings...
        elif question_type == 'greet':
            if answer_type == 'return greeting':
                self.say('Hello there.')
            elif answer_type == 'no answer':
                self.nonverbal_behavior('does not answer')
            elif answer_type == 'busy':
                self.say('I\m sorry, I am busy right now.')


    def get_valid_questions(self, target):
        ''' Valid questions to ask '''
        valid_questions = []
        if target not in self.recent_interlocutors:
            return ['greet']

        if target not in self.knowledge.keys():
            return ['name']

        if self.knowledge[target]['city'] == None:
            valid_questions.append('city')

        if self.knowledge[target]['age'] == None:
            valid_questions.append('age')

        if self.knowledge[target]['profession'] == None:
            valid_questions.append('profession')

        if self.knowledge[target]['goals'] == None:
            valid_questions.append('goals')

        ## TODO - allow NPCs to recruit, under certain circumstances
        if self.is_commander() and target.sapient.commander != self.owner and self.owner == player:
            valid_questions.append('recruit')

        return valid_questions


    #def get_valid_topics(self, target):
    #    ''' Valid topics of conversation '''
    #    return self.topics

    #def change_topic(self, topic):
    #    self.topic = topic
    #    game.add_message('You begin talking about ' + self.topic + '.', libtcod.color_lerp(player.color, PANEL_FRONT, .5))


    def determine_response(self, asker, question_type):

        if question_type == 'greet':
            self.recent_interlocutors.append(asker)
            asker.sapient.recent_interlocutors.append(self.owner)

            return 'return greeting'

        elif question_type == 'name':
            ''' Ask the target's name '''
            asker.sapient.meet(self.owner)

            return 'truth'

        elif question_type == 'profession':
            ''' Ask about their profession '''
            profession = self.profession
            if profession is None:
                profession = 'No profession'

            asker.sapient.add_person_knowledge(other_person=self.owner, info_type=question_type, info=profession)

            return 'truth'

        elif question_type == 'age':
            ''' Ask about their profession '''
            age = self.get_age()

            asker.sapient.add_person_knowledge(other_person=self.owner, info_type=question_type, info=age)
            return 'truth'

        elif question_type == 'city':
            ''' Ask about the city they live in '''

            current_citizen_of = self.current_citizenship
            if current_citizen_of is None:
                current_citizen_of = 'No citizenship'

            asker.sapient.add_person_knowledge(other_person=self.owner, info_type=question_type, info=current_citizen_of)

            return 'truth'

        elif question_type == 'goals':
            ''' Ask about their goals '''

            goals = []
            if len(self.goals):
                for goal in self.goals:
                    goals.append(goal)

            asker.sapient.add_person_knowledge(other_person=self.owner, info_type=question_type, info=goals)

            return 'truth'

        elif question_type == 'recruit':
            ''' Try to recruit person into actor's party '''
            if self.get_age() >= MIN_MARRIAGE_AGE and (self.owner.creature.sex == 1 or self.spouse == None) \
                and self.profession == None and not self.commander:
                return 'yes'

            else:
                return 'no'


    def handle_pending_conversations(self):
        for (asker, question_type) in self.pending_conversations:

            #if self.owner == player:
                ## TODO - prompt GUI for player to choose his answer
            #    answer_type = self.determine_response(asker, question_type)
            #    self.verbalize_answer(asker, question_type, answer_type)
            #else:

            answer_type = self.determine_response(asker, question_type)
            self.verbalize_answer(asker, question_type, answer_type)

            # GUI stuff - must update when NPC gives response
            if asker == player:
                for panel in interface.get_panels(panel_name='talk_screen'):
                    panel.button_refresh_func(*panel.button_refresh_args)


        self.pending_conversations = []

    #def score_question(self, conversation, asker, target, question_type):
    #    score = 5
    #    return score

    def say(self, text_string):
        msg_color = libtcod.color_lerp(self.owner.color, PANEL_FRONT, .5)

        game.add_message('{0}: {1}'.format(self.owner.fullname(), text_string), msg_color)

    def nonverbal_behavior(self, behavior, msg_color=None):
        ''' Any nonverbal behavior that this creature can undertake '''
        if msg_color is None:
            msg_color = libtcod.color_lerp(self.owner.color, PANEL_FRONT, .5)

        game.add_message('%s %s.' % (self.owner.fullname(), behavior), msg_color)

    def verbalize_pain(self, damage, sharpness, pain_ratio):
        ''' The creature will verbalize its pain '''
        # Damage/pain ratio are decimals, so divide and multiply are opposite
        pain_composite = (damage * 3) + (pain_ratio / 2)
        will_verbalize = roll(1, 100) <= (pain_composite * 100)
        #will_verbalize = 1

        if will_verbalize:
            if pain_composite > .8:
                self.nonverbal_behavior('lets loose a bloodcurdling scream')
            elif pain_composite > .7:
                self.nonverbal_behavior('lets loose a shrill scream')
            elif pain_composite > .6:
                self.nonverbal_behavior('screams in pain')
            elif pain_composite > .5:
                self.nonverbal_behavior('screams')
            elif pain_composite > .4:
                self.nonverbal_behavior('grunts loudly')
            elif pain_composite > .3:
                self.nonverbal_behavior('grunts')

    def take_captive(self, figure):
        figure.sapient.captor = self.owner
        self.captives.append(figure)

    def is_captive(self):
        ''' Function simply returns whether or not this guy is a captive '''
        return self.captor is not None

    def sapient_free_from_captivity(self):
        ''' Handles setting a sapient free from captivity, and making sure any army holding it captive is also properly handled '''
        if self.captor.sapient.army and self.owner in self.captor.sapient.army.captives:
            self.captor.sapient.army.captives.remove(self.owner)

        self.captor.sapient.captives.remove(self.owner)
        self.captor = None

        # Unsure if this will work properly, but, once freed, all sapients should re-evaluate to make sure captives show up as enemies properly
        for figure in M.sapients:
            if figure.local_brain:
                figure.local_brain.set_enemy_perceptions_from_cached_factions()
        ############################################################

        self.say('I\'m free!')


    def is_available_to_act(self):
        ''' Way to check whether the figure can act of their own accord.'''
        return not (self.is_captive() or self.owner.creature.status == 'dead')

    def change_citizenship(self, new_city, new_house):
        ''' Transfer citizenship from one city to another '''
        # Remove from old citizenship
        if self.current_citizenship:
            # TEMP FIX
            try:
                self.current_citizenship.citizens.remove(self.owner)
            except:
                game.add_message('{0} says it is citizen of {1} but not in list'.format(self.owner.fulltitle(), self.current_citizenship.name), libtcod.red)
        # Remove old housing stuff
        if self.house:
            self.house.remove_inhabitant(self.owner)
        # Remove old faction stuff
        if self.faction:
            self.faction.remove_member(self.owner)
        # Change to new city, and add to that city's citizens
        if new_city is not None:
            self.current_citizenship = new_city
            new_city.citizens.append(self.owner)
            new_city.faction.add_member(self.owner)
        ## Otherwise switch to the faction that owns the house you're moving to
        elif new_house.faction:
            new_house.faction.add_member(self.owner)

        self.house = new_house
        if self.house:
            self.house.add_inhabitant(self.owner)

    def get_minor_successor(self):
        ''' A way for minor figures to pass down their profession, in cases where it's not a huge deal'''
        possible_successors = [child for child in self.children if
                               child.creature.sex == 1 and child.sapient.get_age() >= MIN_MARRIAGE_AGE]
        if possible_successors != []:
            return possible_successors[0]
        else:
            return self.current_citizenship.create_inhabitant(sex=1, born=time_cycle.years_ago(18, 35), char='o', dynasty=None, important=self.important)

    def add_event(self, date, event):
        ''' Should add an event to our memory'''
        (year, month, day) = date
        if (year, month, day) in self.events.keys():
            self.events[(year, month, day)].append(event)
        else:
            self.events[(year, month, day)] = [event]


    def die(self):
        figure = self.owner
        figure.creature.status = 'dead'
        #print figure.fulltitle(), ', gen', str(self.generation), 'has died'
        if WORLD.tiles[figure.wx][figure.wy].site:  location = WORLD.tiles[figure.wx][figure.wy].site.name
        else:                                       location = 'the wilderness'

        # Notify world!
        game.add_message('{0} has died in {1}!'.format(figure.fulltitle(), location), libtcod.red)

        # Remo
        if figure.sapient.current_citizenship:
            figure.sapient.current_citizenship.citizens.remove(figure)

        # Remove from the list of all figures, and the important ones if we're important
        WORLD.all_figures.remove(figure)
        if figure in WORLD.important_figures:
            WORLD.important_figures.remove(figure)

        if self.faction:
            self.faction.remove_member(figure)

        successor = None
        # The faction lead passes on, if we lead a faction
        if self.is_faction_leader:
            self.is_faction_leader.standard_succession()

        # Only check profession if we didn't have a title, so profession associated with title doesn't get weird
        elif self.profession:
            # Find who will take over all our stuff
            successor = self.get_minor_successor()
            self.profession.give_profession_to(successor)

        ## If we were set to inherit anything, that gets updated now
        #  File "E:\Dropbox\Code\Iron Testament\it.py", line 8650, in year_tick
        #    if figure.sapient.get_age() > 70:
        #    File "E:\Dropbox\Code\Iron Testament\it.py", line 7485, in die
        #    RuntimeError: dictionary changed size during iteration
        for faction, position in self.inheritance.iteritems():
            heirs = faction.get_heirs(3) # Should ignore us now since we're dead
            # If our position was 1st in line, let the world know who is now first in line
            if position == 1 and heirs != []:
                game.add_message('After the death of {0}, {1} is now the heir of {2}.'.format(figure.fulltitle(), heirs[0].fullname(), faction.faction_name), libtcod.light_blue)

            elif position == 1:
                game.add_message('After the death of {0}, no heirs to {1} remiain'.format(figure.fulltitle(), faction.faction_name), libtcod.light_blue)


        # Remove self from any armies we might be in
        if figure.sapient.commander:
            if self in figure.sapient.commander.sapient.commanded_figures:
                figure.sapient.commander.remove_commanded_figure(figure)
        elif figure.sapient.is_commander():
            ## The is a possibility that this is a caravan at another city; this will bring the successor there if needed
            # TODO - should just have the person walk there and join up with the army
#             if successor:
#                 ## Pretty ugly hack for now. When a merchant dies naturally, we're gonna teleport
#                 ## a successor to his location. In order to do this, we may have to leave our
#                 ## current city and then get added to the new city.
#                 try:
#                     for city in WORLD.cities:
#                         if army in city.caravans and successor.sapient.current_city != city:
#                             print '%s was teleported to %s upon the death of %s'%(successor.fulltitle(), city.name, figure.fulltitle())
#                             break
#                 except:
#                     print ('%s, successor to %s, looked for caravan in %s but something went wrong!'%(successor.fulltitle(), figure.fulltitle(), city.name))
#
#                 # Actually join the army
#                 successor.sapient.join_army(army)


            if figure.sapient.economy_agent and successor:
                figure.sapient.economy_agent.update_holder(successor)
                #game.add_message(successor.fulltitle() + ' is now ' + successor.sapient.economy_agent.name, libtcod.light_green)

        if self.house:
            try:
                self.house.remove_inhabitant(figure)
            except:
                print figure.fulltitle(), 'was not in his house!'
                game.add_message(figure.fulltitle(), 'was not in his house!')

    def get_age(self):
        return time_cycle.current_year - self.born

    def get_profession(self):
        if self.profession:
            return self.profession.name
        elif self.owner.creature.sex == 0 and self.spouse:
            return 'Housewife'
        elif self.get_age() < MIN_CHILDBEARING_AGE:
            return 'Child'
        return 'No profession'

    def take_spouse(self, spouse):
        self.spouse = spouse
        spouse.sapient.spouse = self.owner

    def have_child(self):

        child = self.current_citizenship.create_inhabitant(sex=roll(0, 1), born=time_cycle.current_year, char='o',
                                                           dynasty=self.spouse.sapient.dynasty, race=self.owner.creature.creature_type, important=self.important)

        self.children.append(child)
        self.spouse.sapient.children.append(child)

        child.sapient.mother = self.owner
        child.sapient.father = self.spouse

        child.sapient.generation = self.spouse.sapient.generation + 1

        return child

    def set_initial_traits(self):
        ## Give the person a few traits
        trait_num = roll(3, 4)
        while trait_num > 0:
            trait = random.choice(TRAITS)

            usable = 1
            for otrait in self.traits:
                if trait in TRAIT_INFO[otrait]['opposed_traits'] or trait == otrait:
                    usable = 0
                    break
            if usable:
                # "Somewhat = .5, regular = 1, "very" = 2
                multiplier = random.choice([.5, .5, 1, 1, 1, 1, 2])
                self.traits[trait] = multiplier
                trait_num -= 1
                #t_ind = TRAITS.index(trait)
                ## Some traits modify skills
                #for skill in TRAIT_INFO[t_ind].skill_modifiers.keys():
                #    self.modify_skill(skill, TRAIT_INFO[t_ind].skill_modifiers[skill])

    def set_opinions(self):
        # Set opinions on various things according to our profession and personality
        self.opinions = {}

        for issue in PROF_OPINIONS.keys():
            prof_opinion = 0
            personal_opinion = 0
            reasons = {}

            ## Based on profession ##
            if self.profession != None and self.profession.category in PROF_OPINIONS[issue].keys():
                prof_opinion = PROF_OPINIONS[issue][self.profession.category]
                reasons['profession'] = prof_opinion

            ## Based on personal traits ##
            for trait, multiplier in self.traits.iteritems():
                if trait in PERSONAL_OPINIONS[issue].keys():
                    amount = PERSONAL_OPINIONS[issue][trait] * multiplier
                    reasons[trait] = amount
                    personal_opinion += amount

            # A total tally of the opinion
            opinion = prof_opinion + personal_opinion
            # Now we save the issue, our opinion, and the reasoning
            self.opinions[issue] = [opinion, reasons]



    def add_person_knowledge(self, other_person, info_type, info):
        ''' Checks whether we know of the person and then updates info '''
        if not other_person in self.knowledge.keys():
            self.add_awareness_of_person(other_person)

        self.knowledge[other_person][info_type] = info


    def get_relations(self, other_person):
        # set initial relationship with another person
        # Needs to be greatly expanded, and able to see reasons why
        reasons = {}

        for trait, multiplier in self.traits.iteritems():
            for otrait in other_person.sapient.traits.keys():
                if trait == otrait:
                    reasons['Both ' + trait] = 4 * multiplier
                    break
                elif trait in TRAIT_INFO[otrait]['opposed_traits']:
                    reasons[trait + ' vs ' + otrait] = -2 * multiplier
                    break

        # Things other than traits can modify this, must be stored in self.extra_relations
        # Basically merge this into the "reasons" dict
        if other_person in self.knowledge.keys():
            for reason, amount in self.knowledge[other_person]['relations'].iteritems():
                reasons[reason] = amount

        return reasons


    def modify_relations(self, other_person, reason, amount):
        # Anything affecting relationship not covered by traits

        # Add them to relation list if not already there
        if not other_person in self.knowledge.keys():
            self.add_awareness_of_person(other_person)

        # Then add the reason
        if not reason in self.knowledge[other_person]['relations'].keys():
            self.knowledge[other_person]['relations'][reason] = amount
        else:
            self.knowledge[other_person]['relations'][reason] += amount

    def add_awareness_of_person(self, other_person):
        ''' To set up the knowledge dict '''
        self.knowledge[other_person] = {'relations':{},
                                        'profession':None,
                                        'age':None,
                                        'city':None,
                                        'goals':None
                                        }

    def modify_skill(self, skill, amount):
        if skill in self.skills.keys():
            self.skills[skill] += amount
        else:
            self.skills[skill] = amount

    def meet(self, other):
        # Use to set recipricol relations with another person
        self.modify_relations(other, 'Knows personally', 2)
        other.sapient.modify_relations(self.owner, 'Knows personally', 2)


class Creature:
    def __init__(self, creature_type, sex, intelligence_level):
        self.creature_type = creature_type
        self.sex = sex
        self.intelligence_level = intelligence_level

        self.next_tick = 1
        self.turns_since_move = 0


        self.current_weapon = None
        self.status = 'alive'

        self.cskills = {'Mobility': 10,
                        'Fighting': 10,
                        'Reflexes': 10,
                        'Hand-Eye Coordination':10
        }

        self.catts = {'Fortitude':10,
                       'Stamina':10,
                       'Move Speed':1,
                       'Attack Speed':1
                       }


        self.alert_sight_radius = 60
        self.unalert_sight_radius = 30
        #self.move_action_pool = 0
        #self.attack_action_pool = 0

        self.energy = 10
        self.pain = 0
        ## Blood ##
        self.blood = 5.6 # in liters - should also scale with body's volume
        self.max_blood = self.blood
        self.bleeding = 0
        self.clotting = .05

        self.set_stance(random.choice(('Aggressive', 'Defensive')) )
        # 8 cardinal directions, 0 = north, every +1 is a turn clockwise
        self.facing = 0

        # To be set later
        self.dijmap_desires = {}

        # To be set when it is added to the object component
        self.owner = None

    def check_to_perceive(self, other_creature):

        perceived = 0
        threat_level = -1

        if self.owner.distance_to(other_creature) < self.unalert_sight_radius:
            line = libtcod.line_init(self.owner.x, self.owner.y, other_creature.x, other_creature.y)
            perceived = 1
            # Raycast from our position to see if any obstacles block our vision
            x, y = libtcod.line_step()
            while x is not None:
                if M.tile_blocks_sight(x, y):
                    perceived = 0
                    break

                x, y = libtcod.line_step()

        return perceived, threat_level

    def set_initial_desires(self):

        ## TODO - more elegant way to become aware of all factions
        ## !! currently doesn't know about any factions other than ourselves and enemies
        self.dijmap_desires =     {
                                   self.owner.sapient.faction.faction_name:0,
                                   'map_center':0
                                  }


        for faction in self.owner.sapient.enemy_factions:
            self.dijmap_desires[faction.faction_name] = 0


    def handle_tick(self):

        #self.move_action_pool += self.catts['Move Speed']
        #self.attack_action_pool += self.catts['Attack Speed']


        if self.bleeding:
            self.bleed()
            ## Add some blood
            #blood_amt = min(actor.creature.bleeding/100, 1)
            blood_amt = .1
            #M.tiles[self.owner.x][self.owner.y].color = libtcod.color_lerp(M.tiles[self.owner.x][self.owner.y].color, libtcod.darker_red, blood_amt)
            M.tiles[self.owner.x][self.owner.y].set_color(color=libtcod.color_lerp(M.tiles[self.owner.x][self.owner.y].color, libtcod.darker_red, blood_amt) )


    def set_status(self, status):
        self.status = status

    def set_stance(self, stance):
        self.stance = stance

    def get_graspers(self):
        return [component for component in self.owner.components if 'grasp' in component.functions]

    def get_defense_score(self):

        return_dict = {
                       'Mobility skill':self.cskills['Mobility'],
                       'Fighting skill':self.cskills['Fighting'],
                       'Reflexes skill':self.cskills['Reflexes']
                       }

        return return_dict


    def get_attack_score(self, verbose=0):

        return_dict = {self.stance + ' stance':STANCES[self.stance]['attack_bonus'],
                       'Fighting skill':self.cskills['Fighting']
                       }

        return return_dict

    def get_current_weapon(self):
        if self.current_weapon is not None:
            return self.current_weapon

        elif self.current_weapon is not None:
            # See if we're holding any item
            for grasper in self.get_graspers():
                if grasper.grasped_item is not None:
                    return grasper.grasped_item

        ## TODO - this is weird...
        ## Kind of simulates unarmed combat - will return the object and thus use the first component as a weapon
        else:
            return self.owner
        #return None

    def dijmap_move(self):
        """ Move via use of dijisktra maps. There's a separate map for each desire, and we just sum
        each map, multiply by the weight of each desire, and roll downhill """
        current_tile_cost = 0
        i, j = (self.owner.x, self.owner.y)
        nx = i
        ny = j

        for desire, amount in self.dijmap_desires.iteritems():
            current_tile_cost += (M.dijmaps[desire].dmap[i][j] * amount)

        for (x, y) in ( (i - 1, j - 1), (i, j - 1), (i + 1, j - 1),
                        (i - 1, j),                 (i + 1, j),
                        (i - 1, j + 1), (i, j + 1), (i + 1, j + 1) ):

            if M.is_val_xy((x, y)) and not M.tile_blocks_mov(x, y): #not M.tiles[x][y].blocked:
                ## Check each desire, multiply by amount, and save if necessary
                weighted_desire = 0
                for desire, amount in self.dijmap_desires.iteritems():
                    weighted_desire += (M.dijmaps[desire].dmap[x][y] * amount)
                    ## Only move if we have a reason to
                if weighted_desire < current_tile_cost:
                    current_tile_cost = weighted_desire
                    nx, ny = (x, y)

        if (nx, ny) != (self.owner.x, self.owner.y):
            # Once the spot is picked, move there
            self.owner.abs_pos_move(x=nx, y=ny)

            self.turns_since_move = 0
        else:
            self.turns_since_move += 1


    def face(self, other):
        # Face an object
        # Start by calculating where we'd have to move
        dx = other.x - self.owner.x
        dy = other.y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        self.facing = NEIGHBORS.index((dx, dy))


    def get_attack_odds(self, attacking_object_component, force, target, target_component):
        ''' Gets attack odds, returning a breakdown as a dict if verbose is selected '''

        attack_score = self.get_attack_score()

        if target.creature:
            defend_score = target.creature.get_defense_score()
        else:
            defend_score = {}

        # Compare volume of volume of the creature to the volume of the target component
        # This difference becomes a defense modifier
        if target_component:
            #volume_mod = int( (target_component.get_volume() / self.owner.get_volume()) )
            volume_mod = int( self.owner.get_volume() / target_component.get_volume() )
            #print volume_mod

            defend_score['Vol. size bonus'] = volume_mod

        return attack_score, defend_score



    def handle_renegade_faction(self, target):
        utterance = random.choice(('HEY!', 'WHAT ARE YOU DOING?!', 'AAAAHHHH!!!'))
        target.sapient.say(utterance)

        if target.creature.current_weapon is not None and target.creature.current_weapon.weapon:
            target.local_brain.set_state('attacking')
        else:
            target.local_brain.set_state('fleeing')


    def standard_combat_attack(self, attacking_object_component, force, target, target_component):
        ''' Calculates whether an attack will hit or not '''

        if target.sapient and target.local_brain and target.local_brain.ai_state == 'idle':
            self.handle_renegade_faction(target)


        attack_modifiers, defend_modifiers = self.get_attack_odds(attacking_object_component, force, target, target_component)

        attack_chance = sum(attack_modifiers.values())
        defend_chance = sum(defend_modifiers.values())

        if roll(1, attack_chance + defend_chance) < attack_chance:
            # Attack hits!

            # Lists the top layers (outermost layer first)
            layers = target_component.get_coverage_layers()

            chances_to_hit = []
            running_coverage_amt = 0
            for layer, coverage_amt in layers:
                # Chance to hit is this layer's coverage minus previous layer's coverage
                # Exception - if this layer's coverage is smaller, it's essentially un-hittable
                # TODO - ensure that chance_to_hit and running_coverage_amt work correctly with layers with weird cvg amounts
                chance_to_hit = max(coverage_amt, running_coverage_amt) - running_coverage_amt
                running_coverage_amt += chance_to_hit

                chances_to_hit.append((layer, chance_to_hit))

            #print chances_to_hit
            # Weighted choice, from stackoverflow
            targeted_layer = weighted_choice(chances_to_hit)

            # Use the poorly-written physics module to compute damage
            targeted_layer.apply_force(other_obj_comp=attacking_object_component, total_force=force)

    def cause_to_bleed(self, damage, sharpness):
        #self.bleeding = min(damage*sharpness, self.max_blood)
        self.bleeding = min(sharpness-1, self.max_blood)

    def bleed(self):
        ''' Taking damage can cause us to bleed, this function handles that '''
        self.blood = max(self.blood - self.bleeding, 0)
        # Clot
        self.bleeding = max(self.bleeding - self.clotting, 0)

        # Do we die?
        if self.blood < 2 and self.status == 'alive':
            self.pass_out(reason='loss of blood')
        elif self.blood < 1:
            self.map_death(reason='blood loss')


    def increment_pain(self, damage, sharpness):
        self.pain = min(self.pain + damage, self.get_max_pain() )

        if sharpness > 1:
            self.cause_to_bleed(damage, sharpness)

        self.handle_pain_effects(damage, sharpness)

    def get_pain(self):
        return self.pain

    def get_max_pain(self):
        return 1 + int(self.catts['Fortitude']/10)

    def get_pain_ratio(self):
        return self.get_pain() / self.get_max_pain()

    def handle_pain_effects(self, damage, sharpness):
        pain_ratio = self.get_pain_ratio()

        # Potentially pass out
        if pain_ratio > .95 and self.status == 'alive':
            self.pass_out(reason='pain')

        if self.status == 'alive' and self.owner.sapient:
            self.owner.sapient.verbalize_pain(damage, sharpness, pain_ratio)


    def pass_out(self, reason):
        self.set_status('unconscious')
        self.set_stance('Prone')

        # Drop any things we have
        for component in self.get_graspers():
            if component.grasped_item is not None:
                # Drop the object (and release hold on it)
                self.owner.drop_object(own_component=component, obj=component.grasped_item)

        self.owner.set_display_color(self.owner.pass_out_color)
        self.owner.sapient.nonverbal_behavior('passes out due to %s' %reason, libtcod.darker_red)


    def map_death(self, reason):
        ''' Die ! '''
        creature_obj = self.owner
        self.set_status('dead')

        # Drop any things we have
        for component in self.get_graspers():
            if component.grasped_item is not None:
                # Drop the object (and release hold on it)
                creature_obj.drop_object(own_component=component, obj=component.grasped_item)

        if creature_obj.sapient.commander and self.owner in creature_obj.sapient.commander.commanded_figures:
            creature_obj.sapient.commander.sapient.remove_commanded_figure(creature_obj)

        M.sapients.remove(creature_obj)
        M.objects.append(creature_obj)

        if creature_obj.creature:
            game.add_message('{0} has died due to {1}'.format(creature_obj.fulltitle(), reason), libtcod.darker_red)

        creature_obj.set_display_color(creature_obj.death_color)
        creature_obj.blocks_mov = False
        creature_obj.local_brain = None
        libtcod.map_set_properties(M.fov_map, creature_obj.x, creature_obj.y, True, True)
        creature_obj.name = 'Corpse of {0}'.format(creature_obj.fulltitle())


class DijmapSapient:
    ''' AI using summed dij maps '''
    def __init__(self):
        self.astar_refresh_period = 7

    def ai_initialize(self):
        self.ai_state = 'idle'  # Should go here - moving temporarily
        self.current_action = None

        self.astar_refresh_cur = roll(1, 5)
        #
        self.target_figure = None
        self.target_location = None

        self.perceived_enemies = {}
        ## Create a list of all enemies we have not perceived yet
        self.unperceived_enemies = []
        self.perception_info = {'closest_enemy':None, 'closest_enemy_distance':None}

        # An ordered list of behaviors
        #self.behaviors = []

        self.patrol_route = []  # Should go here - moving temporarily
        self.current_patrol_index = 0
        self.follow_distance = 10


    def set_enemy_perceptions_from_cached_factions(self):
        # Make sure We are not a captive (later, if freed, captives will need to run this routine)
        if not self.owner.sapient.is_captive():

            for enemy_faction in self.owner.sapient.enemy_factions:
                for member in M.factions_on_map[enemy_faction]:
                    if member not in self.perceived_enemies.keys() and member not in self.unperceived_enemies and not member.sapient.is_captive():
                        self.unperceived_enemies.append(member)


    def take_turn(self):
        # Can't do anything if we're unconscious or dead
        if self.owner.creature.status != 'alive':
            return

        self.perceive_surroundings()

        self.battle_behavior()

        #self.non_battle_behavior()

    def perceive_surroundings(self):
        actor = self.owner

        for figure in self.unperceived_enemies[:]:
            perceived, threat_level = actor.creature.check_to_perceive(figure)

            if perceived:
                self.owner.sapient.say('I see you, %s'%figure.fullname())
                self.perceived_enemies[figure] = threat_level
                self.unperceived_enemies.remove(figure)

        self.find_closest_perceived_enemy()

    def find_closest_perceived_enemy(self):

        closest_enemy = None
        closest_dist = 1000

        for figure in filter(lambda figure: figure.creature.status == 'alive', self.perceived_enemies):
            dist = self.owner.distance_to(figure)
            if dist < closest_dist:
                closest_enemy = figure
                closest_dist = dist

        ## Update perception dict
        self.perception_info['closest_enemy'] = closest_enemy
        self.perception_info['closest_enemy_dist'] = closest_dist


    def handle_astar_refresh(self):
        # Every 5 turns astar will refresh. Allows us to cache longer paths
        self.astar_refresh_cur -= 1
        if self.astar_refresh_cur == 0:
            self.astar_refresh_cur = self.astar_refresh_period
        # Clear dead targets
        if self.target_figure and self.target_figure.creature.status != 'alive':
            self.unset_target()
        # Refresh to new target location
        if self.target_figure and ( (1 <= len(self.owner.cached_astar_path) <= 5) or self.astar_refresh_cur == 5):
            self.target_location = (self.target_figure.x, self.target_figure.y)
            self.owner.set_astar_target(self.target_location[0], self.target_location[1])
        # Path to target location if it exists and is not set
        elif not self.target_figure and self.target_location and not self.owner.cached_astar_path:
            self.owner.set_astar_target(self.target_location[0], self.target_location[1])


    def set_target_figure(self, target_figure):
        self.target_figure = target_figure
        self.target_location = target_figure.x, target_figure.y
        ## Now set the location
        self.owner.set_astar_target(self.target_location[0], self.target_location[1])

    def set_target_location(self, target_location):
        self.target_figure = None
        self.target_location = target_location
        self.owner.set_astar_target(self.target_location[0], self.target_location[1])

    def unset_target(self):
        self.target_figure = None
        self.target_location = None

    def astar_move(self):
        self.handle_astar_refresh()

        blocks_mov = self.owner.move_with_stored_astar_path(path=self.owner.cached_astar_path)

        if blocks_mov == 'path_end':
            game.add_message('%s reached end of path'%self.owner.fulltitle() )
            self.unset_target()

        elif blocks_mov == 1:
            # Reset path. TODO - new path to target_figure if existsw
            self.owner.set_astar_target(self.target_location[0], self.target_location[1])
            self.owner.move_with_stored_astar_path(path=self.owner.cached_astar_path)

    def battle_behavior(self):
        actor = self.owner
        #has_moved = 0

        # Handle idle -> attacking behavior
        if self.ai_state not in ('fleeing', 'attacking') and self.perception_info['closest_enemy'] is not None:
            self.set_state('attacking')

        # Taking some extra perceptory info to understand when to flee
        if self.ai_state != 'fleeing' and ( (actor.creature.get_pain_ratio() > .5) or (actor.creature.blood < 5 and actor.creature.bleeding) ):
            self.set_state('fleeing')


        if self.ai_state == 'attacking':
            self.ai_state_attack()

        elif self.ai_state  == 'fleeing':
            self.ai_state_flee()

        elif self.ai_state == 'moving':
            self.ai_state_move()

        elif self.ai_state == 'following':
            self.ai_state_follow()

        elif self.ai_state == 'patrolling':
            self.ai_state_patrol()

        #if not has_moved:
        #    actor.creature.dijmap_move()

        # Finally, make any attacks which can be allowed
        if self.perception_info['closest_enemy'] is not None and self.perception_info['closest_enemy_dist'] < 2:
            self.attack_enemy(self.perception_info['closest_enemy'])



    def ai_state_attack(self):
        if self.perception_info['closest_enemy_dist'] < DIJMAP_CREATURE_DISTANCE:
            self.unset_target()
        # Use A* if enemy is out of certain distance
        if self.target_figure is None and self.perception_info['closest_enemy'] is not None and self.perception_info['closest_enemy_dist'] >= DIJMAP_CREATURE_DISTANCE:
            self.set_target_figure(target_figure=self.perception_info['closest_enemy'])

        # Use A* move
        if self.target_figure and self.perception_info['closest_enemy'] and self.perception_info['closest_enemy'] >= DIJMAP_CREATURE_DISTANCE:
            self.astar_move()

        else:
            self.owner.creature.dijmap_move()

    def ai_state_flee(self):
        actor = self.owner

        if not actor.creature.bleeding and actor.creature.get_pain_ratio() < .5:
            self.set_state('attacking')

        ## Hacking for now - using an abstract "bandage"
        elif actor.creature.bleeding and (self.perception_info['closest_enemy'] is None or self.perception_info['closest_enemy_dist'] > 8):
            actor.creature.bleeding = max(actor.creature.bleeding - .25, 0)
            game.add_message(actor.fullname() + ' has used a bandage', libtcod.dark_green)

        actor.creature.dijmap_move()


    def set_state(self, ai_state, **kwargs):
        actor = self.owner
        actor.sapient.nonverbal_behavior(' is now %s'%ai_state )
        self.ai_state  = ai_state

        if self.ai_state  == 'attacking':
            # This will clear the target, in case they happen to be following someone or whatever
            self.unset_target()

            for faction in actor.sapient.enemy_factions:
                actor.creature.dijmap_desires[faction.faction_name] = 2

        elif self.ai_state  == 'fleeing':
            for faction in actor.sapient.enemy_factions:
                actor.creature.dijmap_desires[faction.faction_name] = -4

            actor.creature.dijmap_desires['map_center'] = -2

        elif self.ai_state == 'patrolling':
            if not self.patrol_route:
                self.patrol_route = kwargs['patrol_route']

        elif self.ai_state == 'moving':
            self.set_target_location(kwargs['target_location'])

        elif self.ai_state == 'following':
            self.set_target_figure(kwargs['target_figure'])


    def ai_state_patrol(self):
        ''' Handles route-setting and moving of patrolling entities '''
        if self.target_location is None:
            if M.get_astar_distance_to(x=self.owner.x, y=self.owner.y, target_x=self.patrol_route[self.current_patrol_index][0], target_y=self.patrol_route[self.current_patrol_index][1]) > 0:
                self.set_target_location(self.patrol_route[self.current_patrol_index])
            else:
                game.add_message('%s could not reach patrol route at (%i, %i), aborting' %(self.owner.fulltitle(), self.patrol_route[self.current_patrol_index][0], self.patrol_route[self.current_patrol_index][1]) )
                del self.patrol_route[self.current_patrol_index]
                self.set_target_location(self.patrol_route[self.current_patrol_index])

        if get_distance_to(self.owner.x, self.owner.y, self.target_location[0], self.target_location[1]) < 2:
            self.current_patrol_index = looped_increment(self.current_patrol_index, len(self.patrol_route)-1, 1)

            self.set_target_location(self.patrol_route[self.current_patrol_index])

        self.astar_move()


    def ai_state_move(self):
        if self.target_location:
            distance = get_distance_to(self.owner.x, self.owner.y, self.target_location[0], self.target_location[1])
            if self.target_location and distance > 0:
                self.astar_move()

            elif distance == 0:
                self.unset_target()
                self.set_state('idle')


    def ai_state_follow(self):
        if self.target_figure and self.owner.distance_to(self.target_figure) > self.follow_distance:
            self.astar_move()


    def attack_enemy(self, enemy):
        self.owner.creature.turns_since_move = 0
        # TODO - make sure this makeshift code is turned into something much more intelligent
        weapon = self.owner.creature.get_current_weapon()
        if weapon:
            target_part = random.choice(enemy.components)
            #target_layer, coverage_amount = random.choice(target_part.get_coverage_layers() )
            self.owner.creature.standard_combat_attack(attacking_object_component=weapon.components[0], force=weapon.get_mass(), target=enemy, target_component=target_part)


class BasicWorldBrain:
    def __init__(self):
        self.destination = None
        self.path = None
        self.next_tick = 0
        self.goals = []


    def add_goal(self, priority, goal_type, reason, **kwargs):
        ' Terribly written general handler for any goal type \
        messy implementation with **kwargs for now...'

        # To be phased out at some point
        if goal_type == 'wait':
            # Name the location
            behavior_list = []
            #target = kwargs['target']
            #location = WORLD.tiles[target[0]][target[1]].get_location_description()
            #if (self.owner.wx, self.owner.wy) != target or len(self.goals): # Problematic that this is calculated when the goal is added rather than when fired.
            #    goal_name = '{0} to {1} to {2} for {3} days'.format(kwargs['travel_verb'], location, kwargs['activity_verb'], kwargs['num_days'])
            #    behavior_list.append(MovLocBehavior(coords=target, figure=self.owner))
            #else:
            #    goal_name = '{0} at {1} for {2} days'.format(kwargs['activity_verb'], location, kwargs['num_days'])
            #wait = WaitBehavior(figure=self.owner, num_days=kwargs['num_days'], activity=kwargs['activity_verb'])
            wait = WaitBehavior(figure=self.owner, location=kwargs['location'], num_days=kwargs['num_days'], travel_verb=kwargs['travel_verb'], activity_verb=kwargs['activity_verb'])
            behavior_list.append(wait)

        elif goal_type == 'travel':
            #goal_name = 'travel to {0}'.format(WORLD.tiles[target_tuple[0]][target_tuple[1]].get_location_description())
            goto_site = MovLocBehavior(location=kwargs['location'], figure=self.owner, travel_verb='travel')
            behavior_list = [goto_site]
        # also phased out
        elif goal_type == 'travel to person':
            target_figure = kwargs['target']
            #goal_name = 'travel to ' + target_figure.fulltitle()
            goto_target = MovTargBehavior(target=target_figure, figure=self.owner)
            behavior_list = [goto_target]

        elif goal_type == 'kill person':
            target_figure = kwargs['target']
            #goal_name = 'kill ' + target_figure.fulltitle()
            goto_target = MovTargBehavior(target=target_figure, figure=self.owner)
            kill_target = KillTargBehavior(target=target_figure, figure=self.owner)

            behavior_list = [goto_target, kill_target]

        elif goal_type == 'capture person':
            target_figure = kwargs['target']
            target_prison_bldg = kwargs['target_prison_bldg']
            target_prison_site = target_prison_bldg.site
            #goal_name = 'capture ' + target_figure.fulltitle()
            goto_target = MovTargBehavior(target=target_figure, figure=self.owner)
            capture_target = CaptureTargBehavior(target=target_figure, figure=self.owner)
            #for after capture
            goto_target_location = MovLocBehavior(location=(target_prison_site.x, target_prison_site.y), figure=self.owner)
            imprison_target = ImprisonTargBehavior(target=target_figure, figure=self.owner, building=target_prison_bldg)

            behavior_list = [goto_target, capture_target, goto_target_location, imprison_target]

        elif goal_type == 'move_trade_goods_to_city':
            target_city = kwargs['target_city']
            #goal_name = 'move goods to to {0}'.format(target_city.name)
            goto_site = MovLocBehavior(location=(target_city.x, target_city.y), figure=self.owner)
            unload_goods = UnloadGoodsBehavior(target_city=target_city, figure=self.owner)
            behavior_list = [goto_site, unload_goods]

        ## Tell the world what you're doing
        #if goal_type != 'move_trade_goods_to_city':
        #    game.add_message('{0} has decided to {1}'.format(self.owner.fulltitle(), goal_name), libtcod.color_lerp(PANEL_FRONT, self.owner.color, .5))

        # Add the goal to the list. Automatically add a goal to return home after the goal is complete
        if len(self.goals) >= 2 and self.goals[-1].reason == 'I like to be home when I can.':
            self.goals.insert(-1, Goal(behavior_list=behavior_list, priority=priority, reason=reason))
        else:
            self.goals.append(Goal(behavior_list=behavior_list, priority=priority, reason=reason))

        # Auto return home
        if self.goals[-1].reason != 'I like to be home when I can.' and self.owner.sapient.current_citizenship:
            home_city = self.owner.sapient.current_citizenship
            return_from_site = MovLocBehavior(location=(home_city.x, home_city.y), figure=self.owner, travel_verb='return home')
            behavior_list = [return_from_site]

            self.goals.append(Goal(behavior_list=behavior_list, priority=priority, reason='I like to be home when I can.'))

    def handle_goal_behavior(self):
        ''' Key function which takes each goal a step at a time
        and performs the behavior one by one '''
        current_goal = self.goals[0]
        current_goal.take_goal_action()

        if current_goal.is_completed():
            self.goals.remove(current_goal)

            #if len(self.goals) == 0:
            #    WORLD.travelers.remove(self.owner)


    def monthly_life_check(self):
        sapient = self.owner.sapient
        age = sapient.get_age()

        if self.owner.creature.intelligence_level == 3:
            # Pick a spouse and get married immediately
            if sapient.spouse == None and self.owner.creature.sex == 1 and MIN_MARRIAGE_AGE <= age <= MAX_MARRIAGE_AGE:
                if roll(1, 48) >= 48:
                    self.pick_spouse()

            # Have kids! Currenly limiting to 2 for non-important, 5 for important (will need to be fixed/more clear later)
            # Check female characters, and for now, a random chance they can have kids
            if sapient.spouse and self.owner.creature.sex == 0 and MIN_CHILDBEARING_AGE <= age <= MAX_CHILDBEARING_AGE and len(sapient.children) <= (sapient.important * 3) + 2:
                if roll(1, 20) == 20:
                    sapient.have_child()

            ####### GOALS #######

            if not sapient.economy_agent \
                    and self.owner.creature.sex == 1 \
                    and age >= 18 \
                    and not sapient.is_commander() \
                    and not sapient.is_captive() \
                    and roll(1, 50) == 1:

                moving = self.check_for_move_city()

                if not moving:
                    self.check_for_liesure_travel()

        ## Lesser intelligent creatures
        elif self.owner.creature.intelligence_level == 2:
            num = roll(1, 100)

            if num < 10:
                city = WORLD.get_closest_city(self.owner.wx, self.owner.wy)[0]
                if city:
                    self.add_goal(priority=1, goal_type='wait', reason='Do we need a reason?', location=(city.x, city.y), travel_verb='travel', activity_verb='pillage', num_days=2)

                    self.add_goal(priority=1, goal_type='travel', reason='Do we need a reason?', location=(self.owner.wx, self.owner.wy), travel_verb='return')
                    #self.add_goal(priority=1, goal_type='wait', reason='Do we need a reason?', location=return_targ, travel_verb='return', activity_verb='rebase', num_days=2)

    def pick_spouse(self):
        sapient = self.owner.sapient
        # Pick someone to marry. Not very sophistocated for now. Must be in a site to consider marriage
        if WORLD.tiles[self.owner.wx][self.owner.wy].site:
            potential_spouses = [figure for figure in WORLD.tiles[self.owner.wx][self.owner.wy].entities
                                 if figure.creature.sex != self.owner.creature.sex
                                 and figure.creature.creature_type == self.owner.creature.creature_type
                                 and figure.sapient.dynasty != sapient.dynasty
                                 and MIN_MARRIAGE_AGE < figure.sapient.get_age() < MAX_MARRIAGE_AGE]

            if len(potential_spouses) == 0 and sapient.current_citizenship:
                # Make a person out of thin air to marry
                sex = abs(self.owner.creature.sex-1)
                s_born = time_cycle.years_ago(sapient.get_age()-5, sapient.get_age()+5)
                potential_spouses = [sapient.current_citizenship.create_inhabitant(sex=sex, born=s_born, char='o', dynasty=None, race=self.owner.creature.creature_type, important=sapient.important, house=sapient.house)]
            elif sapient.current_citizenship is None:
                game.add_message('{0} wanted to pick a spouse, but was not a citizen of any city'.format(self.owner.fulltitle()), libtcod.dark_red)
                return

            spouse = random.choice(potential_spouses)
            sapient.take_spouse(spouse=spouse)
            ## Notify world
            # game.add_message(''.join([self.owner.fullname(), ' has married ', spouse.fullname(), ' in ', sapient.current_citizenship.name]) )
            # Update last names
            if self.owner.creature.sex == 1:    spouse.sapient.lastname = sapient.lastname
            else:                               sapient.lastname = spouse.sapient.lastname

            ## Move in
            if spouse.sapient.current_citizenship != sapient.current_citizenship:
                #game.add_message('{0} (spouse), citizen of {1}, had to change citizenship to {2} in order to complete marriage'.format(spouse.fullname(), spouse.sapient.current_citizenship.name, sapient.current_citizenship.name ), libtcod.dark_red)
                spouse.sapient.change_citizenship(new_city=sapient.current_citizenship, new_house=sapient.house)
            # Make sure the spouse meets them
            if (spouse.wx, spouse.wy) != (self.owner.wx, self.owner.wy):
                spouse.world_brain.add_goal(priority=1, goal_type='travel', reason='because I just married {0}, so I must move to be with him!'.format(self.owner.fullname()), location=(self.owner.wx, self.owner.wy))

            return spouse

    def check_for_move_city(self):
        sapient = self.owner.sapient
        if sapient.profession is None and roll(1, 1000) >= 950:
            target_city = random.choice([city for city in WORLD.cities if city != sapient.current_citizenship])
            reason = random.choice(['needed a change of pace', 'wanted to see more of the world'])

            sapient.change_citizenship(new_city=target_city, new_house=None)
            self.add_goal(priority=1, goal_type='travel', reason=reason, location=(target_city.x, target_city.y))
            # Return whether the goal was fired or not
            return 1
        return 0


    def check_for_liesure_travel(self):
        sapient = self.owner.sapient
        if (sapient.profession is None or sapient.profession == 'Adventurer') and roll(1, 1000) >= 500:

            # More interesting alternative - visiting a holy site
            if roll(0, 1) and len(sapient.culture.pantheon.holy_sites):
                holy_site = random.choice(sapient.culture.pantheon.holy_sites)
                target_x, target_y = holy_site.x, holy_site.y
                travel_verb = 'go on a pilgrimmage to'
                activity = 'meditate'
                reason = 'wanted to visit this holy site.'
            # Otherwise, pick a random spot to travel to
            else:
                found_spot = False
                while not found_spot:
                    xdist = roll(5, 15) * random.choice((-1, 1))
                    ydist = roll(5, 15) * random.choice((-1, 1))
                    # If we can path there, it's OK
                    if WORLD.get_astar_distance_to(self.owner.wx, self.owner.wy, self.owner.wx + xdist, self.owner.wy + ydist):
                        found_spot = True
                # Pick a reason
                travel_verb = 'travel'
                activity = random.choice(('explore', 'hunt'))
                reasons = {'explore':['wanted to explore', 'wanted to see more of the world'],
                           'hunt':['needed time to relax', 'wanted a change of pace', 'think it\s a nice way to see the world', 'love the thrill of the chase']}
                reason = random.choice(reasons[activity])
                target_x, target_y = (self.owner.wx + xdist, self.owner.wy + ydist)

            num_days = roll(3, 8)
            #self.add_goal(priority=1, goal_type='travel', reason=reason, target=(target_x, target_y))
            self.add_goal(priority=1, goal_type='wait', reason=reason, location=(target_x, target_y), num_days=num_days, activity_verb=activity, travel_verb=travel_verb)
            return 1

        return 0



    def set_destination(self, origin, destination):
        self.destination = destination
        self.path = origin.path_to[destination][:]

    def take_turn(self):
        if self.goals:
            self.handle_goal_behavior()


    def make_decision(self, decision_name):
        weighed_options = {}
        for option in decisions[decision_name]:
            weighed_options[option] = {}

            if self.owner.sapient.profession and self.owner.sapient.profession.name in option['professions']:
                weighed_options[option][self.owner.sapient.profession.name] = decisions[decision_name][option][self.owner.sapient.profession.name]

            for trait in option['traits']:
                if trait in self.owner.sapient.traits:
                    weighed_options[option][trait] = decisions[decision_name][trait]

            for misc_reason in option['misc']:
                weighed_options[option][misc_reason] = decisions[decision_name][option][misc_reason]


######################## Code from Paradox Inversion on libtcod forums ###################################
class TimeCycle(object):
    # The TimeCycle class has all information on time and current day
    def __init__(self):
        self.ticks_per_hour = 600
        self.hours_per_day = 24
        self.days_per_week = 7
        self.days_per_month = 30
        self.months_per_year = 12

        self.current_day_tick = 0
        self.current_tick = 0
        self.current_hour = 0
        self.current_day = 0
        self.current_weekday = 0
        self.current_month = 0
        self.current_year = 1

        self.weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                         'Saturday', 'Sunday']
        self.months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                       'September', 'October', 'November', 'December']
        ## Dict of events, with keys being the future Y, M, and D, and values being a list of events
        self.events = {}

    def days_to_date(self, days_in_advance):
        # Return a tuple containing year, month, day, hour info
        (years, remainder) = divmod(days_in_advance, (self.months_per_year * self.days_per_month))
        (months, days_left) = divmod(remainder, self.days_per_month)

        total_days = self.current_day + days_left
        if total_days <= self.days_per_month:
            future_day = total_days
        else:
            future_day = total_days - self.days_per_month
            months += 1 #should never be more than 1 month

        total_months = self.current_month + months
        if total_months <= self.months_per_year:
            future_month = total_months
        else:
            future_month = total_months - self.months_per_year
            years += 1 #should never be more than 1 year

        future_year = self.current_year + years

        return (future_year, future_month, future_day)


    def add_event(self, date, event):
        ''' Should add an event to the scheduler'''
        (year, month, day) = date
        if (year, month, day) in self.events.keys():
            self.events[(year, month, day)].append(event)
        else:
            self.events[(year, month, day)] = [event]

    def handle_events(self):
        if (self.current_year, self.current_month, self.current_day) in self.events.keys():
            for event in self.events[(self.current_year, self.current_month, self.current_day)]:
                event()


    def check_tick(self):
        if self.current_tick == self.ticks_per_hour:
            self.current_tick = 0
            self.current_hour += 1
            self.check_hour()

    def check_hour(self):
        if 7 <= self.current_hour < 19:
            if self.current_hour == 7:
                self.nightToDay()
        else: #If the current time is not between 7a and 7p
            if self.current_hour == 19: #If it's 7, night falls
                self.dayToNight()

        if self.current_hour == self.hours_per_day + 1:
            self.current_hour = 0
            self.current_day += 1
            self.current_weekday += 1
            self.check_day()
            #game.add_message('It is now ' + self.weekdays[self.current_weekday], libtcod.light_sea)
            # day_tick method to test civs:
            self.day_tick(num_days=1)
            ##############################

    def next_day(self):
        if self.current_day + 1 >= self.days_per_month:
            next_day = 0
        else:
            next_day = self.current_day + 1
        return next_day

    def check_day(self):
        # Day to day stuff
        self.current_day += 1
        self.current_weekday += 1
        # Change week (civs take turn)
        if self.current_weekday == self.days_per_week:
            self.current_weekday = 0
            self.week_tick()
            # Change month
        if self.current_day == self.days_per_month:
            self.current_day = 0

            self.month_tick()
            #game.add_message('It is now ' + self.months[self.current_month], libtcod.light_sea)

    def check_month(self):
        if self.current_month == self.months_per_year:
            self.year_tick()

    def goto_next_week(self):
        days_til_next_week = self.days_per_week - self.current_weekday
        self.day_tick(days_til_next_week)

    def dayToNight(self):
        #message ('Night falls.', libtcod.grey)
        pass

    def nightToDay(self):
        #message ('The sun breaks the dark of night.', libtcod.light_yellow)
        pass

    def get_current_date(self):
        return ''.join([self.weekdays[self.current_weekday], ', ', self.months[self.current_month], ' ', str(self.current_day + 1)])

    def get_current_time(self):
        minutes = int(math.floor(self.current_tick / 10))
        if minutes < 10:
            minutes = '0' + str(minutes)
        else:
            minutes = str(minutes)

        return str(self.current_hour) + ':' + minutes

    def years_ago(self, *args):
        if len(args) == 1:
            return self.curent_year - args[0]
        elif len(args) == 2:
            return self.current_year - (roll(args[0], args[1]))

    #a tick method, which was implemented before libtcod. it now keeps track of how many turns have passed.
    def tick(self):
        self.current_tick += 1
        self.check_tick()

        ### Creatures
        for creature in M.creatures:
            creature.creature.handle_tick()

            if creature.local_brain and creature.creature.next_tick <= self.current_tick:
                next_tick = creature.creature.next_tick + creature.creature.catts['Move Speed']
                if next_tick >= self.ticks_per_hour:
                    next_tick = next_tick - self.ticks_per_hour
                creature.creature.next_tick = next_tick
                creature.local_brain.take_turn()

        ### Sapients
        for actor in M.sapients:
            # Talk
            actor.sapient.handle_pending_conversations()
            # Bleed every tick, if necessary
            actor.creature.handle_tick()

            #if actor.ai and actor.creature.next_tick == self.current_tick:
            if actor.local_brain and actor.creature.next_tick <= self.current_tick:
                next_tick = actor.creature.next_tick + actor.creature.catts['Move Speed']
                if next_tick >= self.ticks_per_hour:
                    next_tick = next_tick - self.ticks_per_hour
                actor.creature.next_tick = next_tick
                actor.local_brain.take_turn()
                #actor.creature.dijmap_move()

        M.update_dmaps()

        '''
		for army in armies_in_battle[:]:
				if len(army.units) == 0:
					armies_in_battle.remove(army)
					army.disband()
					game.add_message(army.name + ' has been completely destroyed!')
		'''

    #def hour_tick(self):
    #    self.current_hour += 1
    #    self.check_hour()

    def day_tick(self, num_days):
        for iteration in xrange(num_days):
            self.check_day()
            self.handle_events()

            for figure in reversed(WORLD.all_figures):
                if figure.world_brain and figure.sapient.is_available_to_act(): #and figure .world_brain.next_tick == self.current_day:
                    #figure.world_brain.next_tick = self.next_day()
                    figure.world_brain.take_turn()

#             for traveler in reversed(WORLD.travelers):
#                 if traveler.world_brain and traveler.sapient.is_available_to_act() and traveler.world_brain.next_tick == self.current_day:
#                     traveler.world_brain.next_tick = self.next_day()
#                     traveler.world_brain.take_turn()
#                     #M.fov_recompute = True
#                     #############################################

    def week_tick(self):
        # Cheaply defined to get civs working per-day
        for city in reversed(WORLD.cities):
            city.econ.run_simulation()
            city.dispatch_caravans()

        # Player econ preview - to show items we're gonna bid on
        if game.state == 'playing' and player.sapient.economy_agent:
            player.sapient.economy_agent.player_auto_manage()
            panel4.tiles_dynamic_buttons = []
            panel4.recalculate_wmap_dyn_buttons = True

        elif game.state == 'playing' and panel4.render:
            panel4.render = 0


    def month_tick(self):
        self.current_month += 1
        self.check_month()

        ## Have figures do some stuff monthly
        for figure in WORLD.all_figures[:]:
            ## TODO - make sure this check works out all the time
            if figure.sapient.is_available_to_act():
                figure.world_brain.monthly_life_check()

        for plot in WORLD.plots[:]:
            if plot.check_for_fire():
                plot.fire()


    def year_tick(self):
        self.current_month = 0
        self.current_year += 1
        #game.add_message('It is now ' + str(self.current_year), libtcod.light_sea)
        for figure in WORLD.all_figures[:]:
            # Die from old age
            if figure.sapient.get_age() > 70:
                figure.sapient.die()


    def rapid_tick(self, ticks):
        ticks = ticks
        for x in xrange(ticks):
            self.tick()

    def rapid_hour_tick(self, hours):
        for x in xrange(hours):
            self.hour_tick()

    def rapid_month_tick(self, months):
        for x in xrange(months):
            self.month_tick()

######################## End Code from Paradox inversion on libtcod forums ###################################


class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.x = 0
        self.y = 0

        self.center(int(round(WORLD_WIDTH / 2)), int(round(WORLD_HEIGHT / 2)))

    def move(self, dx, dy):
        if game.map_scale == 'world':
            # Make sure the new camera coordinate won't let the camera see off the map
            if 0 <= self.x + dx < WORLD_WIDTH - self.width - 1:
                self.x += dx
            if 0 <= self.y + dy < WORLD_HEIGHT - self.height - 1:
                self.y += dy

        if game.map_scale == 'human':
            # Make sure the new camera coordinate won't let the camera see off the map
            if 0 <= self.x + dx < M.width - self.width - 1:
                self.x += dx
            if 0 <= self.y + dy < M.height - self.height - 1:
                self.y += dy

    def center(self, target_x, target_y):
        #new camera coordinates (top-left corner of the screen relative to the map)
        x = target_x - int(round(self.width / 2))  #coordinates so that the target is at the center of the screen
        y = target_y - int(round(self.height / 2))

        #make sure the camera doesn't see outside the map
        if x < 0: x = 0
        if y < 0: y = 0
        if game.map_scale == 'world':
            if x > WORLD_WIDTH - self.width - 1:
                x = WORLD_WIDTH - self.width - 1
            if y > WORLD_HEIGHT - self.height - 1:
                y = WORLD_HEIGHT - self.height - 1

        ## Add FOV compute once it works for the world.
        elif game.map_scale == 'human':
            if x > M.width - self.width - 1:
                x = M.width - self.width - 1
            if y > M.height - self.height - 1:
                y = M.height - self.height - 1

        (self.x, self.y) = (x, y)

    def map2cam(self, x, y):
        ''' 'convert coordinates on the map to coordinates on the screen '''
        (x, y) = (x - self.x, y - self.y)
        return (x, y)

    def cam2map(self, x, y):
        ''' convert coordinates on the map to coordinates on the screen '''
        (x, y) = (x + self.x, y + self.y)
        return (x, y)

    def click_and_drag(self, mouse):
        ''' Handles clicking and dragging to move map around, on both scale-level maps '''
        ox, oy = self.cam2map(mouse.cx, mouse.cy)

        momentum = 0
        while not mouse.lbutton_pressed:
            # Need to force game to update FOV while dragging if on human-scale map; otherwise map console will not update
            if game.map_scale == 'human':
                game.handle_fov_recompute()
            render_handler.render_all()

            event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)  #get mouse position and click status

            (x, y) = self.cam2map(mouse.cx, mouse.cy)

            dif_x, dif_y = (x - ox, y - oy)
            # add some momentum to the camera
            if dif_x != ox and dif_y != oy:
                momentum += 2
            else:
                momentum = max(momentum - 1, 0)

            self.move(-dif_x, -dif_y)

        # after button is released, move the camera a bit more based on momentum
        total_momentum = momentum
        m_amt = 1
        while momentum > 0 and int(round(dif_x * m_amt)) + int(round(dif_y * m_amt)):
            momentum -= 1
            m_amt = momentum / total_momentum
            # Need to force game to update FOV while dragging if on human-scale map; otherwise map console will not update
            if game.map_scale == 'human':
                game.handle_fov_recompute()
            render_handler.render_all()

            self.move(-int(round(dif_x * m_amt)), -int(round(dif_y * m_amt)))

    def mouse_is_on_map(self):
        ''' Ensures mouse doesn't pick up activity outside edge of camera '''
        return (0 <= mouse.cx <= self.width and 0 <= mouse.cy <= self.height)


def create_shirt():
    shirtcomps = copy.deepcopy(phys.shirtcomps)
    shirt = Object(name='shirt', char='T', color=libtcod.sepia, components=shirtcomps, blocks_mov=0, blocks_vis=0,
                       description='Test description', creature=None, sapient=None, weapon=None, wearable=1, x=None, y=None)

    return shirt


class Culture:
    def __init__(self, color, language, world, races):
        self.color = color
        self.language = language
        self.name = self.gen_word(syllables=roll(1, 3), num_phonemes=(3, 20), cap=1)

        self.world = world
        self.races = races
        # Set astrology from the world
        self.astrology = religion.Astrology(world.moons, world.suns, language=self.language)
        self.pantheon = religion.Pantheon(astrology=self.astrology, num_misc_gods=1)

        self.subsistence = 'Hunter-gatherer'

        self.neighbor_cultures = []
        self.territory = []
        self.villages = []
        self.access_res = []

        self.culture_traits = {}
        self.set_culture_traits()
        self.weapons = []

        # On initial run, it should only generate spears (and eventually bows)
        self.create_culture_weapons()

    def set_culture_traits(self):
        trait_num = roll(3, 4)
        while trait_num > 0:
            trait = random.choice(CULTURE_TRAIT_INFO.keys())

            for otrait in self.culture_traits:
                if trait in CULTURE_TRAIT_INFO[otrait]['opposed_traits'] or trait == otrait:
                    break
            else:
                # "Somewhat = .5, regular = 1, "very" = 2
                multiplier = random.choice([.5, .5, 1, 1, 1, 1, 2])
                self.culture_traits[trait] = multiplier
                trait_num -= 1

    def set_subsistence(self, subsistence):
        self.subsistence = subsistence

        #if subsistence != 'Hunter-gatherer':
        #    self.create_culture_weapons()

    def gen_word(self, syllables, num_phonemes=(3, 20), cap=0):
        word = self.language.gen_word(syllables=syllables, num_phonemes=num_phonemes)

        if cap:
            word = lang.spec_cap(word)

        return word

    def create_culture_weapons(self):
        ''' Culturally specific weapons '''
        # If we can't access resources, for now we can still make weapons out of wood
        if not ('iron' in self.access_res or 'bronze' in self.access_res or 'copper' in self.access_res):
            weapon_types = phys.basic_weapon_types
            materials = ['wood']
        else:
            weapon_types = phys.blueprint_dict.keys()
            materials = [m for m in self.access_res if m=='iron' or m=='bronze' or m=='copper']

        ''' Create a few types of unique weapons for this culture '''
        #weapon_types = ('sword', 'axe')

        for wtype in weapon_types:
            material_name = random.choice(materials)
            material = phys.materials[material_name]

            special_properties = {random.choice(phys.PROPERTIES): random.choice( (5, 10) ) }

            # Send it over to the item generator to generate the weapon
            weapon_info_dict = phys.wgenerator.generate_weapon(wtype=wtype, material=material, special_properties=special_properties)

            weapon_name = self.gen_word(syllables=roll(1, 2))

            name = weapon_name + ' ' + wtype
            weapon_info_dict['name'] = name

            # Finally, append to list of object dicts
            #self.weapon_info_dicts.append(weapon_info_dict)
            self.weapons.append(name)

            phys.object_dict[name] = weapon_info_dict


    def add_villages(self):
        for x, y in self.territory:
            for resource in WORLD.tiles[x][y].res.keys():
                if resource not in self.access_res and WORLD.is_valid_site(x, y, None, MIN_SITE_DIST) and not len(WORLD.tiles[x][y].minor_sites): #and 10 < x < WORLD_WIDTH - 10 and 10 < y < WORLD_HEIGHT - 10:
                    self.access_res.append(resource)
                    self.add_village(x, y)
                    break


    def add_village(self, x, y):
        village = Site(world=WORLD, site_type='village', x=x, y=y, char=chr(7), name=self.name + ' village', color=self.color)
        WORLD.sites.append(village)
        WORLD.tiles[x][y].site = village
        self.villages.append(village)



    def create_being(self, sex, born, char, dynasty, important, faction, wx, wy, armed=0, race=None, save_being=0, intelligence_level=3):
        ''' Create a human, using info loaded from xml in the physics module '''
        # If race=None then we'll need to pick a random race from this culture
        if not race:
            race = random.choice(self.races)

        # The creature component
        creature_component = Creature(creature_type=race, sex=sex, intelligence_level=intelligence_level)

        # Look up the creature (imported as a dict with a million nested dicts
        info = phys.creature_dict[race]

        # Gen names based on culture and dynasty
        if sex == 1: firstname = lang.spec_cap(random.choice(self.language.vocab_m.values()))
        else:        firstname = lang.spec_cap(random.choice(self.language.vocab_f.values()))

        if dynasty is not None:   lastname = dynasty.lastname
        else:                     lastname = lang.spec_cap(random.choice(self.language.vocab_n.values()))

        sapient_comp = SapientComponent(firstname=firstname, lastname=lastname, culture=self, born=born, dynasty=dynasty, important=important)

        human = assemble_object(object_blueprint=info, creature=creature_component, sapient=sapient_comp, local_brain=DijmapSapient(), world_brain=BasicWorldBrain(), force_material=None, wx=wx, wy=wy)
        faction.add_member(human)

        if dynasty is not None:
            dynasty.members.append(human)
        ###### Give them a weapon #######
        material = phys.materials['iron']
        if len(faction.weapons):    wname = random.choice(faction.weapons)
        else:                       wname = random.choice(self.weapons)

        if armed:
            weapon = assemble_object(object_blueprint=phys.object_dict[wname], creature=None, sapient=None, local_brain=None, world_brain=None, force_material=material, wx=wx, wy=wy)
            human.initial_give_object_to_hold(weapon)

        ################################
        shirt = create_shirt()
        human.put_on_clothing(clothing=shirt)
        # Let them know who owns it
        shirt.set_current_owner(human)
        shirt.set_current_holder(human)

        # This function will get anytime there needs to be people generated. They don't always need
        # to be saved in the world - thus, we won't worry too much about them if we don't need to
        if save_being:
            WORLD.tiles[wx][wy].entities.append(human)

            WORLD.all_figures.append(human)
            if important:
                WORLD.important_figures.append(human)


        return human


def assemble_object(object_blueprint, creature, sapient, local_brain, world_brain, force_material, wx, wy):
    ''' Build an object from the blueprint dictionary '''
    ## TODO - Currently only force_material works...

    if sapient and sapient.faction: color = sapient.faction.color
    elif force_material:            color = force_material.color
    else:
        # Not ideal, but when importing xml, we cache all possible materials the object can include - pick a random one for the color
        color = phys.materials[random.choice(object_blueprint['possible_materials'])].color

    components = phys.assemble_components(clist=object_blueprint['components'], force_material=force_material)

    obj = Object(name = object_blueprint['name'],
                    char = object_blueprint['char'],
                    color = color,
                    components = components,
                    blocks_mov = object_blueprint['blocks_mov'],
                    blocks_vis = object_blueprint['blocks_vis'],
                    description = object_blueprint['description'],

                    creature = creature,
                    sapient = sapient,
                    local_brain = local_brain,
                    world_brain = world_brain,
                    weapon = object_blueprint['weapon_component'],
                    wx = wx,
                    wy = wy
                    )
    return obj


def get_info_under_mouse():
    ''' get info to be printed in the sidebar '''
    (x, y) = camera.cam2map(mouse.cx, mouse.cy)
    info = []
    if game.map_scale == 'human' and M.is_val_xy((x, y)):
        info.append(('Tick: ' + str(time_cycle.current_tick), PANEL_FRONT))
        info.append(('at coords %i, %i height is %i' %(x, y, M.tiles[x][y].height), PANEL_FRONT))
        ### This will spit out some info about the unit we've selected (debug stuff)
        if render_handler.debug_active_unit_dijmap and not M.tiles[x][y].blocks_mov:
            debug_unit = render_handler.debug_active_unit_dijmap
            info.append((debug_unit.fullname() + ': tick = ' + str(debug_unit.creature.next_tick), libtcod.copper))
            total_desire = 0
            for desire, amount in debug_unit.creature.dijmap_desires.iteritems():
                if amount < 0: dcolor = libtcod.color_lerp(PANEL_FRONT, libtcod.red, amount/100)
                elif amount > 0: dcolor = libtcod.color_lerp(PANEL_FRONT, libtcod.green, amount/100)
                else: dcolor = PANEL_FRONT
                info.append((desire + ': ' + str(amount), dcolor ))
                total_desire += (M.dijmaps[desire].dmap[x][y] * amount)
            info.append(('Total: ' + str(total_desire), libtcod.dark_violet))
            info.append((' ', libtcod.white))
        ###############################################################################

        # Info about the surface of the map
        info.append((M.tiles[x][y].surface, libtcod.color_lerp(PANEL_FRONT, M.tiles[x][y].color, .5) ))
        info.append((' ', libtcod.white))
        # Zoning info
        if M.tiles[x][y].zone:
            info.append((M.tiles[x][y].zone, PANEL_FRONT))
            info.append((' ', PANEL_FRONT))
            # Building info
        if M.tiles[x][y].building:
            info.append((M.tiles[x][y].building.get_name(), PANEL_FRONT))
            info.append((' ', PANEL_FRONT))

        color = PANEL_FRONT
        for obj in M.tiles[x][y].objects:
            if libtcod.map_is_in_fov(M.fov_map, obj.x, obj.y):
                info.append((obj.fulltitle(), libtcod.color_lerp(PANEL_FRONT, obj.color, .3) ))

                if obj.creature and obj.creature.status == 'alive':
                    info.append(
                        ('Facing ' + COMPASS[obj.creature.facing], libtcod.color_lerp(libtcod.yellow, color, .5) ))

                info.append((' ', color))
                '''
				for component in obj.components:
					if component.grasped_item:
						info.append((component.name + ' (' + component.grasped_item.name + ')', color))
					else:
						info.append((component.name, color))
				'''

    elif game.map_scale == 'world':
        color = PANEL_FRONT
        xc, yc = camera.map2cam(x, y)
        if 0 <= xc <= CAMERA_WIDTH and 0 <= yc <= CAMERA_HEIGHT:
            info.append((WORLD.tiles[x][y].region.capitalize(), libtcod.color_lerp(color, WORLD.tiles[x][y].color, .5)))
            ###### Cultures ########
            if WORLD.tiles[x][y].culture is not None:
                info.append(('Culture:  ' + WORLD.tiles[x][y].culture.name, libtcod.color_lerp(color, WORLD.tiles[x][y].culture.color, .3)))
                info.append(('Language: ' + WORLD.tiles[x][y].culture.language.name, libtcod.color_lerp(color, WORLD.tiles[x][y].culture.color, .3)))
            else:
                info.append(('No civilized creatures inhabit this region', color))
            ###### Territory #######
            if WORLD.tiles[x][y].territory is not None:
                info.append(('Territory: ' + WORLD.tiles[x][y].territory.name, libtcod.color_lerp(color, WORLD.tiles[x][y].territory.color, .3)))
            else:
                info.append(('No state\'s borders claim this region', color))
            info.append((' ', color))

            # Resources
            for resource, amount in WORLD.tiles[x][y].res.iteritems():
                info.append(('{0} ({1})'.format(resource.capitalize(), amount), color))
            info.append((' ', color))

            ## FEATURES
            for feature in WORLD.tiles[x][y].features + WORLD.tiles[x][y].caves:
                info.append((feature.get_name(), color))
            for site in WORLD.tiles[x][y].minor_sites:
                info.append((site.name, color))
                if site.is_holy_site_to:
                    for pantheon in site.is_holy_site_to:
                        info.append((' - This is considered a holy site to the {0}.'.format(pantheon.name), color ))
            info.append((' ', color))

            # Sites
            site = WORLD.tiles[x][y].site
            if site:
                info.append(('{0} ({1})'.format(site.name.capitalize(), site.site_type), color))
                if site.site_type == 'city':
                    info.append(('{0} caravans harbored here'.format(len(site.caravans)), color))
                    num_figures = len([f for f in WORLD.tiles[x][y].entities if (f.sapient.is_commander() or not f.sapient.commander)])
                    info.append(('{0} figures or parties here'.format(num_figures), color))
            else:
                # Entities
                for entity in WORLD.tiles[x][y].entities:
                    # Commanders of parties or armies
                    if entity.sapient and entity.sapient.is_commander():
                        info.append(('{0} ({1} total men)'.format(entity.fulltitle(), entity.sapient.get_total_number_of_commanded_beings()), entity.sapient.faction.color))
                    # Individual travellers
                    elif entity.sapient and not entity.sapient.commander:
                        info.append(('{0}'.format(entity.fulltitle()), entity.sapient.faction.color))
                    info.append((' ', color))
                # Only show uncommanded populations
                for population in WORLD.tiles[x][y].populations:
                    if not population.commander:
                        info.append(('{0}'.format(population.name), population.faction.color))

            info.append((' ', color))

    return info

class RenderHandler:
    def __init__(self):

        self.debug_active_unit_dijmap = None


    def debug_dijmap_view(self, figure=None):
        if figure is None and self.debug_active_unit_type is not None:
            self.debug_active_unit_dijmap.char = 'o'
            self.debug_active_unit_dijmap = None

        else:
            self.debug_active_unit_dijmap = figure
            self.debug_active_unit_dijmap.char = 'X'


    def progressbar_screen(self, header, current_action, min_val, max_val, background_text=None):
        root_con.clear()
        map_con.clear()

        libtcod.console_print_ex(0, int(round(SCREEN_WIDTH / 2)), 1, libtcod.BKGND_NONE, libtcod.CENTER, header)

        '''
        if background_text != None:
            y = 10
            for t in background_text:
                h = libtcod.console_print_rect(con=con.con, x=5, y=y, w=70, h=10, fmt=t)
                y += h + 2
        '''

        map_con.render_bar(x=int(round(SCREEN_WIDTH / 2)) - 9, y=1, total_width=18, name=current_action, value=min_val,
                   maximum=max_val, bar_color=libtcod.color_lerp(libtcod.dark_yellow, PANEL_FRONT, .5),
                   back_color=PANEL_BACK, text_color=PANEL_FRONT, show_values=False, title_inset=False)
        libtcod.console_blit(map_con.con, 0, 0, camera.width, camera.height, 0, 0, 10)
        #libtcod.console_blit(con.con, 0, 0, SCREEN_WIDTH, PANEL1_HEIGHT, 0, 0, PANEL1_YPOS)
        libtcod.console_set_default_background(map_con.con, libtcod.black)
        libtcod.console_flush()

    def blink(self, x, y, color, repetitions, speed):
        # Have a tile blink at specified speed for specified # of repetitions
        (wmap_x, wmap_y) = camera.cam2map(x, y)

        render_handler.render_all(do_flush=1)

        for repetition in xrange(repetitions):
            # Render red
            #libtcod.console_put_char_ex(con.con, x, y, WORLD.tiles[wmap_x][wmap_y].char, color, color)
            libtcod.console_put_char_ex(map_con.con, x, y, 'X', color, color)
            libtcod.console_blit(map_con.con, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, 0, 0)
            libtcod.console_flush()
            time.sleep(speed)
            # Render background color
            libtcod.console_put_char_ex(map_con.con, x, y, WORLD.tiles[wmap_x][wmap_y].char, WORLD.tiles[wmap_x][wmap_y].char_color, WORLD.tiles[wmap_x][wmap_y].color)
            libtcod.console_blit(map_con.con, 0, 0, camera.width, camera.height, 0, 0, 0)
            libtcod.console_flush()
            time.sleep(speed)

    def render_all(self, do_flush=1):

        if game.map_scale == 'human' and M.fov_recompute:
            M.display(self.debug_active_unit_dijmap)

        elif game.map_scale == 'world':
            WORLD.display()

        # Handle the basic rendering steps on the GUI panels
        for panel in interface.gui_panels:
            panel.render_panel(game.map_scale, mouse)

        # Debug - print FPS
        libtcod.console_print(panel2.con, x=2, y=1, fmt='%i FPS' %int(libtcod.sys_get_fps()) )

        if game.state == 'playing':
            # Current date and time info
            libtcod.console_print(panel2.con, 2, 2, time_cycle.get_current_date())
            if game.map_scale == 'world':
                libtcod.console_print(panel2.con, 2, 3, '{0} year of {1}'.format(int2ord(1 + time_cycle.current_year - player.sapient.faction.leader_change_year), player.sapient.faction.leader.fullname() ))
                libtcod.console_print(panel2.con, 2, 4, '({0}); {1} pop, {2} imp'.format(time_cycle.current_year, len(WORLD.all_figures), len(WORLD.important_figures)))

            ##### PANEL 4 - ECONOMY STUFF
            if player.sapient.economy_agent is not None:
                libtcod.console_set_default_foreground(panel4.con, PANEL_FRONT)

                agent = player.sapient.economy_agent
                y = 5
                libtcod.console_print(panel4.con, 2, y, agent.name + ' (' + agent.economy.owner.name + ')')
                y +=  1
                libtcod.console_print(panel4.con, 2, y, str(agent.gold) + ' gold')
                # Display price beliefs
                for item, value in agent.perceived_values.iteritems():
                    y += 1
                    libtcod.console_print(panel4.con, 2, y, item + ': ' + str(value.center-value.uncertainty) + ' to ' + str(value.center+value.uncertainty))

                y += 2
                libtcod.console_print(panel4.con, 2, y, '-* Last turn *-')
                h = 1
                for j in xrange(len(agent.last_turn)):
                    y += h
                    h = libtcod.console_print_rect(panel4.con, 2, y, PANEL4_WIDTH -4, 2, ' - ' + agent.last_turn[j])

                y += h + 2
                libtcod.console_print(panel4.con, 2, y, '-* Inventory *-')
                # Display inventory
                inv = Counter(agent.inventory)
                for item, amount in inv.iteritems():
                    y += 1
                    libtcod.console_print(panel4.con, 2, y, item + ': ' + str(amount))

                y += 2
                libtcod.console_print(panel4.con, 2, y, '-* Future buys *-')
                for item, [bid_price, bid_quantity] in agent.future_bids.iteritems():
                    y += 1
                    libtcod.console_print(panel4.con, 2, y, str(bid_quantity) + ' ' + item + ' @ ' + str(bid_price) )


                    if panel4.recalculate_wmap_dyn_buttons:
                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_bid_price, args=(item, -1),
                                                                      text='<', topleft=(PANEL4_WIDTH-3, y), width=2, height=2, color=libtcod.light_blue, hcolor=libtcod.white, do_draw_box=False) )
                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_bid_price, args=(item, 1),
                                                                      text='>', topleft=(PANEL4_WIDTH-2, y), width=2, height=2, color=libtcod.light_blue*1.3, hcolor=libtcod.white, do_draw_box=False) )

                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_bid_quant, args=(item, -1),
                                                                      text='<', topleft=(PANEL4_WIDTH-5, y), width=2, height=2, color=libtcod.light_violet, hcolor=libtcod.white, do_draw_box=False) )
                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_bid_quant, args=(item, 1),
                                                                      text='>', topleft=(PANEL4_WIDTH-4, y), width=2, height=2, color=libtcod.light_violet*1.3, hcolor=libtcod.white, do_draw_box=False) )

                y += 1
                libtcod.console_print(panel4.con, 2, y, '-* Future sells *-')
                for item, [sell_price, sell_quantity] in agent.future_sells.iteritems():
                    y += 1
                    libtcod.console_print(panel4.con, 2, y, str(sell_quantity) + ' ' + item + ' @ ' + str(sell_price) )


                    if panel4.recalculate_wmap_dyn_buttons:
                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_sell_price, args=(item, -1),
                                                                      text='<', topleft=(PANEL4_WIDTH-3, y), width=1, height=1, color=libtcod.light_blue, hcolor=libtcod.white, do_draw_box=False) )
                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_sell_price, args=(item, 1),
                                                                      text='>', topleft=(PANEL4_WIDTH-2, y), width=1, height=1, color=libtcod.light_blue*1.3, hcolor=libtcod.white, do_draw_box=False) )

                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_sell_quant, args=(item, -1),
                                                                      text='<', topleft=(PANEL4_WIDTH-5, y), width=1, height=1, color=libtcod.light_violet, hcolor=libtcod.white, do_draw_box=False) )
                        panel4.wmap_dynamic_buttons.append(gui.Button(gui_panel=panel4, func=player.sapient.economy_agent.change_sell_quant, args=(item, 1),
                                                                      text='>', topleft=(PANEL4_WIDTH-4, y), width=1, height=1, color=libtcod.light_violet*1.3, hcolor=libtcod.white, do_draw_box=False) )


                if panel4.recalculate_wmap_dyn_buttons:
                    panel4.recalculate_wmap_dyn_buttons = 0

            ## Panel 3 - player info ##
            libtcod.console_print_ex(panel3.con, int(round(PANEL3_WIDTH / 2)), 1, libtcod.BKGND_NONE, libtcod.CENTER,
                                     ''.join(['-* ', player.fullname(), ' *-']))


            # A list of things to display
            disp_list = []
            for grasper in player.creature.get_graspers():
                if grasper.grasped_item is None:
                    disp_list.append(grasper.name + ': ')
                else:
                    disp_list.append(grasper.name + ': ' + grasper.grasped_item.name)
                    #print weapon properties
                    for wproperty, amt in grasper.grasped_item.get_weapon_properties().iteritems():
                        disp_list.append(' -%s: %i' %(wproperty, amt) )



            ## Display the list ##
            y = 2
            for text in disp_list:
                y += 1
                libtcod.console_print(panel3.con, 2, y, text)
                ## Bar showing current energy amount ##
            panel3.render_bar(x=2, y=panel3.height - 3, total_width=panel3.width - 4, name='Energy',
                       value=player.creature.energy, maximum=player.creature.catts['Stamina'],
                       bar_color=ENERGY_FRONT, back_color=ENERGY_BACK, text_color=libtcod.black, show_values=True,
                       title_inset=True)
            ## bar showing current pain amount ##
            panel3.render_bar(x=2, y=panel3.height - 4, total_width=panel3.width - 4, name='Pain',
                       value=player.creature.get_pain(), maximum=player.creature.get_max_pain(),
                       bar_color=PAIN_FRONT, back_color=PAIN_BACK, text_color=libtcod.black, show_values=True,
                       title_inset=True)
            ### Done rendering player info ###

            if game.map_scale == 'human':
                battle_hover_information()

        y = 6
        for (line, color) in get_info_under_mouse():
            ## Quick fix to catch more text than panel height
            if y > PANEL2_HEIGHT - 4:
                libtcod.console_print(panel2.con, PANEL2_TEXTX, y, '<< More >>')
                break
                ## Otherwise, print the info in whatever color it was specified as
            if not line == ' ':
                splitline = textwrap.wrap(line, PANEL2_WIDTH - PANEL2_TEXTX - 2)
            else:
                splitline = ' '
            for nline in splitline:
                libtcod.console_set_default_foreground(panel2.con, color)
                libtcod.console_print(panel2.con, PANEL2_TEXTX, y, nline)
                y += 1

        #print the game messages
        y = 1
        for (line, color) in game.get_game_msgs():
            libtcod.console_set_default_foreground(panel1.con, color)
            libtcod.console_print(panel1.con, MSG_X, y, line)
            y += 1

        #blit the contents of "panel" to the root console
        for panel in interface.gui_panels:
            if panel.render:
                panel.blit()
        # Special priority for the hover information panel
        if interface.hover_info:
            interface.hover_info.hover()

        if do_flush:
            libtcod.console_flush()

        for panel in interface.panel_deletions[:]:
            interface.delete_panel(panel)


def battle_hover_information():
    ''' Displays a box summarizing some combat stats on mouse hover '''
    (x, y) = camera.cam2map(mouse.cx, mouse.cy)  #from screen to map coordinates

    target = None
    if camera.mouse_is_on_map() and M.is_val_xy((x, y)) and M.tiles[x][y].explored:
        for obj in M.tiles[x][y].objects:
            if obj.creature and obj.creature.status != 'dead':
                target = obj
                break

        other_objects = [obj for obj in M.tiles[x][y].objects if (not obj.creature) or (obj.creature and obj.creature.status != 'alive') ]

        if M.tiles[x][y].interactable:
            itext = M.tiles[x][y].interactable['hover_text']
            gui.HoverInfo(header=['Interact'], text=itext, cx=mouse.cx, cy=mouse.cy, hoffset=1, textc=PANEL_FRONT, bcolor=PANEL_FRONT, transp=.8, interface=interface)

        ####### FOR OTHER OBJECTS ######
        if len(other_objects) > 0:
            oheader = ['Objects:']

            otext = []
            for obj in other_objects:
                otext.append(obj.fullname())
                otext.append(obj.description)
                otext.append('')

            gui.HoverInfo(header=oheader, text=otext, cx=mouse.cx+1, cy=mouse.cy+1, hoffset=1, textc=PANEL_FRONT, bcolor=PANEL_FRONT, transp=.8, interface=interface, xy_corner=1)

        ######## FOR SAPIENTS ###########
        if target and target.sapient:
            header = [target.fulltitle()]

            #if target.sapient.army:
            #    header.append(target.sapient.army.name)

            inventory = target.get_inventory()

            header.append('Wearing ' + ', '.join([item.name for item in inventory['clothing'] ]))
            header.append('Holding ' + ', '.join([item.name for item in inventory['grasped'] ]))
            header.append('Storing ' + ', '.join([item.name for item in inventory['stored'] ]))

            text = [skill + ': ' + str(value) for skill, value in target.creature.cskills.iteritems()]
            text.insert(0, target.creature.stance + ' stance')

            description = textwrap.wrap(target.description, 40)
            # Beginning with the last line, add each line of the description to the hover info
            text.insert(0, '')
            for line in reversed(description):
                text.insert(0, line)


            if target.local_brain:
                text.append(' :- - - - - - - : ')
                text.append('State: %s'%target.local_brain.ai_state )
                text.append('Target_fig: %s'%target.local_brain.target_figure.fullname() if target.local_brain.target_figure else 'Target_fig: None' )
                text.append('Target_loc: %s, %s'%(target.local_brain.target_location[0], target.local_brain.target_location[1]) if target.local_brain.target_location else 'Target_loc: None' )
                text.append('Path reset: %s'%target.local_brain.astar_refresh_cur )
                text.append('Closest_enemy: %s'%target.local_brain.perception_info['closest_enemy'])
                text.append('Closest_dist: %s'%target.local_brain.perception_info['closest_enemy_distance'])
                #text.append('State: ' + target.local_brain.ai_state )

            gui.HoverInfo(header=header, text=text, cx=mouse.cx, cy=mouse.cy, textc=PANEL_FRONT, bcolor=PANEL_FRONT, transp=.8, interface=interface)

        ### If it's a non-sapient creature....
        elif target:
            header = [target.fullname()]
            text = [target.description]

            if target.local_brain:
                text.append('')
                text.append('AI State: %s' %target.local_brain.ai_state )

            gui.HoverInfo(header=header, text=text, cx=mouse.cx, cy=mouse.cy, textc=PANEL_FRONT, bcolor=PANEL_FRONT, transp=.8, interface=interface)
        ######################################

        ## Only handle recompute if there's something uner the cursor
        ## TODO - still halves FPS while hovering over objects - this should only recompute FOV if the mouse moves
        if target or len(other_objects):
            game.handle_fov_recompute()


def infobox(header, options, xb=0, yb=0, xoffset=2, yoffset=2, textc=libtcod.grey, selcolor=libtcod.white,
            bcolor=libtcod.black, transp=.5, buttons=0):

    global mouse, key
    ## First find width of the box
    total_width = xoffset * 2
    for column in options:
        total_width += len(max(column, key=len)) + 1 # Add 1 as spacer between each column
        ## Then find height of the box
    if header == '':
        header_height = 0
    else:
        header_height = 3
    height = len(max(options, key=len)) + header_height + (yoffset * 2)

    # Give box center coords
    if xb == 0 and yb == 0:
        xb = int(round(SCREEN_WIDTH / 2)) - int(round(total_width / 2))
        yb = int(round(SCREEN_HEIGHT / 2)) - int(round(height / 2))

    #create an off-screen console that represents the menu's window
    wpanel = gui.GuiPanel(width=total_width, height=height, xoff=0, yoff=0, interface=interface,
                          is_root=0, append_to_panels=0)

    # Blit window once with desired transparency.
    libtcod.console_blit(wpanel.con, 0, 0, total_width, height, 0, xb, yb, 1.0, transp)

    event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
    while not mouse.lbutton:
        #print the header, with auto-wrap
        libtcod.console_set_default_foreground(wpanel.con, textc)
        libtcod.console_print(wpanel.con, xoffset, yoffset, header)

        cur_width = xoffset
        #print all the options
        for column in options:
            y = header_height + yoffset
            width = len(max(column, key=len))
            for entry in column:
                libtcod.console_set_default_foreground(wpanel.con, textc)
                libtcod.console_print(wpanel.con, cur_width, y, entry)
                y += 1

            cur_width += width + 1

        # Draw box around menu if parameter is selected
        if bcolor is not None:
            wpanel.draw_box(0, total_width - 1, 0, height - 1, bcolor)

        # Blit to root console + flush to present changes
        libtcod.console_blit(wpanel.con, 0, 0, total_width, height, 0, xb, yb, 1.0, 0)
        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        #key = libtcod.console_wait_for_keypress(True)
        #key = libtcod.console_check_for_keypress(False)
        #### Mouse code ####
        (mx, my) = (mouse.cx, mouse.cy)

    libtcod.console_delete(wpanel.con)

    #game.handle_fov_recompute()
    #render_handler.render_all()


def show_object_info(obj):
    ## Display information about a creature and it's status
    objlist = []
    complist = []

    objlist.append('Mass: ' + str(round(obj.get_mass(), 2)) + 'kg')
    objlist.append('Density: ' + str(round(obj.get_density(), 2)) + 'kg/m^3')

    if obj.creature:
        objlist.append('Movespeed: ' + str(obj.creature.catts['Move Speed']))
        objlist.append('Blood: ' + str(obj.creature.blood))
        objlist.append('Bleeding: ' + str(obj.creature.bleeding))

    for component in obj.components:
        name = component.name
        mass = str(round(component.get_mass(), 2))
        density = str(round(component.get_density(), 2))

        comptitle = ''.join([name, ': ', mass, 'kg, ', density, 'kg/m^3'])

        if component.grasped_item is not None:
            comptitle += '. Holding a ' + component.grasped_item.name

        complist.append(comptitle)
        ### Display attachments (packs, bags, etc)
        attached_items = []
        for attached_item_component in component.attachments:
            if attached_item_component.owner != obj and attached_item_component.owner not in attached_items:
                attached_items.append(attached_item_component.owner)

        for item in attached_items:
            complist.append(item.name)


        for layer in component.layers:
            lname = layer.material.name
            cov = str(layer.coverage)
            health = str(round(layer.health, 2) * 100)

            linfo = ' - ' + lname + ' (' + health + ' health, ' + cov + ' coverage)'
            complist.append(linfo)

        complist.append(' ')

    infobox(header=obj.name, options=[objlist, complist], xb=1, yb=1,
            xoffset=2, yoffset=2, textc=libtcod.white, selcolor=libtcod.white,
            bcolor=obj.color, transp=.8, buttons=0)

    game.handle_fov_recompute()
    #render_handler.render_all()



class Game:
    def __init__(self, interface):

        self.interface = interface
        self.interface.set_game(self)

        self.state = 'worldgen'
        self.map_scale = 'world'        self.msgs = []

        self.quit_game = 0

        self.msg_index = 0


    def get_game_msgs(self):
        ''' Get the messages to display '''
        if len(self.msgs) < MSG_HEIGHT:
            return self.msgs
        else:
            return self.msgs[self.msg_index:(self.msg_index + MSG_HEIGHT)]


    def set_msg_index(self, amount=None):
        ''' Sets the index from which messages will be read.
        Makes sure that the message index will stat within appropriate bounds '''
        if amount is None:
            self.msg_index = max(0, len(self.msgs) - MSG_HEIGHT)

        elif self.msg_index + amount < 0:
            self.msg_index = 0

        elif self.msg_index + amount > len(self.msgs) - MSG_HEIGHT:
            self.msg_index = len(self.msgs) - MSG_HEIGHT

        else:
            self.msg_index = self.msg_index + amount

    def add_message(self, new_msg, color=libtcod.white):
        #split the message if necessary, among multiple lines
        new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

        for line in new_msg_lines:
            #if the buffer is full, remove the first line to make room for the new one
            if len(self.msgs) == MSG_HEIGHT * 10:
                del self.msgs[0]
                #add the new line as a tuple, with the text and the color
            self.msgs.append((line, color))

        self.set_msg_index()


    def switch_to_quit_game(self):
        self.quit_game = 1

    def switch_map_scale(self, map_scale):
        ''' Toggles map state between larger "world" view and human-scaled map '''
        bwidth = 20
        self.map_scale = map_scale

        if self.map_scale == 'human':

            panel2.bmap_buttons = [
                                   gui.Button(gui_panel=panel2, func=player_order_move, args=[],
                                              text='Move!', topleft=(4, PANEL2_HEIGHT-26), width=10, height=5),
                                   gui.Button(gui_panel=panel2, func=player_order_follow, args=[],
                                              text='Follow Me!', topleft=(14, PANEL2_HEIGHT-26), width=10, height=5),

                                   gui.Button(gui_panel=panel2, func=debug_menu, args=[],
                                              text='Debug Panel', topleft=(4, PANEL2_HEIGHT-21), width=bwidth, height=5),
                                   gui.Button(gui_panel=panel2, func=self.return_to_worldmap, args=[], text='Return to World view',
                                      topleft=(4, PANEL2_HEIGHT-16), width=20, height=5),
                                   gui.Button(gui_panel=panel2, func=pick_up_menu, args=[], text='Pick up item',
                                      topleft=(4, PANEL2_HEIGHT-11), width=20, height=5),
                                   gui.Button(gui_panel=panel2, func=manage_inventory, args=[], text='Inventory',
                                      topleft=(4, PANEL2_HEIGHT-6), width=20, height=5)
                                   ]

        elif self.map_scale == 'world':

            panel2.wmap_buttons = [
                                   gui.Button(gui_panel=panel2, func=debug_menu, args=[],
                                              text='Debug Panel', topleft=(4, PANEL2_HEIGHT-21), width=bwidth, height=5),
                                   gui.Button(gui_panel=panel2, func=WORLD.goto_scale_map, args=[],
                                              text='Go to scale map', topleft=(4, PANEL2_HEIGHT-16), width=bwidth, height=5),
                                   gui.Button(gui_panel=panel2, func=show_civs, args=[WORLD],
                                              text='Civ info', topleft=(4, PANEL2_HEIGHT-11), width=bwidth, height=5),
                                   gui.Button(gui_panel=panel2, func=show_languages, args=[WORLD, None],
                                              text='Languages', topleft=(4, PANEL2_HEIGHT-6), width=bwidth, height=5)
                                   ]

    def handle_fov_recompute(self):
        ''' FOV / map is only re-rendered when fov_recompue is set to true '''
        if self.map_scale == 'world':
            WORLD.fov_recompute = 1
        elif self.map_scale == 'human':
            M.fov_recompute = 1


    def save_game(self):
        #open a new empty shelve (possibly overwriting an old one) to write the game data
        save_file = shelve.open('savegame', 'n')
        save_file['WORLD'] = WORLD
        save_file['time_cyle'] = time_cycle
        save_file.close()

    def load_game(self):
        #open the previously saved shelve and load the game data
        global M, WORLD, player, time_cycle
        file = shelve.open('savegame', 'r')
        WORLD = file['WORLD']
        time_cycle = file['time_cyle']
        file.close()


    def create_new_world_and_begin_game(self):
        global WORLD, camera
        # Need to first set camera
        camera = Camera(width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
        # Gen world
        WORLD = None # Clear in case previous world was generated
        WORLD = World(WORLD_WIDTH, WORLD_HEIGHT)
        WORLD.generate()
        self.game_main_loop()


    def new_game(self):
        global player

        self.switch_map_scale(map_scale='world')

        playerciv = WORLD.cities[0]
        player = playerciv.culture.create_being(sex=1, born=roll(-40, -30), char='@', dynasty=None, important=0, faction=playerciv.faction, armed=1, wx=playerciv.x, wy=playerciv.y)
        WORLD.tiles[player.wx][player.wy].entities.append(player)
        player.color = libtcod.cyan
        player.local_brain = None
        player.world_brain = None

        camera.center(player.wx, player.wy)
        self.state = 'playing'


    def game_main_loop(self):
        ''' Main game loop - handles input and renders map '''
        while not libtcod.console_is_window_closed():
            #render the screen
            render_handler.render_all(do_flush=True)
            #libtcod.console_flush()

            #handle keys and exit game if needed
            action = self.handle_keys()

            if self.quit_game or action == 'exit':
                #save_game()
                break


    def setup_quick_battle(self):
        ''' A quick and dirty battle testing arena, more or less. Will need a massive overhaul
            at some point, if it even stays in '''
        global time_cycle, camera, player, M, WORLD

        # Need to first set camera
        camera = Camera(width=CAMERA_WIDTH, height=CAMERA_HEIGHT)

        t1 = time.time()
        ##################### Create a dummy world just for the quick battle
        WORLD = World(width=3, height=3)
        WORLD.setup_world()
        WORLD.gen_sentient_races()
        cult = Culture(color=libtcod.grey, language=lang.Language(), world=WORLD, races=WORLD.sentient_races)
        for x in xrange(WORLD.width):
            for y in xrange(WORLD.height):
                WORLD.tiles[x][y].region = 'temperate forest'
                WORLD.tiles[x][y].color = libtcod.darker_sepia
                WORLD.tiles[x][y].culture = cult
                WORLD.tiles[x][y].height = 120


        ########### Factions ################
        faction1 = Faction(leader_prefix='King', faction_name='Player faction', color=random.choice(civ_colors), succession='dynasty')
        faction2 = Faction(leader_prefix='King', faction_name='Enemy faction', color=random.choice(civ_colors), succession='dynasty')
        # Set them as enemies (function will do so reciprocally)
        faction1.set_enemy_faction(faction=faction2)

        ### Make the player ###
        player = cult.create_being(sex=1, born=roll(-40, -20), char='@', dynasty=None, important=1, faction=faction1, armed=1, wx=1, wy=1)
        player.char = '@'
        player.local_brain = None

        ### Make player's party ###
        #player_party = Army(x=None, y=None, char='@', name=player.fullname() + '\'s band', color=faction1.color, speed=3,
        #                    goods=None, figures=[player], units={'Swordsmen': 10}, faction=faction1, culture=cult, ai=None)
        #player_party.world_last_dir = (0, 1)

        ### Make enemy party ###
        #enemy_army = Army(x=None, y=None, char='x', name='Enemies', color=faction2.color, speed=3,
        #                  goods=None, figures=[], units={'Swordsmen': 10}, faction=faction2, culture=cult, ai=None)
        #enemy_army.world_last_dir = (0, 0)

        hideout_site = WORLD.tiles[1][1].add_minor_site(world=WORLD, site_type='hideout', x=1, y=1, char='#', name='Hideout', color=libtcod.black, culture=cult, faction=faction2)
        hideout_building = hideout_site.create_building(zone='residential', b_type='hideout', template='temple1', professions=[], inhabitants=[], tax_status=None)
        #hideout_building.add_garrison(enemy_army)
        #WORLD.tiles[1][0].features.append(Feature(site_type='river', x=1, y=0))
        #WORLD.tiles[1][1].features.append(Feature(site_type='river', x=1, y=1))
        #WORLD.tiles[1][2].features.append(Feature(site_type='river', x=1, y=2))
        #####################################################################

        self.switch_map_scale(map_scale='human')
        self.state = 'playing'


        ## Make map
        M = Wmap(world=WORLD, wx=1, wy=1, width=MAP_WIDTH, height=MAP_HEIGHT)
        hm = M.create_heightmap_from_surrounding_tiles()
        base_color = WORLD.tiles[1][1].get_base_color()
        M.create_map_tiles(hm=hm, base_color=base_color, explored=1)
        M.run_cellular_automata(cfg=MCFG[WORLD.tiles[x][y].region])
        M.add_minor_sites_to_map()
        M.color_blocked_tiles(cfg=MCFG[WORLD.tiles[x][y].region])
        M.add_vegetation(cfg=MCFG[WORLD.tiles[x][y].region])
        M.set_initial_dmaps()
        M.add_sapients_from_world()


        # Clothing...
        ### WEARABLE Wearable
        #shirtcomps = phys.shirtcomps
        #shirt = Object(name='shirt', char='T', color=libtcod.sepia, components=shirtcomps, blocks_mov=0, blocks_vis=0,
        #               description='A shirt.', creature=None, sapient=None, ai=None, weapon=None, wearable=1, x=None, y=None)
        #player.put_on_clothing(clothing=shirt)

        packcomps = phys.packcomps
        pack = Object(name='pack', char='T', color=libtcod.sepia, components=packcomps, blocks_mov=0, blocks_vis=0,
                      description='A pack', creature=None, sapient=None, weapon=None, wearable=1, x=None, y=None)

        player.put_on_clothing(clothing=pack)
        #player.sapient.epithet = "the Wise"
        ## Deer?
        #info = phys.creature_dict['deer']
        #creature_component = Creature(creature_type='deer', sex=1)
        #deer = assemble_object(object_blueprint=info, creature=creature_component, sapient=None, ai=BasicHerbivore(), force_material=None)
        #M.add_object_to_map(x=150, y=200, obj=deer)

        ####################

        '''
        cx, cy = 150, 150
        colors = [libtcod.red, libtcod.orange, libtcod.yellow, libtcod.cyan, libtcod.blue]
        side = 20

        for color in colors:
            side += 10
            tiles = 0
            t = time.time()

            for x in xrange(cx-side, cx+1+side):
                for y in xrange(cy-side, cy+1+side):
                    if is_circle_radius(cx, cy, side, x, y):
                        M.tiles[x][y].set_color(color)
                        tiles += 1

            game.add_message('%i tiles, done in %.05f' %(tiles, time.time()-t), color)
        '''

        camera.center(player.x, player.y)

        game.add_message('loaded in %.2f seconds' %(time.time() - t1))

        # Finally, start the main game loop
        self.game_main_loop()


    def return_to_worldmap(self):
        '''
        for obj in M.objects[:]:
            if obj.ai or obj == player:
                M.objects.remove(obj)

        file = shelve.open('WORLD' + str(player_party.x) + str(player_party.y), 'n')
        file['map'] = map
        file['WORLD' + str(player_party.x) + str(player_party.y) + '.objects'] = objects
        file.close()
        '''
        M.clear_objects()

        self.switch_map_scale(map_scale='world')
        camera.center(player.wx, player.wy)


    def handle_keys(self):
        global mouse, key

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        #test for other keys
        key_char = chr(key.c)

        (x, y) = camera.cam2map(mouse.cx, mouse.cy)

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            #Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        if key.vk == libtcod.KEY_F12:
            #libtcod.sys_save_screenshot('E:\Dropbox\test.png')
            libtcod.sys_save_screenshot()

        elif key.vk == libtcod.KEY_ESCAPE:
            return 'exit'  #exit game

        if mouse.lbutton and camera.mouse_is_on_map():
            camera.click_and_drag(mouse)

        if mouse.wheel_up:
            game.set_msg_index(amount=-1)
        elif mouse.wheel_down:
            game.set_msg_index(amount=1)

        if self.state == 'playing':

            if self.map_scale == 'world':
                if key_char == 't':
                    if game.world_map_display_type == 'normal':
                        game.world_map_display_type = 'culture'
                    elif game.world_map_display_type == 'culture':
                        game.world_map_display_type = 'territory'
                    elif game.world_map_display_type == 'territory':
                        game.world_map_display_type = 'resource'
                    elif game.world_map_display_type == 'resource':
                        game.world_map_display_type = 'normal'

            if self.map_scale == 'human':
                if mouse.lbutton_pressed and camera.mouse_is_on_map():
                    # Clicking on a fellow sapient lets you talk to it
                    if len(M.tiles[x][y].objects) or M.tiles[x][y].interactable:
                        choose_object_to_interact_with(objs=M.tiles[x][y].objects, x=x, y=y)
                        #self.handle_fov_recompute()

                if key_char == 'n':
                    render_handler.debug_dijmap_view(figure=None)
                    self.handle_fov_recompute()

            #movement keys
            if key.vk == libtcod.KEY_UP or key_char == 'w' or key.vk == libtcod.KEY_KP8:
                self.player_move_or_attack(0, -1)

            elif key.vk == libtcod.KEY_DOWN or key_char == 'x' or key.vk == libtcod.KEY_KP2:
                self.player_move_or_attack(0, 1)

            elif key.vk == libtcod.KEY_LEFT or key_char == 'a' or key.vk == libtcod.KEY_KP4:
                self.player_move_or_attack(-1, 0)

            elif key.vk == libtcod.KEY_RIGHT or key_char == 'd' or key.vk == libtcod.KEY_KP6:
                self.player_move_or_attack(1, 0)

            elif key.vk == libtcod.KEY_SPACE or key_char == 's' or key.vk == libtcod.KEY_KP5:
                self.player_move_or_attack(0, 0)

            elif key_char == 'q' or key.vk == libtcod.KEY_KP7:
                self.player_move_or_attack(-1, -1)

            elif key_char == 'e' or key.vk == libtcod.KEY_KP9:
                self.player_move_or_attack(1, -1)

            elif key_char == 'c' or key.vk == libtcod.KEY_KP3:
                self.player_move_or_attack(1, 1)

            elif key_char == 'z' or key.vk == libtcod.KEY_KP1:
                self.player_move_or_attack(-1, 1)


        elif self.state == 'worldgen':
            if key.vk == libtcod.KEY_UP:
                camera.move(0, -10)

            elif key.vk == libtcod.KEY_DOWN:
                camera.move(0, 10)

            elif key.vk == libtcod.KEY_LEFT:
                camera.move(-10, 0)

            elif key.vk == libtcod.KEY_RIGHT:
                camera.move(10, 0)

    def get_key(self, key):
        ''' 'return either libtcod code or character that was pressed '''
        if key.vk == libtcod.KEY_CHAR:
            return chr(key.c)
        else:
            return key.vk


    def player_advance_time(self, ticks):
        time_cycle.rapid_tick(ticks)

        # TODO - make much more efficient
        self.handle_fov_recompute()

    def player_move_or_attack(self, dx, dy):
        if self.map_scale == 'human':
            #the coordinates the player is moving to/attacking
            x = player.x + dx
            y = player.y + dy

            if M.is_val_xy((x, y)):
                #try to find an attackable object there
                target = None
                for obj in M.tiles[x][y].objects:
                    if obj.creature and obj.creature.status != 'dead' and (obj.sapient and obj.sapient.faction in player.sapient.faction.enemy_factions):
                        target = obj
                        break
                #attack if target found, move otherwise
                if target != None:
                    ## TODO - drop random attacks when you try to move to the tile?
                    ## Or should just use whatever AI ends up happening
                    weapon = player.creature.get_current_weapon()
                    if weapon:
                        target_part = random.choice(target.components)
                        player.creature.standard_combat_attack(attacking_object_component=weapon.components[0], force=weapon.get_mass(), target=target, target_component=target_part)
                else:
                    player.move_and_face(dx, dy)
                # Advance time!
                self.player_advance_time(player.creature.catts['Move Speed'])

                camera.center(player.x, player.y)

        elif self.map_scale == 'world':
            # Change back to allow blocked movement and non-glitchy battlemap
            player.w_move(dx, dy)
            time_cycle.day_tick(1)
            camera.center(player.wx, player.wy)


def main_menu():
    global game, mouse, key
    img = libtcod.image_load('neuromancer.png')

    b_width = 20
    # Set button origin points
    bx = int(round(SCREEN_WIDTH / 2)) - int(round(b_width/2))
    sty = int(round(SCREEN_HEIGHT / 2.5))
    ## List of y vals for the buttons
    bys = []
    for i in range(4):
        bys.append(sty + (i * 7))
        ## The buttons themselves
    buttons = [gui.Button(gui_panel=root_con, func=game.create_new_world_and_begin_game, args=[],
                          text='Generate World', topleft=(bx, bys[0]), width=b_width, height=6, color=libtcod.light_grey, hcolor=libtcod.white, do_draw_box=True),
               gui.Button(gui_panel=root_con, func=game.setup_quick_battle, args=[],
                          text='Quick Battle', topleft=(bx, bys[1]), width=b_width, height=6, color=libtcod.light_grey, hcolor=libtcod.white, do_draw_box=True),
               #gui.Button(gui_panel=root_con, func=lambda:2, args=[],
               #           text='Continue Game', topleft=(bx, bys[2]), width=b_width, height=6, color=libtcod.light_grey, hcolor=libtcod.white, do_draw_box=True),
               gui.Button(gui_panel=root_con, func=game.switch_to_quit_game, args=[],
                          text='Quit', topleft=(bx, bys[3]), width=b_width, height=6, color=libtcod.light_grey, hcolor=libtcod.white, do_draw_box=True)]

    ## Start looping
    while not libtcod.console_is_window_closed():

        if game.quit_game:
            break

        active_button = None
        ## Clear the console
        libtcod.console_clear(root_con.con)
        #show the background image, at twice the regular console resolution
        #libtcod.image_blit_2x(img, 0, 0, 0)
        #libtcod.image_blit_2x(image=img, console=root_con.con, dx=0, dy=10)

        # Handle buttons
        for button in buttons:
            active_button = button.display(mouse)
            if active_button is not None:
                break

        #show the title
        libtcod.console_set_default_foreground(0, libtcod.light_grey)
        libtcod.console_print_ex(0, int(round(SCREEN_WIDTH / 2)), int(round(SCREEN_HEIGHT / 4)), libtcod.BKGND_NONE, libtcod.CENTER, 'I R O N   T E S T A M E N T')
        libtcod.console_print_ex(0, int(round(SCREEN_WIDTH / 2)), int(round(SCREEN_HEIGHT) - 2), libtcod.BKGND_NONE, libtcod.CENTER, 'By Josh Coppola - (thanks to Jotaf\'s tutorial!)')

        # Flush console
        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)


##########################################################
##########################################################
## Map stuff! ##

class PathNode:
    def __init__(self, x, y, size, neighbors):
        self.x = x
        self.y = y
        self.size = size

        self.neighbors = neighbors
        self.connected = []

    def connect(self, other, n_div, div_mag, usemap):
        coords = [(self.x, self.y)]
        for n in xrange(1, n_div):
            xc = int(round(self.x + n * (other.x - self.x) / n_div)) + roll(-div_mag, div_mag)
            yc = int(round(self.y + n * (other.y - self.y) / n_div)) + roll(-div_mag, div_mag)
            coords.append((xc, yc))
        coords.append((other.x, other.y))

        ## Go through list of coords and draw a line coord to coord. Since there was
        ## some randomization as we split up the line, it adds some windyness to the roads
        for n in xrange(len(coords) - 1):
            cur_x, cur_y = coords[n]
            next_x, next_y = coords[n + 1]
            libtcod.line_init(cur_x, cur_y, next_x, next_y)

            nx, ny = cur_x, cur_y
            while nx is not None:
                for i in xrange(self.size):
                    for j in xrange(self.size):
                        if usemap.is_val_xy((nx + i, ny + j)) and usemap.tiles[nx+i][ny+j].surface != 'road':
                        #if usemap.tiles[nx+i][ny+j].color != libtcod.cyan:
                            usemap.tiles[nx + i][ny + j].make_road('paved')

                nx, ny = libtcod.line_step()

            ## Color self ##
            #usemap.tiles[self.x][self.y].color = libtcod.cyan
            usemap.tiles[self.x][self.y].make_road('paved')

        ## Update connection info ##
        self.connected.append(other)
        other.connected.append(self)

    def find_closest_neighbors(self, num, nodes):
        ## Find x closest neighbors
        num_neighbors = len(self.neighbors)
        if num_neighbors < num:
            for i in xrange(num - num_neighbors):
                closest_dist = 10000
                closest_node = None

                for node in nodes:
                    d = get_distance_to(self.x, self.y, node.x, node.y)
                    if d < closest_dist and not node in self.neighbors and node != self:
                        closest_dist = d
                        closest_node = node

                if closest_node:
                    self.neighbors.append(closest_node)
                    closest_node.neighbors.append(self)


class StartingNode(PathNode):
    def __init__(self, x, y, size, neighbors, no_connect):
        ## Init path node object
        PathNode.__init__(self, x, y, size, neighbors)

        self.no_connect = no_connect

        for node in self.no_connect:
            node.no_connect.append(self)

    def find_closest_neighbors(self, num, nodes):
        ## Find x closest neighbors
        for i in xrange(num):
            closest_dist = 10000
            closest_node = None

            for node in nodes:
                d = get_distance_to(self.x, self.y, node.x, node.y)
                if d < closest_dist and not node in self.neighbors and not node in self.no_connect and node != self:
                    closest_dist = d
                    closest_node = node

            if closest_node:
                self.neighbors.append(closest_node)
                closest_node.neighbors.append(self)

    def connect(self, other, n_div, div_mag, usemap):
        ## Go through list of coords and draw a line coord to coord.
        libtcod.line_init(self.x, self.y, other.x, other.y)
        nx, ny = self.x, self.y
        while nx is not None:
            for i in xrange(self.size):
                for j in xrange(self.size):
                    usemap.tiles[nx + i][ny + j].make_road('paved')

            nx, ny = libtcod.line_step()
            ## Color self ##
        usemap.tiles[self.x][self.y].make_road('paved')


class CityMap:
    def __init__(self, usemap, city_class):
        self.city_class = city_class
        self.usemap = usemap

        self.all_nodes = []

        self.block_nodes = []

        self.houses = []
        self.noble_houses = []
        self.industries = []
        ## Market is list of actual tiles, not a rect
        self.markets = []

    def add_initial_nodes(self, num_nodes, min_dist):
        ### Make a bunch of new nodes. They need to be a minimum distance from others ###
        new_nodes = 0
        node_size = 2 # controls thickness of roads
        while new_nodes < num_nodes:

            use_node = False
            while not use_node:
                nx, ny = roll(10, self.usemap.width - 11), roll(10, self.usemap.height - 11)

                use_node = True
                for node in self.all_nodes:
                    if get_distance_to(nx, ny, node.x, node.y) < min_dist:
                        use_node = False
                        break

            self.all_nodes.append(PathNode(nx, ny, node_size, []))
            new_nodes += 1

    def connect_initial_nodes(self, num_neighbors):
        ## Find closest neighbors, then connect with them if you're not already
        for node in self.all_nodes:
            node.find_closest_neighbors(num_neighbors, self.all_nodes)

            for neighbor in node.neighbors:
                if not neighbor in node.connected:
                    node.connect(other=neighbor, n_div=3, div_mag=1, usemap=self.usemap)

    def generate_city_map(self, num_nodes, min_dist, disorg):
        steps = 9
        pbarname = 'Generating ' + self.city_class.name + ' map'
        render_handler.progressbar_screen(pbarname, 'creating main avenues', 1, steps)
        #### Generate the city!
        self.make_main_avenues(center=(int(round(self.usemap.width / 2)), int(round(self.usemap.height / 2))),
                               block_size=min_dist, disorg=disorg)
        #self.all_nodes = self.main_aves

        # Add a smattering of nodes
        render_handler.progressbar_screen(pbarname, 'adding nodes', 2, steps)
        self.add_initial_nodes(num_nodes, min_dist)
        # Connect them
        render_handler.progressbar_screen(pbarname, 'connecting nodes', 3, steps)
        self.connect_initial_nodes(num_neighbors=3)

        #  Set outside
        render_handler.progressbar_screen(pbarname, 'setting outer limits', 4, steps)

        ############################################
        border_cells = set(['road', 'municipal', 'wilderness'])
        def do_fill(tile):
            tile.zone = 'wilderness'

        begin = time.time()
        outside_tiles = floodfill(fmap=self.usemap, x=1, y=1, do_fill=do_fill, do_fill_args=[], is_border=lambda tile: tile.zone in border_cells)
        game.add_message('Floodfill done in %f' % (time.time()-begin), libtcod.orange)
        #############################################


        ## List of lists, each sublist contains floodfilled tiles that form city "blocks"
        development_options = []

        border_zones = set(['wilderness', 'road', 'residential', 'industrial', 'market', 'municipal', 'undeveloped'])

        render_handler.progressbar_screen(pbarname, 'finding initial lots', 5, steps)
        # Now loop through all map tiles and find developments on the inside

        ###########################
        def do_fill(tile):
            tile.zone = 'undeveloped'

        for i in xrange(self.usemap.width):
            for j in xrange(self.usemap.height):
                if self.usemap.tiles[i][j].zone not in border_zones:
                    recently_filled = floodfill(fmap=self.usemap, x=i, y=j, do_fill=do_fill, do_fill_args=[], is_border=lambda tile: tile.zone in border_zones)

                    if recently_filled != set([]):
                        ## TODO - converting to a list is inefficient, but we later need a way to grab an arbitrary element without removing it
                        development_options.append(list(recently_filled))


        has_market = False

        render_handler.progressbar_screen(pbarname, 'zoning and filling lots', 6, steps)
        for development_option in development_options:
            ## Choose a random tile to zone the lot from
            distx, disty = random.choice(development_option)

            if not has_market and 300 < len(development_option) < 400:
                print 'market will be', len(development_option), 'tiles big'
                has_market = True
                self.make_market(empty_lot=development_option, zone='market')

            elif get_distance_to(distx, disty, int(round(self.usemap.width / 2)), int(round(self.usemap.height / 2))) > ( (self.usemap.height + self.usemap.width) / 2) / 4:
                self.make_buildings(empty_lot=development_option, zone='residential')
            else:
                self.make_buildings(empty_lot=development_option, zone='industrial')

        #print(str(len(self.houses)) + ' commoner houses')
        #print(str(len(self.noble_houses)) + ' noble houses')
        #print(str(len(self.industries)) + ' industries')
        #print(str(len(self.markets)) + ' markets')

        render_handler.progressbar_screen(pbarname, 'historizing houses', 7, steps)
        self.historize_houses()
        render_handler.progressbar_screen(pbarname, 'historizing buildings', 8, steps)
        self.historize_buildings()
        render_handler.progressbar_screen(pbarname, 'placing figures', 9, steps)
        self.place_figures()


    def make_market(self, empty_lot, zone):
        # Special case - make a market
        lot = list(empty_lot)
        self.markets.append(lot)
        for x, y in lot:
            if self.usemap.tiles[x][y].surface not in ('wall', 'floor', 'road'):
                self.usemap.tiles[x][y].surface = 'floor' # Quick hack - for some reason the land will develop if we don't turn it into floor
                self.usemap.tiles[x][y].colorize(libtcod.dark_sepia)


    def make_buildings(self, empty_lot, zone):
        ## Terrible building generator
        undeveloped_spaces = list(empty_lot)

        if zone == 'residential':
            building_color = libtcod.darkest_sepia
            floor = 'dirt'
        elif zone == 'industrial':
            building_color = libtcod.darkest_grey
            floor = 'stone'

        # Check each tile in undeveloped_spaces to see if it can support a building of size INITIAL_BLDG_CHK * 2

        while undeveloped_spaces != []:
            x, y = random.choice(undeveloped_spaces)
            self.usemap.tiles[x][y].zone = zone

            usable = True
            for i in xrange(x - INITIAL_BLDG_CHK, x + INITIAL_BLDG_CHK + 1):
                for j in xrange(y - INITIAL_BLDG_CHK, y + INITIAL_BLDG_CHK + 1):
                    if self.usemap.tiles[i][j].surface in ('wall', 'floor', 'road') or not self.usemap.is_val_xy((i, j)):
                        usable = False
                        undeveloped_spaces.remove((x, y))
                        break

                if usable == False:
                    break
                    #### Create a rect and expand it in different directions
            if usable:
                newrect = Rect(x - 1, y - 1, INTIAL_BLDG_SIZE, INTIAL_BLDG_SIZE)

                expansion_dirs = ['n', 's', 'e', 'w']
                while expansion_dirs != []:
                    # I'm stupid, here's a brute force way
                    if not 2 < newrect.y1 - 1 < self.usemap.height - 2:
                        expansion_dirs.remove('n')
                    if not 2 < newrect.y2 + 1 < self.usemap.height - 2:
                        expansion_dirs.remove('s')
                    if not 2 < newrect.x1 - 1 < self.usemap.width - 2:
                        expansion_dirs.remove('w')
                    if not 2 < newrect.x2 + 1 < self.usemap.width - 2:
                        expansion_dirs.remove('e')

                    # Check size of building; if too big, stop
                    rwidth, rheight = newrect.get_dimensions()
                    if rwidth >= MAX_BUILDING_SIZE or rheight >= MAX_BUILDING_SIZE:
                        break

                    # North
                    if 'n' in expansion_dirs:
                        expand = True
                        for s in xrange(newrect.x1, newrect.x2 + 1):
                            if self.usemap.tiles[s][newrect.y1 - 1].surface in DEVELOPED_SURFACES:
                                expand = False
                                expansion_dirs.remove('n')
                                break
                        if expand:
                            newrect.expand(0, -1)
                            ## South
                    if 's' in expansion_dirs:
                        expand = True
                        for s in xrange(newrect.x1, newrect.x2 + 1):
                            if self.usemap.tiles[s][newrect.y2 + 1].surface in DEVELOPED_SURFACES:
                                expand = False
                                expansion_dirs.remove('s')
                                break
                        if expand:
                            newrect.expand(0, 1)
                            ## East
                    if 'e' in expansion_dirs:
                        expand = True
                        for t in xrange(newrect.y1, newrect.y2 + 1):
                            if self.usemap.tiles[newrect.x2 + 1][t].surface in DEVELOPED_SURFACES:
                                expand = False
                                expansion_dirs.remove('e')
                                break
                        if expand:
                            newrect.expand(1, 0)
                            ## West
                    if 'w' in expansion_dirs:
                        expand = True
                        for t in xrange(newrect.y1, newrect.y2 + 1):
                            if self.usemap.tiles[newrect.x1 - 1][t].surface in DEVELOPED_SURFACES:
                                expand = False
                                expansion_dirs.remove('w')
                                break
                        if expand:
                            newrect.expand(-1, 0)
                #### Done expanding #######

                ## Add walls to edge of building and floor to the floor
                for q in xrange(newrect.x1, newrect.x2 + 1):
                    for r in xrange(newrect.y1, newrect.y2 + 1):
                        ## Add wall or floor
                        if q in [newrect.x1, newrect.x2] or r in [newrect.y1, newrect.y2]:
                            self.usemap.tiles[q][r].make_wall(building_color)
                        else:
                            self.usemap.tiles[q][r].make_floor(floor_type=floor)


                ## Door code take 1
                has_door = False
                '''
                # First check if midpoint on a wall is already connected to a roadway
                for mpx, mpy in (newrect.middle_point('n'), newrect.middle_point('s'), newrect.middle_point('e'), newrect.middle_point('w')):
                    if 'road' in (self.usemap.tiles[mpx - 1][mpy].zone, self.usemap.tiles[mpx + 1][mpy].zone, self.usemap.tiles[mpx][mpy - 1].zone, self.usemap.tiles[mpx][mpy + 1].zone):
                        ### DOOR!
                        self.usemap.make_door(x=mpx, y=mpy, floor_type=floor)
                        has_door = True
                        break
                '''
                if not has_door:
                    # If midpoint is not already connected, check each direction in turn to see if we can make a path straight to the road
                    directions = {(0, -1): newrect.middle_point('n'), (0, 1): newrect.middle_point('s'),
                                  (1, 0): newrect.middle_point('e'), (-1, 0): newrect.middle_point('w')}

                    for (dx, dy), (mpx, mpy) in directions.iteritems():
                        # Go through each direction in turn. If one direction already yielded a door, stop
                        px, py = mpx, mpy
                        path = []
                        iter = 0
                        # Give it 6 spaces to try to hit a road
                        while iter != 10:
                            iter += 1
                            ## First possibility: Found road!
                            if self.usemap.tiles[px + dx][py + dy].surface == 'road':
                                self.usemap.make_door(x=mpx, y=mpy, floor_type=floor)
                                for tx, ty in path:
                                    self.usemap.tiles[tx][ty].make_road('paved')
                                    #### DOOR!
                                has_door = True
                                break

                            ## Second possibility: we run into something we don't want, and must stop to try another direction
                            elif self.usemap.tiles[px + dx][py + dy].surface in DEVELOPED_SURFACES:
                                break

                            ## If we didn't already hit something but didn't find a road, add to current path
                            else:
                                px = px + dx
                                py = py + dy
                                path.append((px, py))

                        if has_door:
                            door_dir, door_point = (dx, dy), (mpx, mpy)
                            break



                if has_door:
                    if zone == 'residential' and newrect.get_size() < 80:
                        self.houses.append(newrect)
                    elif zone == 'residential':
                        self.noble_houses.append(newrect)
                    elif zone == 'industrial':
                        self.industries.append(newrect)

                        # Color starting node black
                        #self.usemap.tiles[x][y].color = libtcod.black

        surfaces = set(['wall', 'floor', 'road', 'water'])
        for x, y in empty_lot:
            if self.usemap.tiles[x][y].surface not in surfaces:
                self.usemap.tiles[x][y].colorize(libtcod.darker_sepia)
                ## Only place these items near a wall
                near_wall = 0
                for (tx, ty) in get_border_tiles(x, y):
                    if M.is_val_xy(coords=(tx, ty)) and M.tiles[tx][ty].surface == 'wall':
                        near_wall = 1
                        break

                if near_wall:
                    num = roll(1, 30)
                    if num == 1:
                        self.usemap.create_and_add_object(name='crate', x=x, y=y)
                    elif num == 2:
                        self.usemap.create_and_add_object(name='barrel', x=x, y=y)
                    elif num == 3:
                        self.usemap.create_and_add_object(name='pottery', x=x, y=y)



    def place_figures(self):
        ## Place historical figures on the map

        # A list of figures who have been placed so far
        placed_figures = []

        for building in self.city_class.buildings:
            for employee in building.current_workers:
                building.place_within(obj=employee)
                placed_figures.append(employee)

            ''' Why doesn't this always work?
            if building.b_type == 'Tavern':
                for i in xrange(roll(1, 3)):
                    human = self.city_class.create_inhabitant(sex=1, born=time_cycle.current_year-roll(16, 35), char='o', dynasty=None, important=0, house=None)
                    building.place_within(obj=human)
            '''

            for member in building.inhabitants:
                if member not in placed_figures:
                    building.place_within(obj=member)
                    placed_figures.append(member)

            # Ug
            building.add_housed_objects_to_map()

        ### Adding agents from the economy to the city
        profession_to_business = {'Blacksmith':'Foundry', 'Potter':'Kiln', 'Carpenter':'Carpenter Workshop', 'Clothier':'Clothier Workshop'}

        for good_producer in self.city_class.econ.good_producers:
            work_tiles = random.choice(self.industries)
            home_tiles = random.choice(self.houses)

            self.industries.remove(work_tiles)
            self.houses.remove(home_tiles)

            ## Choose a title for the business
            professions = [Profession(name=good_producer.name, category='commoner')]
            ptype = good_producer.name.split(' ')[1]
            new_building = self.city_class.create_building(zone='commercial', b_type=profession_to_business[ptype],
                                    template='TEST', professions=professions, inhabitants=[], tax_status='commoner')


            ## Fill positions
            new_building.fill_initial_positions()
            # The first employee listed is the actual economy agent
            new_building.current_workers[0].sapient.economy_agent = good_producer


            for x in xrange(work_tiles.x1, work_tiles.x2 + 1):
                for y in xrange(work_tiles.y1, work_tiles.y2 + 1):
                    new_building.physical_property.append((x, y))
                    self.usemap.tiles[x][y].building = new_building

            for employee in new_building.current_workers:
                new_building.place_within(obj=employee)
                placed_figures.append(employee)

            #### WILL ONLY CREATE HOUSE FOR FIRST EMPLOYEE
            # And will not place employee in house
            household = self.city_class.create_building(zone='residential', b_type='house', template='TEST', professions=[], inhabitants=[new_building.current_workers[0]], tax_status='commoner')

            for x in xrange(home_tiles.x1, home_tiles.x2 + 1):
                for y in xrange(home_tiles.y1, home_tiles.y2 + 1):
                    household.physical_property.append((x, y))
                    self.usemap.tiles[x][y].building = household

        taverns = [building for building in self.city_class.buildings if building.b_type == 'Tavern']
        #for figure in self.city_class.figures:
        for entity in WORLD.tiles[self.city_class.x][self.city_class.y].entities:
            if entity not in placed_figures:
                tavern = random.choice(taverns)
                tavern.place_within(obj=entity)

        ## Add some schmoes to recruit
        for tavern in taverns:
            for i in xrange(2):
                schmoe = self.city_class.create_inhabitant(sex=1, born=time_cycle.current_year-roll(16, 35), char='o', dynasty=None, important=0, house=None)

                tavern.place_within(obj=schmoe)



    def historize_houses(self):
        ## Add in historical figures from the city info to the city
        big_house_categories = ('noble', 'religion', 'merchant')
        ## Loop through the list of historical houses
        for i, building in enumerate(self.city_class.buildings):
            big_house = False
            for figure in building.inhabitants:
                if figure.sapient.profession and figure.sapient.profession.category in big_house_categories:
                    big_house = True
                    break

            if big_house and len(self.noble_houses):
                b_rect = random.choice(self.noble_houses)
                self.noble_houses.remove(b_rect)
            else:
                b_rect = random.choice(self.houses)
                self.houses.remove(b_rect)

            for x in xrange(b_rect.x1, b_rect.x2 + 1):
                for y in xrange(b_rect.y1, b_rect.y2 + 1):
                    self.usemap.tiles[x][y].building = building
                    building.physical_property.append((x, y))


    def historize_buildings(self):
        ## Add in historical figures from the city info to the city
        market = self.city_class.get_building('Market')
        for x, y in self.markets[0]:
            self.usemap.tiles[x][y].building = market
        market.physical_property = self.markets[0]

        ## Loop through the list of historical buildings
        for i, building in enumerate(self.city_class.buildings):

            if not building.physical_property:
                phys_building = random.choice(self.industries)
                self.industries.remove(phys_building)

                for x in xrange(phys_building.x1, phys_building.x2 + 1):
                    for y in xrange(phys_building.y1, phys_building.y2 + 1):
                        self.usemap.tiles[x][y].building = building
                        self.city_class.buildings[i].physical_property.append((x, y))


    def make_municipal_bldg(self, x, y, w, h, road_thickness, building_info):
        ''' Municipal buildings are government-owned '''
        physical_property = []
        for i in xrange(x, x + w):
            for j in xrange(y, y + h):
                self.usemap.tiles[i][j].zone = 'municipal'
                self.usemap.tiles[i][j].building = building_info
                physical_property.append((i, j))

                if i in [x, x + w - 1] or j in [y, y + h - 1]:
                    self.usemap.tiles[i][j].make_wall(libtcod.darkest_grey)
                else:
                    self.usemap.tiles[i][j].make_floor(floor_type='stone')

        door_x, door_y = int(round((x + (x + w)) / 2)), y + h - 1

        self.usemap.make_door(x=door_x, y=door_y, floor_type='stone')

        building_info.physical_property = physical_property

        c1 = StartingNode(x - road_thickness, y - road_thickness, road_thickness, [], [])
        c2 = StartingNode(x - road_thickness, y + h, road_thickness, [c1], [])
        c3 = StartingNode(x + w, y - road_thickness, road_thickness, [c1], [c2])
        c4 = StartingNode(x + w, y + h, road_thickness, [c2, c3], [c1])

        self.all_nodes.append(c1)
        self.all_nodes.append(c2)
        self.all_nodes.append(c3)
        self.all_nodes.append(c4)

    def make_main_avenues(self, center, block_size, disorg):
        self.cx, self.cy = center
        block_size = block_size
        self.all_nodes = []

        road_thickness = 2

        building = self.city_class.get_building('City Hall')
        self.make_municipal_bldg(x=self.cx, y=self.cy, w=block_size, h=block_size, road_thickness=road_thickness, building_info=building)

        temple = self.city_class.get_building('Temple')
        self.make_municipal_bldg(x=self.cx-60, y=self.cy, w=block_size, h=block_size, road_thickness=road_thickness, building_info=temple)


        xlen = block_size * 3
        ylen = block_size * 3
        '''
		p = 3
		self.main_aves = []
		#self.main_aves = [PathNode(owner=self, x=self.cx, y=self.cy, size=p, neighbors=[])]

		## avenue going across the x axis. Offset will "tip" to one size
		self.main_aves.append(PathNode(self, self.cx + xlen, self.cy, p, []))
		self.main_aves.append(PathNode(self, self.cx - xlen, self.cy, p, []))

		## avenue going across the y axis. Offset will "tip" to one size
		self.main_aves.append(PathNode(self, self.cx, self.cy + ylen, p, []))
		self.main_aves.append(PathNode(self, self.cx, self.cy - ylen, p, []))

		for node in self.main_aves:
			for neighbor in node.neighbors:
				node.connect(other=neighbor, n_div=3, div_mag=2, usemap=self.usemap)
		'''

        road_thick = 2
        sx, sy = self.cx - xlen, self.cy - ylen

        num_roads = 6
        num_avenues = 6

        avoid_node_size = 15

        for x in xrange(num_roads):
            for y in xrange(num_avenues):

                xoff = roll(-disorg, disorg)
                yoff = roll(-disorg, disorg)

                node_x = sx + (x * block_size) + xoff
                node_y = sy + (y * block_size) + yoff

                use_node = True
                for node in self.all_nodes:
                    if get_distance_to(node_x, node_y, node.x, node.y) < avoid_node_size:
                        use_node = False
                        break

                if use_node:
                    self.all_nodes.append(PathNode(node_x, node_y, road_thick, []))

                    ## Add main aves to streets
                    #self.all_nodes = self.all_nodes + self.main_aves



########################################
########################################
## End map stuff!



def show_people(world):
    # Show people within realms
    curr_p = 0 # current person
    city_number = 0 # City #

    x_att_offset = 10 #  where to offset attribute offsets from
    x_list_offset = 35 #where to offset list of people from

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
        libtcod.console_set_default_foreground(0, libtcod.white)
        libtcod.console_print(0, 2, 2, 'Civ people (ESC to exit, LEFT and RIGHT arrows to scroll)')

        selected_person = world.tiles[world.cities[city_number].x][world.cities[city_number].y].entities[curr_p]
        s_att = selected_person.sapient
        ## Traits ##
        y = 7
        libtcod.console_print(0, x_att_offset, y - 1, 'Skills')
        for skill, amount in selected_person.sapient.skills.iteritems():
            y += 1
            libtcod.console_print(0, x_att_offset, y, skill + ': ' + str(amount))
            ## Skills ##
        y += 2
        libtcod.console_print(0, x_att_offset, y, 'Traits')
        y += 1
        for trait, m in selected_person.sapient.traits.iteritems():
            y += 1
            libtcod.console_print(0, x_att_offset, y, tdesc(trait, m))

        ###
        color = libtcod.white
        libtcod.console_set_default_foreground(0, color)

        libtcod.console_print(0, x_att_offset, 4, '<< ' + world.tiles[world.cities[city_number].x][world.cities[city_number].y].entities[curr_p].fullname() + ' >>')
        ##### Only show people who this person knows personally for now
        y = 0
        for other_person in selected_person.sapient.knowledge.keys():
            if y + 20 > SCREEN_HEIGHT: # Just make sure we don't write off the screen...
                libtcod.console_print(0, x_list_offset, y + 9, '<<< more >>>')
                break

            # Use total opinions (includes trait info)
            total_opinion = selected_person.sapient.get_relations(other_person)
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
                                  other_person.sapient.owner.fullname() + ' (' + str(opinion) + ')')
            y += 1
            for reason, amount in total_opinion.iteritems():
                libtcod.console_print(0, x_list_offset, y + 8, reason + ': ' + str(amount))
                y += 1


            ### Flush, and check keys ###
        libtcod.console_flush()

        key = libtcod.console_wait_for_keypress(False)
        key_pressed = game.get_key(key)


def show_languages(world, spec_language=None):
    lang_number = 0

    key_pressed = None
    event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

    while key_pressed != libtcod.KEY_ESCAPE:

        if spec_language == None:
            if key_pressed == libtcod.KEY_LEFT:
                lang_number -= 1
            if key_pressed == libtcod.KEY_RIGHT:
                lang_number += 1

            if lang_number < 0:
                lang_number = len(world.languages) - 1
            elif lang_number > len(world.languages) - 1:
                lang_number = 0

            language = world.languages[lang_number]

        else:
            language = spec_language

        libtcod.console_clear(0) ## 0 should be variable "con"?


        #### General ######
        root_con.draw_box(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1, PANEL_FRONT) #Box around everything

        root_con.draw_box(1, SCREEN_WIDTH - 2, 1, 6, PANEL_FRONT)

        libtcod.console_print(0, 2, 2,
                              'Languages (ESC to exit, LEFT and RIGHT arrows to scroll)')

        libtcod.console_set_default_foreground(0, PANEL_FRONT)
        libtcod.console_print(0, 4, 4, '-* The language of ' + language.name + ' *-')

        ###### PHONOLOGY ########
        root_con.draw_box(x=1, x2=40, y=7, y2=7 + 2 + len(language.consonants), color=PANEL_FRONT)
        y = 8
        libtcod.console_print(0, 4, y, ''.join(['Consonants in ', language.name]))
        for consonant in language.consonants:
            y += 1
            cnum = consonant.num
            libtcod.console_print(0, 4, y, language.orthography.mapping[cnum])

            description = ''.join([lang.PHON_TO_ENG_EXAMPLES[cnum]])
            libtcod.console_print(0, 7, y, description)

        y += 4
        root_con.draw_box(x=1, x2=40, y=y - 1, y2=y - 1 + 2 + len(language.vowel_freqs), color=PANEL_FRONT)
        libtcod.console_print(0, 4, y, ''.join(['Vowels in ', language.name]))
        for (vnum, vfreq) in language.vowel_freqs:
            y += 1
            libtcod.console_print(0, 4, y, language.orthography.mapping[vnum])

            description = ''.join([lang.PHON_TO_ENG_EXAMPLES[vnum]])
            libtcod.console_print(0, 7, y, description)
            ###### / PHONOLOGY #######

        ###### VOCABULARY ########
        y = 8
        root_con.draw_box(x=41, x2=68, y=y - 1, y2=y - 1 + 2 + len(language.vocabulary.keys()), color=PANEL_FRONT)
        libtcod.console_print(0, 43, y, ''.join(['Basic ', language.name, ' vocabulary']))
        sorted_vocab = [(k, v) for k, v in language.vocabulary.iteritems()]
        sorted_vocab.sort()
        for (eng_word, word) in sorted_vocab:
            y += 1
            if y > SCREEN_HEIGHT - 2:
                break
            libtcod.console_print(0, 43, y, eng_word)

            libtcod.console_print(0, 55, y, word)

        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        #key = libtcod.console_check_for_keypress(True)
        key_pressed = game.get_key(key)




def show_civs(world):
    city_number = 0
    minr, maxr = 0, SCREEN_HEIGHT - 6

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
            minr, maxr = 0, SCREEN_HEIGHT - 6
        if key_pressed == libtcod.KEY_RIGHT:
            city_number += 1
            minr, maxr = 0, SCREEN_HEIGHT - 6

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
            economy_tab(world=world)
        elif key_pressed == 'b':
            view = 'building'
        elif key_pressed == 'f':
            view = 'figures'
        elif key_pressed == 'l':
            show_languages(world=world, spec_language=city.culture.language)
        elif key_pressed == 'r':
            world.cities[city_number].econ.run_simulation()



        #### General ######
        root_con.draw_box(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1, PANEL_FRONT) #Box around everything
        root_con.draw_box(1, SCREEN_WIDTH - 2, 1, 7, PANEL_FRONT)
        libtcod.console_print(0, 2, 2, 'Civilizations (ESC to exit, LEFT and RIGHT arrows to change city, PGUP PGDOWN to scroll vertically)')
        libtcod.console_print(0, 2, 4, '<p> Show people    <b> Show buildings    <f> Show figures    <e> Show economy    <d> Detailed economy    <l> Language')

        #libtcod.console_print_left(0, 2, 4, libtcod.BKGND_NONE, '-* ' + city.name + ' *-')
        #libtcod.console_set_default_foreground(0, libtcod.color_lerp(city.color, PANEL_FRONT, .5))
        #libtcod.console_print_left(0, 2, 5, libtcod.BKGND_NONE, '-* ' + city.name + ' *-' + str(len(city.territory)) + ' square km. Access to: ' + ', '.join(city.native_res.keys()))
        #libtcod.console_set_default_foreground(0, PANEL_FRONT)

        ## Show government type - left panel
        root_con.draw_box(1, 28, 8, SCREEN_HEIGHT - 2, PANEL_FRONT) # Around relations
        # Check for title holder
        if city.faction.leader:
            title_info = ' '.join([city.faction.leader_prefix, city.faction.get_leader().fullname(), 'age', str(city.faction.get_leader().sapient.get_age())])
        else:
            title_info = 'No holder'
        libtcod.console_print(0, 2, 11, title_info)
        libtcod.console_print(0, 2, 12, 'Dynastic heirs:')

        y = 13
        for heir in city.faction.heirs:
            libtcod.console_print(0, 2, y, heir.fullname() + ', age ' + str(heir.sapient.get_age()))
            y += 1

        ######### Cities and governers #############
        root_con.draw_box(29, SCREEN_WIDTH - 2, 8, SCREEN_HEIGHT - 2, PANEL_FRONT) # Around cities + govs

        y = 14
        libtcod.console_set_default_foreground(0, libtcod.color_lerp(city.color, PANEL_FRONT, .5))
        libtcod.console_print(0, 32, y - 4, 'City of ' + city.name + ' (Population: ' + str(
            city.get_population()) + ', Treasury: ' + str(city.treasury) + ')')
        libtcod.console_print(0, 32, y - 3, 'Immediate access to: ' + ', '.join(city.native_res.keys()))
        if city.faction.parent == None:
            liege = ' * Independent *  '
        else:
            liege = 'Vassal to ' + city.faction.parent.site.name + '. '
        libtcod.console_print(0, 32, y - 2, liege + 'Vassals: ' + ', '.join([vassal.site.name for vassal in city.faction.subfactions]))
        libtcod.console_set_default_foreground(0, PANEL_FRONT)

        if view == 'building':
            ####### Positions of interest in the city ###########
            libtcod.console_print(0, 32, y, '-* Important structures *-')

            y += 1
            for building in city.buildings:
                y += 1
                if y > SCREEN_HEIGHT - 12:
                    libtcod.console_print(0, 32, y, '<< More >> ')
                    break

                libtcod.console_print(0, 32, y, '-* ' + building.name + ' *- ')
                for worker in building.current_workers:
                    y += 1
                    libtcod.console_print(0, 32, y, worker.fulltitle())
                y += 1


        elif view == 'economy':

            ####### AGENTS ############
            libtcod.console_set_default_foreground(0, PANEL_FRONT * .7)
            libtcod.console_print(0, 32, y, 'Agent name')
            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.yellow, PANEL_FRONT, .7))
            libtcod.console_print(0, 60, y, 'Gold')
            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.blue, PANEL_FRONT, .7))
            libtcod.console_print_ex(0, 70, y, libtcod.BKGND_NONE, libtcod.RIGHT, 'Buys')
            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.cyan, PANEL_FRONT, .7))
            libtcod.console_print(0, 72, y, 'Sells')
            libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.green, PANEL_FRONT, .7))
            libtcod.console_print(0, 78, y, 'Alive')

            libtcod.console_set_default_foreground(0, PANEL_FRONT)


            all_agents = (city.econ.resource_gatherers + city.econ.good_producers + city.econ.buy_merchants + city.econ.sell_merchants)
            merchants = (city.econ.buy_merchants + city.econ.sell_merchants)

            for agent in all_agents[minr:maxr]:
                y += 1
                if y > SCREEN_HEIGHT - 5:
                    break


                if agent in merchants and agent.current_location == city:
                    agent_name = agent.name + ' (here)'
                elif agent in merchants and agent.current_location != None:
                    agent_name = agent.name + ' (' + agent.current_location.owner.name + ')'
                else:
                    agent_name = agent.name

                if agent.attached_to == player:
                    agent_name += ' (you)'

                ### (debug) Player can take on role of economy agent at a whim
                if mouse.cy == y and 32 <= mouse.cx <= 85:
                    acolor = libtcod.dark_yellow

                    # Set the player to "become" one of these agents
                    if mouse.lbutton_pressed:
                        agent.update_holder(figure=player)
                        panel4.render = True
                        pcolor = libtcod.color_lerp(PANEL_FRONT, libtcod.light_green, .5)
                        hcolor = pcolor * 2
                        panel4.wmap_buttons.append(gui.Button(gui_panel=panel4, func=time_cycle.goto_next_week, args=[],
                                                              text='Advance', topleft=(15, 40), width=12, height=3, color=pcolor, hcolor=hcolor, do_draw_box=True) )

                else:
                    acolor = PANEL_FRONT

                libtcod.console_set_default_foreground(0, acolor)
                libtcod.console_print(0, 32, y, agent_name[:26])
                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.yellow, PANEL_FRONT, .7))
                libtcod.console_print(0, 60, y, str(agent.gold))
                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.blue, PANEL_FRONT, .7))
                libtcod.console_print(0, 68, y, str(agent.buys))
                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.cyan, PANEL_FRONT, .7))
                libtcod.console_print(0, 73, y, str(agent.sells))
                libtcod.console_set_default_foreground(0, libtcod.color_lerp(libtcod.green, PANEL_FRONT, .7))
                libtcod.console_print(0, 78, y, str(agent.turns_alive))

            # Set color back
            libtcod.console_set_default_foreground(0, PANEL_FRONT)
            ###### End print individual agents ######

            ## Print good info ##
            y = 12
            libtcod.console_print(0, 85, y - 2, 'Most demanded last turn: ' + city.econ.find_most_demanded_commodity())

            libtcod.console_print(0, 85, y, 'Commodity')
            libtcod.console_print_ex(0, 101, y, libtcod.BKGND_NONE, libtcod.RIGHT, 'Avg$')
            libtcod.console_print(0, 103, y, 'Last$')
            libtcod.console_print_ex(0, 112, y, libtcod.BKGND_NONE, libtcod.RIGHT, 'Sply')
            libtcod.console_print_ex(0, 117, y, libtcod.BKGND_NONE, libtcod.RIGHT, 'Dmnd')
            libtcod.console_print_ex(0, 121, y, libtcod.BKGND_NONE, libtcod.RIGHT, 'D:S')
            libtcod.console_print(0, 124, y, '#')

            y += 2

            for commodity, auction in city.econ.auctions.iteritems():
                if auction.supply != None and auction.demand != None:
                    libtcod.console_print(0, 85, y, commodity)
                    libtcod.console_print(0, 100, y, str(auction.mean_price))

                    # Color trades - green means price last round was > than avg, red means < than avg
                    if auction.mean_price <= auction.price_history[-1]:
                        color = libtcod.color_lerp(libtcod.green, PANEL_FRONT,
                                                   auction.mean_price / auction.price_history[-1])
                    else:
                        color = libtcod.color_lerp(libtcod.red, PANEL_FRONT,
                                                   auction.price_history[-1] / auction.mean_price)
                    libtcod.console_set_default_foreground(0, color)
                    libtcod.console_print(0, 105, y, str(auction.price_history[-1]))
                    ## /color trades
                    libtcod.console_set_default_foreground(0, PANEL_FRONT)
                    libtcod.console_print(0, 110, y, str(auction.supply))
                    libtcod.console_print(0, 114, y, str(auction.demand))
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

                    libtcod.console_set_default_foreground(0, libtcod.color_lerp(color, PANEL_FRONT, color_mod))
                    libtcod.console_print(0, 118, y, "{0:.2f}".format(round(d_s_ratio, 2)))
                    libtcod.console_set_default_foreground(0, PANEL_FRONT)

                    # Iteration in economy
                    libtcod.console_print(0, 124, y, str(auction.iterations))
                    y += 1

            ### Good info ###
            y += 3
            libtcod.console_print(0, 85, y - 1, '-* Imports *-')
            for other_city, commodities in city.imports.iteritems():
                for commodity in commodities:
                    y += 1
                    if y < SCREEN_HEIGHT - 5:
                        libtcod.console_print(0, 85, y, commodity + ' from ' + other_city.name)

            y += 3
            libtcod.console_print(0, 85, y - 1, '-* Exports *-')
            for other_city, commodities in city.exports.iteritems():
                for commodity in commodities:
                    y += 1
                    if y < SCREEN_HEIGHT - 5:
                        libtcod.console_print(0, 85, y, commodity + ' to ' + other_city.name)
                        ## End print good info ##


        elif view == 'figures':
            selected = False
            ## Figures currently residing here
            y = 16
            ny = y # for opinions

            libtcod.console_print(0, 34, y - 2, str(len(world.tiles[city.x][city.y].entities)) + ' notable characters')
            for figure in world.tiles[city.x][city.y].entities:
                if y > SCREEN_HEIGHT - 5:
                    break

                ##
                #if 34 <= mouse.cx <= 34+len(figure.fullname()) and mouse.cy == y:
                if 34 <= mouse.cx <= 60 + len(figure.sapient.get_profession()) and mouse.cy == y:
                    selected = True

                    if figure.creature.sex:
                        symb = chr(11)
                        color = libtcod.light_blue
                    else:
                        color = libtcod.light_red
                        symb = chr(12)

                    libtcod.console_set_default_foreground(0, color)
                    libtcod.console_print(0, 85, ny, symb)
                    libtcod.console_set_default_foreground(0, PANEL_FRONT)

                    libtcod.console_print(0, 87, ny, figure.fullname())
                    libtcod.console_print(0, 85, ny + 1,
                                          figure.sapient.get_profession() + ', age ' + str(figure.sapient.get_age()))

                    spouseinfo = 'No spouse'
                    if figure.sapient.spouse:
                        end = ''
                        if figure.sapient.spouse.creature.status == 'dead':
                            end = ' (dead)'
                        spouseinfo = 'Married to ' + figure.sapient.spouse.fulltitle() + end

                    libtcod.console_print(0, 85, ny + 2, spouseinfo)

                    if figure.sapient.current_citizenship == city:
                        info = 'Currently lives here'
                    else:
                    #    info = 'Staying at ' + random.choice(city.get_building_type('Tavern')).get_name()
                        info = 'Currently visiting'

                    libtcod.console_print(0, 85, ny + 3, info)

                    ny += 4
                    for trait, m in figure.sapient.traits.iteritems():
                        libtcod.console_print(0, 85, ny + 1, tdesc(trait, m))
                        ny += 1

                    ny += 1
                    for issue, (opinion, reasons) in figure.sapient.opinions.iteritems():
                        ny += 1
                        ##
                        s = issue + ': ' + str(opinion)
                        libtcod.console_print(0, 85, ny, s)
                        for reason, amount in reasons.iteritems():
                            ny += 1
                            libtcod.console_print(0, 86, ny, reason + ': ' + str(amount))

                if selected:
                    libtcod.console_set_default_foreground(0, libtcod.color_lerp(PANEL_FRONT, libtcod.yellow, .5))
                    selected = False

                elif libtcod.console_get_default_foreground != PANEL_FRONT:
                    libtcod.console_set_default_foreground(0, PANEL_FRONT)

                libtcod.console_print(0, 34, y, figure.fullname())

                libtcod.console_print(0, 57, y, str(figure.sapient.get_age()))

                libtcod.console_print(0, 60, y, figure.sapient.get_profession())

                if figure.sapient.dynasty:
                    libtcod.console_put_char_ex(0, 32, y, figure.sapient.dynasty.symbol,
                                                figure.sapient.dynasty.symbol_color,
                                                figure.sapient.dynasty.background_color)

                if figure.creature.sex:
                    symb = chr(11)
                    color = libtcod.light_blue
                else:
                    color = libtcod.light_red
                    symb = chr(12)

                libtcod.console_set_default_foreground(0, color)
                libtcod.console_print(0, 55, y, symb)
                libtcod.console_set_default_foreground(0, PANEL_FRONT)


                # Increase so next figure goes onto next line
                y += 1

        libtcod.console_flush()

        event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        #key = libtcod.console_check_for_keypress(True)
        key_pressed = game.get_key(key)


def economy_tab(world):
    global mouse, key
    city_number = 0
    agent_index = 0
    view = 'economy'
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
            city_number -= 1
            agent_index = 0
        if key_pressed == libtcod.KEY_DOWN:
            city_number += 1
            agent_index = 0

        elif key_pressed == 'p':
            show_people(world=world)
        elif key_pressed == 'e':
            view = 'economy'
        elif key_pressed == 'b':
            view = 'building'
        elif key_pressed == 'r':
            world.cities[city_number].econ.run_simulation()

        if city_number < 0:
            city_number = len(world.cities) - 1
        elif city_number > len(world.cities) - 1:
            city_number = 0

        libtcod.console_clear(0) ## 0 should be variable "con"?

        #### Set current variables ####
        city = world.cities[city_number]
        ################################

        #### General ######
        root_con.draw_box(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1, PANEL_FRONT) #Box around everything
        root_con.draw_box(1, SCREEN_WIDTH - 2, 1, 7, PANEL_FRONT)
        libtcod.console_print(0, 2, 2, 'Civilizations (ESC to exit, LEFT and RIGHT arrows to scroll)')
        libtcod.console_print(0, 2, 4,
                              '<p> - Show people    <b> - Show buildings    <f> - Show figures    <e> Show economy')

        #libtcod.console_set_default_foreground(0, libtcod.color_lerp(city.color, PANEL_FRONT, .5))
        #libtcod.console_print_left(0, 2, 4, libtcod.BKGND_NONE, '-* ' + city.name + ' *-')

        libtcod.console_set_default_foreground(0, PANEL_FRONT)
        libtcod.console_print(0, 2, 5,
                              str(len(city.territory)) + ' square km. Access to: ' + ', '.join(city.native_res.keys()))

        ####### AGENTS ############
        y = 10

        libtcod.console_set_default_foreground(0, PANEL_FRONT * .7)
        libtcod.console_print(0, 5, y, 'Agent name')
        libtcod.console_print(0, 25, y, 'Inventory')
        libtcod.console_print(0, 45, y, 'Beliefs')

        libtcod.console_set_default_foreground(0, PANEL_FRONT)
        #for agent in city.econ.resource_gatherers + city.econ.good_producers + city.econ.buy_merchants + city.econ.sell_merchants:
        iy, cy, ly = y, y, y
        agent_list = city.econ.resource_gatherers + city.econ.good_producers + city.econ.buy_merchants + city.econ.sell_merchants
        if agent_index > len(agent_list) - 6:
            agent_index = len(agent_list) - 6
        for agent in agent_list[agent_index:agent_index + 6]:
            y = max(iy, cy, ly, y + 6) + 1
            if y > 70:
                break
            libtcod.console_print(0, 5, y, agent.name)
            libtcod.console_print(0, 5, y + 1, str(agent.gold) + ' gold')
            libtcod.console_print(0, 5, y + 2, str(agent.buys) + ' buys')
            libtcod.console_print(0, 5, y + 3, str(agent.sells) + ' sells')
            libtcod.console_print(0, 5, y + 4, 'Alive: ' + str(agent.turns_alive))
            libtcod.console_print(0, 5, y + 5, str(agent.turns_since_food) + ' since food')

            inventory = Counter(agent.inventory)
            iy = y
            for item, amount in inventory.iteritems():
                libtcod.console_print(0, 25, iy, item + ' (' + str(amount) + ')')
                iy += 1
                if iy > 70: break

            cy, ly = y, y
            if agent in city.econ.resource_gatherers + city.econ.good_producers:
                for commodity, value in agent.perceived_values.iteritems():
                    libtcod.console_print(0, 45, cy, commodity + ': ' + str(value.center) + ' (' + str(value.uncertainty) + ')')
                    cy += 1
                    if cy > 70: break

                for j in xrange(len(agent.last_turn)):
                    libtcod.console_print(0, 70, ly, agent.last_turn[j])
                    ly += 1
                    if ly > 70: break

            elif agent in city.econ.buy_merchants + city.econ.sell_merchants and agent.current_location == city.econ:
                for commodity, value in agent.buy_perceived_values.iteritems():
                    libtcod.console_print(0, 45, cy, agent.buy_economy.owner.name + ' - ' + commodity + ': ' + str(value.center) + ' (' + str(value.uncertainty) + ')')
                    cy += 1
                    if cy > 70: break
                for commodity, value in agent.sell_perceived_values.iteritems():
                    libtcod.console_print(0, 45, cy, agent.sell_economy.owner.name + ' - ' + commodity + ': ' + str(value.center) + ' (' + str(value.uncertainty) + ')')
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
        #key = libtcod.console_check_for_keypress(True)
        key_pressed = game.get_key(key)


##### START GAME #####
if __name__ == '__main__':
    global interface, render_handler, game

    #SCREEN_RES = (1920, 1080)
    #SCREEN_RES = (1366, 768)
    #SCREEN_RES = libtcod.sys_get_current_resolution()
    TILE_SIZE = 12
    #actual size of the window
    SCREEN_WIDTH = int(SCREEN_RES[0]/TILE_SIZE)
    SCREEN_HEIGHT = int(SCREEN_RES[1]/TILE_SIZE)

    #SCREEN_WIDTH = 130
    #SCREEN_HEIGHT = 70


    PANEL1_HEIGHT = 17
    #sizes and coordinates relevant for the GUI
    PANEL2_WIDTH = 30
    PANEL2_XPOS = SCREEN_WIDTH - PANEL2_WIDTH
    PANEL2_HEIGHT = SCREEN_HEIGHT - PANEL1_HEIGHT
    PANEL2_TEXTX = 2
    PANEL2_YPOS = 0

    PANEL1_WIDTH = SCREEN_WIDTH - PANEL2_WIDTH
    PANEL1_YPOS = SCREEN_HEIGHT - PANEL1_HEIGHT
    PANEL1_XPOS = 0

    PANEL3_YPOS = PANEL1_YPOS
    PANEL3_XPOS = PANEL2_XPOS

    PANEL3_WIDTH = PANEL2_WIDTH
    PANEL3_HEIGHT = PANEL1_HEIGHT

    PANEL4_WIDTH = 28
    PANEL4_HEIGHT = 45
    PANEL4_XPOS = 0
    PANEL4_YPOS = SCREEN_HEIGHT - PANEL1_HEIGHT - PANEL4_HEIGHT

    #size of the map portion shown on-screen
    CAMERA_WIDTH = SCREEN_WIDTH - PANEL2_WIDTH
    CAMERA_HEIGHT = SCREEN_HEIGHT - PANEL1_HEIGHT

    MSG_X = 2
    MSG_WIDTH = PANEL1_WIDTH - 5
    MSG_HEIGHT = PANEL1_HEIGHT - 2

    font_path = os.path.join(os.getcwd(), 'fonts', 't12_test.png')
    #libtcod.console_set_custom_font('t10.png', libtcod.FONT_LAYOUT_ASCII_INROW|libtcod.FONT_TYPE_GREYSCALE)
    libtcod.console_set_custom_font(font_path, libtcod.FONT_LAYOUT_ASCII_INROW|libtcod.FONT_TYPE_GREYSCALE, 16, 20)
    #libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Iron Testament v0.5', False, renderer=libtcod.RENDERER_SDL)
    #libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Iron Testament v0.5', False, renderer=libtcod.RENDERER_OPENGL)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Iron Testament v0.5', True, renderer=libtcod.RENDERER_GLSL)
    libtcod.mouse_show_cursor(visible=1)
    libtcod.sys_set_fps(LIMIT_FPS)

    #interface = gui.PlayerInterface()
    interface = gui.interface

    root_con = gui.GuiPanel(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, xoff=0, yoff=0, interface=interface, is_root=1, name='Root')
    #libtcod.console_set_fullscreen(True)

    render_handler = RenderHandler()

    map_con = gui.GuiPanel(width=CAMERA_WIDTH, height=CAMERA_HEIGHT, xoff=0, yoff=0, interface=interface, name='MapCon')

    ## 2 other GUI panels ##
    panel1 = gui.GuiPanel(width=PANEL1_WIDTH, height=PANEL1_HEIGHT, xoff=PANEL1_XPOS, yoff=PANEL1_YPOS, interface=interface, name='Panel1')

    panel2 = gui.GuiPanel(width=PANEL2_WIDTH, height=PANEL2_HEIGHT, xoff=PANEL2_XPOS, yoff=PANEL2_YPOS, interface=interface, name='Panel2')

    panel3 = gui.GuiPanel(width=PANEL3_WIDTH, height=PANEL3_HEIGHT, xoff=PANEL3_XPOS, yoff=PANEL3_YPOS, interface=interface, name='Panel3')

    panel4 = gui.GuiPanel(width=PANEL4_WIDTH, height=PANEL4_HEIGHT, xoff=PANEL4_XPOS, yoff=PANEL4_YPOS, interface=interface, name='Panel4')
    panel4.render = False

    interface.gui_panels = [panel1, panel2, panel3, panel4]

    game = Game(interface)

    main_menu()
    #prof.run('main_menu()', 'itstats')
    #p = pstats.Stats('itstats')
    #p.sort_stats('cumulative').print_stats(10)
    #p.sort_stats('time').print_stats(10)

    libtcod.console_delete(None)
