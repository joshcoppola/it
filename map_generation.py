from __future__ import division
import random
from random import randint as roll
import libtcodpy as libtcod
import time

from helpers import *
from it import Profession
import config as g

##### City map generating stuff
MAX_BUILDING_SIZE = 15
INITIAL_BLDG_CHK = 3 # for initial check around building radius
INTIAL_BLDG_SIZE = 5
DEVELOPED_SURFACES = set(['road', 'wall', 'floor', 'water'])


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
    def __init__(self, usemap, city_class, figures):
        self.city_class = city_class
        self.usemap = usemap
        self.figures = figures

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
        g.game.render_handler.progressbar_screen(pbarname, 'creating main avenues', 1, steps)
        #### Generate the city!
        self.make_main_avenues(center=(int(round(self.usemap.width / 2)), int(round(self.usemap.height / 2))),
                               block_size=min_dist, disorg=disorg)
        #self.all_nodes = self.main_aves

        # Add a smattering of nodes
        g.game.render_handler.progressbar_screen(pbarname, 'adding nodes', 2, steps)
        self.add_initial_nodes(num_nodes, min_dist)
        # Connect them
        g.game.render_handler.progressbar_screen(pbarname, 'connecting nodes', 3, steps)
        self.connect_initial_nodes(num_neighbors=3)

        #  Set outside
        g.game.render_handler.progressbar_screen(pbarname, 'setting outer limits', 4, steps)

        ############################################
        border_cells = set(['road', 'municipal', 'wilderness'])
        def do_fill(tile):
            tile.zone = 'wilderness'

        begin = time.time()
        outside_tiles = floodfill(fmap=self.usemap, x=1, y=1, do_fill=do_fill, do_fill_args=[], is_border=lambda tile: tile.zone in border_cells)
        #game.add_message('Floodfill done in %f' % (time.time()-begin), libtcod.orange)
        #############################################


        ## List of lists, each sublist contains floodfilled tiles that form city "blocks"
        development_options = []

        border_zones = set(['wilderness', 'road', 'residential', 'industrial', 'market', 'municipal', 'undeveloped'])

        g.game.render_handler.progressbar_screen(pbarname, 'finding initial lots', 5, steps)
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

        g.game.render_handler.progressbar_screen(pbarname, 'zoning and filling lots', 6, steps)
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

        g.game.render_handler.progressbar_screen(pbarname, 'historizing houses', 7, steps)
        self.historize_houses()
        g.game.render_handler.progressbar_screen(pbarname, 'historizing buildings', 8, steps)
        self.historize_buildings()
        g.game.render_handler.progressbar_screen(pbarname, 'placing figures', 9, steps)
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
                    if self.usemap.is_val_xy(coords=(tx, ty)) and self.usemap.tiles[tx][ty].surface == 'wall':
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

        unplaced_homeseekers = 0
        for good_producer in self.city_class.econ.good_producers:
            if len(self.industries) and len(self.houses):
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

            # TODO - find out why there aren't enough houses in the city
            else:
                unplaced_homeseekers += 1

        print '{0} unplaced figures looking for either home or work'.format(unplaced_homeseekers)

        taverns = [building for building in self.city_class.buildings if building.b_type == 'Tavern']
        #for figure in self.city_class.figures:
        for entity in self.figures:
            if entity not in placed_figures:
                tavern = random.choice(taverns)
                tavern.place_within(obj=entity)

        ## Add some schmoes to recruit
        #for tavern in taverns:
        #    for i in xrange(2):
        #        schmoe = self.city_class.create_inhabitant(sex=1, born=time_cycle.current_year-roll(16, 35), char='o', dynasty=None, important=0, house=None)
        #        tavern.place_within(obj=schmoe)



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