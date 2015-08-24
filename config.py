from __future__ import division
import libtcodpy as libtcod


# Code to detect screen resolution (libtcod's doesn't work for some reason?)
try:
    from ctypes import windll
    user32 = windll.user32
    SCREEN_RES = ( user32.GetSystemMetrics(0), user32.GetSystemMetrics(1) )
except:
    print 'Cannot auto-size resolution, fall back to default...'
    SCREEN_RES = (1280, 720)


TILE_SIZE = 16
#actual size of the window
SCREEN_WIDTH = int(SCREEN_RES[0]/TILE_SIZE)
SCREEN_HEIGHT = int(SCREEN_RES[1]/TILE_SIZE)

#size of the WORLD
WORLD_WIDTH = 240
WORLD_HEIGHT = 220

#size of the battle map
MAP_WIDTH = 250
MAP_HEIGHT = 250
# Size for cities
CITY_MAP_WIDTH = 350
CITY_MAP_HEIGHT = 350

DIJMAP_CREATURE_DISTANCE = 10

WATER_HEIGHT = 100
MOUNTAIN_HEIGHT = 175

# Sites must be this far apart
MIN_SITE_DIST = 5

# There can be this much space between cities when starting an economy
MAX_ECONOMY_DISTANCE = 25
# Total number of economy agents which can work a tile at once
MAX_ECONOMY_AGENTS_PER_TILE = 6

# If distance from one city to another is below this amount, a new road will be built
NEW_ROAD_PATH_RATIO = .65

DEFAULT_TAX_AMOUNT = 50 # gold / turn of economy simulation

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = 1  #light walls or not
UNALERT_FOV_RADIUS = 30
ALERT_FOV_RADIUS = 60

LIMIT_FPS = 60


## colors ##
PANEL_BACK = libtcod.Color(18, 15, 15)
PANEL_FRONT = libtcod.Color(138, 115, 95)


PAIN_FRONT = libtcod.color_lerp(PANEL_FRONT, libtcod.red, .6)
PAIN_BACK = libtcod.color_lerp(libtcod.dark_red, libtcod.black, .6)


# When looping trough, these are the tree trunk characters for large (2x2) trees
TREE_CHARS = {0:(307, 308), 1:(311, 312), 2:(313, 314), 3:(309, 310) }
TREE_STUMP_CHARS = {0:315, 1:317, 2:318, 3:316 }


MIN_MARRIAGE_AGE = 16
MAX_MARRIAGE_AGE = 50
MIN_CHILDBEARING_AGE = 16
MAX_CHILDBEARING_AGE = 40


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


PROFESSION_INFAMY = {
    'King': 100,
    'Noble': 75,
    'General': 75,
    'High Priest': 75,
    'Tax Collector': 50,
    'Spymaster': 50,
    'Vizier': 75,
    'Militia Captain': 50,
    'Scribe': 20,

    'Adventurer': 5,
    'Tavern Keeper': 10,
    'Bard': 10,
    'Assassin': 0,
    'Bandit': 0,

    'Swordsman': 0,
    'Caravan Guard': 0,

    'merchant': 0
}

LITERATE_PROFESSIONS = {'Noble', 'noble', 'merchant', 'King', 'High Priest', 'Scribe', 'Tax Collector', 'Vizier', 'Tavern Keeper'}




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

CIV_COLORS = (
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
              libtcod.Color(113, 40, 113),

              libtcod.Color(66, 115, 61), libtcod.Color(36, 96, 36), libtcod.Color(189, 169, 18),
              libtcod.Color(128, 0, 0), libtcod.Color(142, 56, 142), libtcod.Color(113, 113, 198),
              libtcod.Color(56, 142, 142), libtcod.Color(113, 198, 113), libtcod.Color(198, 113, 113),
              libtcod.Color(238, 106, 80), libtcod.Color(48, 128, 20), libtcod.Color(0, 199, 140),
              libtcod.Color(125, 38, 205), libtcod.Color(132, 112, 255), libtcod.Color(61, 89, 171),
              libtcod.Color(148, 62, 15), libtcod.Color(205, 38, 38), libtcod.Color(255, 64, 64)
              )

DEBUG_MSG_COLOR = libtcod.dark_red




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


CONVERSATION_QUESTIONS= {
                            'greet':'Hello.',
                            'name':'What is your name?',
                            'profession':'What do you do?',
                            'sites':'What sites do you know about?',
                            'battles':'Have there been any battles lately?',
                            'events':'What\'s been going on?',
                            'age':'How old are you?,',
                            'city':'From where do you hail?',
                            'goals':'What are your current goals?',
                            'recruit':'Will you join me on my quest?',
                            'trade':'Do you have anything available to trade?'}



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
                     },

           'ocean':{
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

def init():
    global WORLD, player, M, game

    WORLD = None
    player = None
    M = None
    game = None




