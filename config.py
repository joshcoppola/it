from __future__ import division
import libtcodpy as libtcod


DIJMAP_CREATURE_DISTANCE = 10

WATER_HEIGHT = 100
MOUNTAIN_HEIGHT = 190


FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = 1  #light walls or not
UNALERT_FOV_RADIUS = 30
ALERT_FOV_RADIUS = 60


# When looping trough, these are the tree trunk characters for large (2x2) trees
TREE_CHARS = {0:(307, 308), 1:(311, 312), 2:(313, 314), 3:(309, 310) }
TREE_STUMP_CHARS = {0:315, 1:317, 2:318, 3:316 }



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


def init():
    global WORLD, player, M, game

    WORLD = None
    player = None
    M = None
    game = None




