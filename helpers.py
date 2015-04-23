from __future__ import division
import math
import libtcodpy as libtcod
import random
from random import randint as roll
from collections import Counter
from pattern.en import pluralize, NOUN

## For individual facing information
NEIGHBORS = ( (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1) )
COMPASS = ('north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest')

PLURAL_EXCEPTIONS = {'mine':'mines'}

# from http://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
int2ord = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def ct(word, num):
    ''' Return a string counting + pluralizing, if necessary, the word  '''
    return '{0} {1}'.format(num, pl(word, num))


def pl(word, num=2):
    ''' Pluralize word based on count '''
    if num != 1:
        if word not in PLURAL_EXCEPTIONS:
            word = pluralize(word, pos='NOUN')
        else:
            word = PLURAL_EXCEPTIONS[word]

    return word

def join_list(string_list, null_value="nothing"):
    if len(string_list) == 0:
        return null_value
    if len(string_list) == 1:
        return string_list[0]
    elif len(string_list) == 2:
        return ' and '.join(string_list)
    else:
        #return ', '.join([s for s in string_list]) + ', and ', string_list[-1]
        return '{0}, and {1}'.format(', '.join([s for s in string_list[:-1]]), string_list[-1])


def describe_map_contents(site_info):
    ''' Condenses a dict containing read information about sites into a readable paragraph '''
    msg = 'On the map, '
    if site_info['readable']['named']['known']:
        sites_by_type = Counter([s.type_ for s in site_info['readable']['named']['known']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There are {0} that you already know about: {1}. '.format(tmp, join_list([s.get_name() for s in site_info['readable']['named']['known']]))

    if site_info['readable']['named']['unknown']:
        sites_by_type = Counter([s.type_ for s in site_info['readable']['named']['unknown']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There are {0} that you did not know about: {1}. '.format(tmp, join_list([s.get_name() for s in site_info['readable']['named']['unknown']]))

    if site_info['readable']['unnamed']['known']:
        sites_by_type = Counter([s.type_ for s in site_info['readable']['unnamed']['known']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There are {0} that you already know about. '.format(tmp)

    if site_info['readable']['unnamed']['unknown']:
        sites_by_type = Counter([s.type_ for s in site_info['readable']['unnamed']['unknown']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There are {0} that you did not know about. '.format(tmp)



    if site_info['unreadable']['named']['known']:
        sites_by_type = Counter([s.type_ for s in site_info['unreadable']['named']['known']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'Although you can\'t read it, there are {0} that must be {1}. '.format(tmp, join_list([s.get_name() for s in site_info['unreadable']['named']['known']]))

    if site_info['unreadable']['named']['unknown']:
        sites_by_type = Counter([s.type_ for s in site_info['unreadable']['named']['unknown']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There are {0} that you cannot recognize. '.format(tmp)

    if site_info['unreadable']['unnamed']['known']:
        sites_by_type = Counter([s.type_ for s in site_info['unreadable']['unnamed']['known']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There appear to be {0} that you already know about. '.format(tmp)

    if site_info['unreadable']['unnamed']['unknown']:
        sites_by_type = Counter([s.type_ for s in site_info['unreadable']['unnamed']['unknown']])
        tmp = join_list([ct(type_, num) for type_, num in sites_by_type.iteritems()])
        msg += 'There appear to be {0} that you did not know about. '.format(tmp)

    return msg

def determine_commander(figures):
        ''' Find the figure with the greatest number of commanded beings and set as commander '''
        current_commander = None
        current_num_commanded_figs = -1 # Non-commanders have 0 commanded figs
        for entity in figures:
            commanded_figs = entity.creature.get_total_number_of_commanded_beings()
            if commanded_figs > current_num_commanded_figs:
                current_commander = entity
                current_num_commanded_figs = commanded_figs

        return current_commander

def centroid(data):
    x, y = zip(*data)
    l = len(x)
    return sum(x) / l, sum(y) / l


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


def get_border_tiles_8(x, y):
    return ( (x, y+1), (x+1, y), (x, y-1), (x-1, y), (x+1, y+1), (x+1, y-1), (x-1, y-1), (x-1, y+1)  )


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


def floodfill(fmap, x, y, do_fill, do_fill_args, is_border, max_tiles=-1):
    ''' Adapted from 1st comment http://stackoverflow.com/questions/11746766/flood-fill-algorithm-python '''
    to_fill = set([(x, y)])
    filled = set()

    # Keep iterating until it runs out of cells to fill, OR the number of filled cells is less than the max (if one is defined)
    while to_fill and (max_tiles < 0 or len(filled) < max_tiles):

        (xx, yy) = to_fill.pop()

        if fmap.is_val_xy((xx, yy)) and not is_border(fmap.tiles[xx][yy]):
            do_fill(fmap.tiles[xx][yy], *do_fill_args)
            filled.add((xx, yy))

            for nx, ny in ( (xx-1, yy), (xx+1, yy), (xx, yy-1), (xx, yy+1) ):
                to_fill.add((nx, ny))

    return filled

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