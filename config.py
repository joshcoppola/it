

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

def init():
    global WORLD, player, M, game

    WORLD = None
    player = None
    M = None
    game = None
