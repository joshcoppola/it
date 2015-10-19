from __future__ import division
import time
import random
from random import randint as roll
import time
from collections import defaultdict

import libtcodpy as libtcod
from dijkstra import Dijmap
from helpers import *
import config as g
import physics as phys
from map_base import Map
import it

import data_importer as data

##### City map generating stuff
MAX_BUILDING_SIZE = 18
INITIAL_BLDG_CHK = 3 # for initial check around building radius
INTIAL_BLDG_SIZE = 5
DEVELOPED_SURFACES = {'road', 'wall', 'floor', 'water'}


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

        self.shaded = 0 # Tracks whether a tree or other pbject has cast a shadow here
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
        if not self.shaded:
            self.shaded = 1
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


class Wmap(Map):
    def __init__(self, world, wx, wy, width, height):
        Map.__init__(self, width, height)
        # A walkable map, composed of an array of tiles
        self.world = world
        self.wx = wx
        self.wy = wy

        self.width = width
        self.height = height


        # List of all objects inhabiting this map
        self.objects = []
        self.creatures = []

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
        self.factions_on_map = defaultdict(set)
        for obj in self.creatures:
            self.factions_on_map[obj.creature.faction].add(obj)

        # Now add a dmap for each
        for faction, member_set in self.factions_on_map.iteritems():
            self.add_dmap(key=faction.name, target_nodes=[(obj.x, obj.y) for obj in member_set], dmrange=g.DIJMAP_CREATURE_DISTANCE)


            # Make sure all sapients know who their enemies are
            #for other_faction, other_member_set in self.factions_on_map.iteritems():
            #    if faction.is_hostile_to(other_faction):
            #        g.game.add_message('%s: setting enemy - %s'%(faction.faction_name, other_faction.faction_name), libtcod.color_lerp(faction.color, PANEL_FRONT, .5) )
            #        for obj in member_set:
            #            obj.sapient.add_enemy_faction(other_faction)

            #for enemy_faction in faction.enemy_factions:
            #    if enemy_faction in self.factions_on_map:
            #        g.game.add_message('%s: setting enemy - %s'%(faction.faction_name, enemy_faction.faction_name), libtcod.color_lerp(faction.color, PANEL_FRONT, .5) )
            #        for obj in member_set:
            #            obj.sapient.add_enemy_faction(enemy_faction)

        for figure in self.creatures:
            if figure.local_brain:
                figure.local_brain.set_enemy_perceptions_from_cached_factions()

        return self.factions_on_map


    def update_dmaps(self):
        #jobs = []
        #def stupid_function(target_nodes):
        #    self.dijmaps[faction.faction_name].update_map(target_nodes)

        for faction, member_set in self.factions_on_map.iteritems():
            target_nodes = [(obj.x, obj.y) for obj in member_set if obj.creature.status == 'alive' and (obj == g.player or (obj != g.player and obj.local_brain.ai_state != 'idle'))]
            self.dijmaps[faction.name].update_map(target_nodes=target_nodes)
            #update_map_test(self.dijmaps[faction.faction_name], target_nodes)

            #j = multiprocessing.Process(target=self.dijmaps[faction.faction_name].update_map, args=(target_nodes))
            #j = multiprocessing.Process(target=self.dijmaps[faction.faction_name].update_map, args=(target_nodes))
            #j = multiprocessing.Process(target=g.game.add_message, args=(faction.faction_name,))
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

        #g.game.add_message('Dmap for %s created in %.2f seconds' %(key, end), libtcod.cyan)


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


    def create_heightmap_from_surrounding_tiles(self, minh=-8, maxh=8, iterations=50):
        '''  Have the world heights influence the heights on the local map '''

        ht = int(self.height/2)
        wd = int(self.width/2)

        surrounding_heights = self.world.get_surrounding_heights(coords=(self.wx, self.wy))
        this_tile_height = min(surrounding_heights[4], g.MOUNTAIN_HEIGHT-10)

        # Which map tiles to use from surrounding_heights variable
        surrounding_heights_to_map = (
                                      (0, 0),             (wd, 0),             (self.width-1, 0),
                                      (0, ht),            (wd, ht),            (self.width-1, ht),
                                      (0, self.height-1), (wd, self.height-1), (self.width-1, self.height-1)
                                      )

        surrounding_rivers = self.world.get_surrounding_rivers(coords=(self.wx, self.wy))

        # Which map tiles to use from the river_dirs variable
        world_to_wmap_rivers =  {
                                (1, 0):(self.width-1, int(self.height/2.5)),
                                (-1, 0):(0, int(self.height/2.5)),
                                (0, 1):(int(self.width/2.5), self.height-1),
                                (0, -1):(int(self.width/2.5), 0)
                                }


        ## Create the actual heightmap
        hm = self.create_and_vary_heightmap(initial_height=this_tile_height, mborder=int(self.width/10),
                                            minr=int(self.width/12.5), maxr=int(self.width/3), minh=minh, maxh=maxh, iterations=iterations)


        corner_tile_indices = {0, 2, 6, 8}
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
            #g.game.add_message('height is %i'%libtcod.heightmap_get_value(hm, r1x, r1y), libtcod.red)
        ######################################################################

        return hm

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
            if libtcod.heightmap_get_value(hm=hm, x=x, y=y) < (g.MOUNTAIN_HEIGHT - height - 1):
                libtcod.heightmap_add_hill(hm=hm, x=x, y=y, radius=radius, height=height)

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
                if tile.height < g.WATER_HEIGHT:
                    tile.make_water()

                # Add the tile to the row
                row.append(tile)

            # Finally, add the row to the map
            self.tiles.append(row)

        self.setup_chunks(chunk_size=10, map_type='human')


    def add_minor_sites_to_map(self):
        for site in self.world.tiles[self.wx][self.wy].minor_sites:
            for building in site.buildings:
                if not building.physical_property:
                    building.add_building_to_map(*building.add_building_to_map_args)


    def is_val_xy(self, coords):
        return (0 < coords[0] < self.width) and (0 < coords[1] < self.height)

    def make_city_map(self, city_class, num_nodes, min_dist, disorg):
        #Make a city on this tile
        self.cit = CityMap(self, city_class, self.world.tiles[city_class.x][city_class.y].entities)
        self.cit.generate_city_map(num_nodes=num_nodes, min_dist=min_dist, disorg=disorg)


    def make_door(self, x, y, floor_type):
        self.tiles[x][y].make_floor(floor_type=floor_type)
        self.create_and_add_object(name='door', x=x, y=y)


    def create_and_add_object(self, name, x, y, creature=None, local_brain=None, world_brain=None, force_material=None):
        # Add an object to a tile
        obj = it.assemble_object(object_blueprint=phys.object_dict[name], force_material=force_material, wx=self.wx, wy=self.wy, creature=creature, local_brain=local_brain, world_brain=world_brain)

        # Check to see if the obj blocks movement
        if not obj.creature and (obj.blocks_mov or obj.blocks_vis):
            self.tiles[x][y].blocks_mov = obj.blocks_mov
            self.tiles[x][y].blocks_vis = obj.blocks_vis

        self.add_object_to_map(x=x, y=y, obj=obj)

        return obj

    def add_object_to_map(self, x, y, obj):
        ''' For adding an existing object to the map '''

        # Make sure to remove it from another spot on the map if need be
        if obj.x and obj.y and obj in self.tiles[obj.x][obj.y].objects:
            self.tiles[obj.x][obj.y].objects.remove(obj)
            # Remove it from the owning map chunk if need be
            if obj in self.tiles[obj.x][obj.y].chunk.objects:
                self.tiles[obj.x][obj.y].chunk.objects.remove(obj)

        # Add it to the new spot on the map
        self.tiles[x][y].objects.append(obj)
        self.tiles[x][y].chunk.objects.append(obj)


        ## If it's a creature and it's not already in the map's list of creatures
        if obj.creature and not obj in self.creatures:
            self.creatures.append(obj)
            obj.creature.next_tick = self.world.time_cycle.current_tick + 1
        ## DEBUG - If not, log it
        elif obj in self.creatures:
            print 'Creature duplication -- {0} was already in map.creatures'.format(obj.fulltitle())

        ## If it's not a creature and it's not already in the map's list of objects
        if not obj.creature and obj not in self.objects:
            self.objects.append(obj)
        ## DEBUG - log the object duplication
        elif not obj.creature and obj in self.objects:
            print 'Object duplication -- {0} was already in map.objects'.format(obj.fulltitle())

        obj.x = x
        obj.y = y

        if obj.local_brain:
            obj.local_brain.ai_initialize()


    def add_sapients_to_map(self, entities, populations, place_anywhere=0):
        hht = int(self.height/2)
        hwd = int(self.width/2)
        # Size of rectangle
        rs = int(self.width/10)

        world_last_dir_to_rect = {(-1, -1):Rect(x=1, y=1, w=rs, h=rs),           (0, -1):Rect(x=hwd, y=1, w=rs, h=rs),                 (1, -1):Rect(x=self.width-(rs+2), y=1, w=rs, h=rs),
                            (-1, 0):Rect(x=1, y=hht, w=rs, h=rs),                (0, 0):Rect(x=hwd, y=hht, w=rs*3, h=rs*3),            (1, 0):Rect(x=self.width-(rs+2), y=hht, w=rs, h=rs),
                            (-1, 1):Rect(x=1, y=self.height-(rs+2), w=rs, h=rs), (0, 1):Rect(x=hwd, y=self.height-(rs+2), w=rs, h=rs), (1, 1):Rect(x=self.width-(rs+2), y=self.height-(rs+2), w=rs, h=rs)
                            }

        site = self.world.tiles[self.wx][self.wy].site

        ###### Standard placement - in the wilderness somewhere ######
        if site is None:
            for entity in entities:
                figure_start = world_last_dir_to_rect[entity.world_last_dir]
                # Find a non-blocked tile
                while 1:
                    x = roll(figure_start.x1, figure_start.x2)
                    y = roll(figure_start.y1, figure_start.y2)
                    # place_anywhere is set to true when battle takes place in the world scale, so that entire large maps do not need to be generated
                    # This means in tiny-sized maps, many creatures may be "on top" of each other.
                    if (g.M.is_val_xy(coords=(x, y)) and not g.M.tile_blocks_mov(x, y)) or place_anywhere:
                        break
                # Add the entity to the map
                g.M.add_object_to_map(x=x, y=y, obj=entity)

            for population in populations:
                population_start = world_last_dir_to_rect[population.world_last_dir]
                population.add_to_map(startrect=population_start, startbuilding=None, patrol_locations=[], place_anywhere=place_anywhere)

            for site in self.world.tiles[self.wx][self.wy].all_sites:
                for building in site.buildings:
                    building.add_housed_objects_to_map()

        ###### Site placement - try to place people inside buildings ######
        elif site:
            for entity in entities:

                if entity.creature.profession and entity.creature.profession.current_work_building and entity.creature.profession.current_work_building.site == site:
                    entity.creature.profession.current_work_building.place_within(entity)

                elif entity.creature.current_citizenship == site and entity.creature.house:
                    # Give it physical property if it doesn't have it
                    #if not entity.creature.house.physical_property:
                    #    entity.creature.house.add_physical_property_rect(physical_property_rect=home_tiles)
                    entity.creature.house.place_within(entity)

                elif entity.creature.current_citizenship == site and site.houses:
                    print '{0} has no house but lives in {1}'.format(entity.fulltitle(), site.name )

                else:
                    taverns = site.get_building_type('Tavern')
                    tavern = random.choice(taverns)
                    tavern.place_within(entity)
                    g.game.add_message('placing {0} in tavern at {1}, {2}'.format(entity.fulltitle(), entity.x, entity.y))

            for building in site.buildings:
                building.add_housed_objects_to_map()

        # placed_figures = []
        #
        # for building in self.city_class.buildings:
        #     for employee in building.current_workers:
        #         building.place_within(obj=employee)
        #         placed_figures.append(employee)
        #
        #     ''' Why doesn't this always work?
        #     if building.b_type == 'Tavern':
        #         for i in xrange(roll(1, 3)):
        #             human = self.city_class.create_inhabitant(sex=1, born=time_cycle.current_year-roll(16, 35), char='o', dynasty=None, important=0, house=None)
        #             building.place_within(obj=human)
        #     '''
        #
        #     for member in building.inhabitants:
        #         if member not in placed_figures:
        #             building.place_within(obj=member)
        #             placed_figures.append(member)
        #
        #     # Ug
        #     building.add_housed_objects_to_map()
        #
        # ### Adding agents from the economy to the city
        # profession_to_business = {'Blacksmith':'Foundry', 'Potter':'Kiln', 'Carpenter':'Carpenter Workshop', 'Clothier':'Clothier Workshop'}
        #
        # unplaced_homeseekers = 0
        # for good_producer in self.city_class.econ.good_producers:
        #     if len(self.industries) and len(self.houses):
        #         work_tiles = random.choice(self.industries)
        #         home_tiles = random.choice(self.houses)
        #
        #         self.industries.remove(work_tiles)
        #         self.houses.remove(home_tiles)
        #
        #         ## Choose a title for the business
        #         professions = [it.Profession(name=good_producer.name, category='commoner')]
        #         ptype = good_producer.name.split(' ')[1]
        #         new_building = self.city_class.create_building(zone='commercial', type_=profession_to_business[ptype],
        #                                 template='TEST', professions=professions, inhabitants=[], tax_status='commoner')
        #
        #
        #         ## Fill positions
        #         new_building.fill_initial_positions()
        #         # The first employee listed is the actual economy agent
        #         new_building.current_workers[0].creature.economy_agent = good_producer
        #
        #
        #         for x in xrange(work_tiles.x1, work_tiles.x2 + 1):
        #             for y in xrange(work_tiles.y1, work_tiles.y2 + 1):
        #                 new_building.physical_property.append((x, y))
        #                 self.usemap.tiles[x][y].building = new_building
        #
        #         for employee in new_building.current_workers:
        #             new_building.place_within(obj=employee)
        #             placed_figures.append(employee)
        #
        #         #### WILL ONLY CREATE HOUSE FOR FIRST EMPLOYEE
        #         # And will not place employee in house
        #         household = self.city_class.create_building(zone='residential', type_='house', template='TEST', professions=[], inhabitants=[new_building.current_workers[0]], tax_status='commoner')
        #
        #         for x in xrange(home_tiles.x1, home_tiles.x2 + 1):
        #             for y in xrange(home_tiles.y1, home_tiles.y2 + 1):
        #                 household.physical_property.append((x, y))
        #                 self.usemap.tiles[x][y].building = household
        #
        #     # TODO - find out why there aren't enough houses in the city
        #     else:
        #         unplaced_homeseekers += 1
        #
        # print '{0} unplaced figures looking for either home or work'.format(unplaced_homeseekers)
        #
        # taverns = [building for building in self.city_class.buildings if building.type_ == 'Tavern']
        # #for figure in self.city_class.figures:
        # for entity in self.figures:
        #     if entity not in placed_figures:
        #         tavern = random.choice(taverns)
        #         tavern.place_within(obj=entity)


        ## DIJMAPS
        factions_on_map = self.cache_factions_for_dmap()

        for obj in self.creatures:
            obj.creature.set_initial_desires(factions_on_map)

        if g.game.map_scale == 'human':
            g.game.add_message('%i objs; %i saps' %(len(self.objects), len(self.creatures)) )
            for s in self.creatures:
                g.game.add_message('{0}: {1}, {2}'.format(s.fulltitle(), s.x, s.y))
            #     self.tiles[s.x][s.y].set_color(libtcod.darker_red)

        self.initialize_fov()


    def clear_objects(self):
        for sap in self.creatures:
            sap.x = None
            sap.y = None

        self.objects = []
        self.creatures = []

    def initialize_fov(self):
        #create the FOV map, according to the generated map
        for y in xrange(self.width):
            for x in xrange(self.height):
                libtcod.map_set_properties(self.fov_map, x, y, not self.tiles[x][y].blocks_vis, not self.tiles[x][y].blocks_mov)

        for obj in self.objects + self.creatures:
            libtcod.map_set_properties(self.fov_map, obj.x, obj.y, not obj.blocks_vis, not obj.blocks_mov)
        self.path_map = libtcod.path_new_using_map(self.fov_map)

        g.game.interface.map_console.clear() # unexplored areas start black (which is the default background color)


    def display(self, debug_active_unit_dijmap):
        #recompute FOV if needed (the g.player moved or something)
        self.fov_recompute = False
        libtcod.map_compute_fov(self.fov_map, g.player.x, g.player.y, g.player.creature.alert_sight_radius, g.FOV_LIGHT_WALLS, g.FOV_ALGO)
        g.game.interface.map_console.clear()

        # NORMAL RENDERING
        if not debug_active_unit_dijmap:
            #go through all tiles, and set their background color according to the FOV
            for cam_y in xrange(g.game.camera.height):
                for cam_x in xrange(g.game.camera.width):
                    (x, y) = g.game.camera.cam2map(cam_x, cam_y)
                    if self.is_val_xy((x, y)):
                        visible = libtcod.map_is_in_fov(self.fov_map, x, y)

                        if visible:
                            #libtcod.console_set_char_background(con.con, x, y, g.M.tiles[map_x][map_y].color, libtcod.BKGND_SET)
                            libtcod.console_put_char_ex(g.game.interface.map_console.con, cam_x, cam_y, self.tiles[x][y].char, self.tiles[x][y].char_color, self.tiles[x][y].color)
                            #since it's visible, explore it
                            self.tiles[x][y].explored = True

                        elif self.tiles[x][y].explored:
                            #if it's not visible right now, the g.player can only see it if it's explored
                            #libtcod.console_set_char_background(con.con, x, y, g.M.tiles[map_x][map_y].color * .5, libtcod.BKGND_SET)
                            libtcod.console_put_char_ex(g.game.interface.map_console.con, cam_x, cam_y, self.tiles[x][y].char, self.tiles[x][y].shadow_char_color, self.tiles[x][y].shadow_color)


        ## UNOPTIMIZED DIJMAP RENDERING
        elif debug_active_unit_dijmap:
            for cam_y in xrange(g.game.camera.height):
                for cam_x in xrange(g.game.camera.width):
                    #(map_x, map_y) = (g.game.camera.x + x, g.game.camera.y + y)
                    (x, y) = g.game.camera.cam2map(cam_x, cam_y)
                    if self.is_val_xy((x, y)):
                        if not self.tiles[x][y].blocks_mov:
                            intensity = 0
                            # Sum all desires for this square, weighted by intensity
                            for desire, value in g.game.render_handler.debug_active_unit_dijmap.creature.dijmap_desires.iteritems():
                                if g.M.dijmaps[desire].dmap[x][y] is not None:
                                    intensity += int(round(value)) * self.dijmaps[desire].dmap[x][y]

                            libtcod.console_set_char_background(g.game.interface.map_console.con, cam_x, cam_y, libtcod.Color((255 - intensity), (255 - intensity), (255 - intensity)), libtcod.BKGND_SET)
                            #libtcod.console_set_char_background(con.con, x, y, libtcod.Color((255 - intensity), (255 - intensity), (255 - intensity)), libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(g.game.interface.map_console.con, cam_x, cam_y, libtcod.darkest_red, libtcod.BKGND_SET)
        #########################################


        #draw all objects in the list, except the g.player.
        for obj in self.objects:
            if self.tiles[obj.x][obj.y].explored:
                obj.draw()

        for creature in self.creatures:
            if self.tiles[creature.x][creature.y].explored:
                creature.draw()

        for sapient in self.creatures:
            if self.tiles[sapient.x][sapient.y].explored and sapient != g.player:
                sapient.draw()
        g.player.draw()

        #blit the contents of map_con to the root console
        g.game.interface.map_console.blit()

    def shade_tree(self, x, y, height, radius):
        ## Experimental shadow code

        #in_circle_shading = (.12, .15, .16, .17, .18, .19, .2, .21)
        #edge_circle_shading = (.11, .12, .12, .13, .14, .15, .16, .17)

        in_circle_shading = (.17, )
        edge_circle_shading = (.12, .13, .13, .14)

        sx, sy = x, y

        for i in xrange(height):
            sx += 1
            #if self.is_val_xy((sx, sy)):
            #    self.tiles[sx][sy].set_shadow(amount=.3)

        for xx in xrange(sx-radius, sx+radius+1):
            for yy in xrange(sy-radius, sy+radius+1):
                if in_circle(center_x=sx, center_y=sy, radius=radius, x=xx, y=yy) and self.is_val_xy((xx, yy)):
                    amount = random.choice(in_circle_shading)
                    self.tiles[xx][yy].set_shadow(amount=amount)
                elif in_circle(center_x=sx, center_y=sy, radius=radius+1, x=xx, y=yy) and self.is_val_xy((xx, yy)) and roll(0, 1):
                    amount = random.choice(edge_circle_shading)
                    self.tiles[xx][yy].set_shadow(amount=amount)


    def make_small_tree(self, x, y):
        ''' Make a small tree xtrunk '''
        self.tiles[x][y].surface = 'Tree trunk'
        self.tiles[x][y].blocks_mov = 1
        #self.tiles[x][y].blocks_vis = 1

        #self.tiles[x][y].set_color(libtcod.darkest_sepia)
        self.tiles[x][y].char = random.choice((288, 289))
        self.tiles[x][y].set_char_color(libtcod.darkest_sepia)

        self.shade_tree(x=x, y=y, height=roll(0, 3), radius=roll(5, 10))


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
            self.tiles[xx][yy].char = random.choice(g.TREE_CHARS[i])
            self.tiles[xx][yy].set_char_color(libtcod.darkest_sepia)
            self.tiles[xx][yy].surface = 'Tree trunk'
            self.tiles[xx][yy].blocks_mov = 1
            #self.tiles[xx][yy].blocks_vis = 1

        self.shade_tree(x=x, y=y, height=roll(3, 6), radius=roll(9, 20))

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
            self.tiles[xx][yy].char = g.TREE_STUMP_CHARS[i]
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

        g.game.add_message('Vegetation: %.2f' %(time.time() - begin))


    def add_world_features(self, x, y):
        ''' Adds in roads, rivers, caves, etc ... '''
        begin = time.time()


        world_2_wmap_roads= {(1, 0):(self.width-1, int(self.height/2)),
                          (-1, 0):(0, int(self.height/2)),
                          (0, 1):(int(self.width/2), self.height-1),
                          (0, -1):(int(self.width/2), 0)
                          }


        if self.world.tiles[x][y].has_feature('road'):
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
        for cave in self.world.tiles[x][y].caves:
            ## find some tiles that border rock for each cave
            borders_rock = False
            while not borders_rock:
                cx, cy = roll(20, self.width-21), roll(20, self.height-21)
                if not self.tile_blocks_mov(x=cx, y=cy):
                    for nx, ny in get_border_tiles(x=cx, y=cy):
                        if g.M.tile_blocks_mov(x=nx, y=ny):
                            borders_rock = True
                            break
            #cx, cy = random.choice(self.rock_border_cells)
            self.tiles[cx][cy].char = 'O'
            self.tiles[cx][cy].interactable = {'func':self.world.make_cave_map, 'args':[x, y, cave], 'text':'Enter cave', 'hover_text':['Cave entrance']}

            g.game.add_message(new_msg='cave at %i, %i' %(cx, cy), color=libtcod.green)

        g.game.add_message('World features: %.2f' %(time.time() - begin))


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
                    if self.tiles[x][y].height > g.WATER_HEIGHT and (roll(1, 1000) <= cfg['initial_blocks_mov_chance'] or self.tiles[x][y].height > cfg['blocks_mov_height']) \
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

        g.game.add_message('Seed cell automata: %.2f' %(time.time() - begin))
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

        g.game.add_message('Iterate cell automata: %.2f' %(time.time() - begin))


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

            g.game.add_message('Color blocks_mov cells: %.2f' %(time.time() - begin))

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

                    if recently_filled:
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
        # self.place_figures()


    def make_market(self, empty_lot, zone):
        # Special case - make a market
        lot = list(empty_lot)
        self.markets.append(lot)

        for x, y in lot:
            if self.usemap.tiles[x][y].surface not in DEVELOPED_SURFACES:
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
                    if self.usemap.tiles[i][j].surface in DEVELOPED_SURFACES or not self.usemap.is_val_xy((i, j)):
                        usable = False
                        undeveloped_spaces.remove((x, y))
                        break

                if usable == False:
                    break
                    #### Create a rect and expand it in different directions
            if usable:
                newrect = Rect(x - 1, y - 1, INTIAL_BLDG_SIZE -1, INTIAL_BLDG_SIZE - 1)

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

        for x, y in empty_lot:
            if self.usemap.tiles[x][y].surface not in DEVELOPED_SURFACES:
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



    # def place_figures(self):
    #     ## Place historical figures on the map
    #
    #     # A list of figures who have been placed so far
    #     placed_figures = []
    #
    #     for building in self.city_class.buildings:
    #         for employee in building.current_workers:
    #             building.place_within(obj=employee)
    #             placed_figures.append(employee)
    #
    #         ''' Why doesn't this always work?
    #         if building.b_type == 'Tavern':
    #             for i in xrange(roll(1, 3)):
    #                 human = self.city_class.create_inhabitant(sex=1, born=time_cycle.current_year-roll(16, 35), char='o', dynasty=None, important=0, house=None)
    #                 building.place_within(obj=human)
    #         '''
    #
    #         for member in building.inhabitants:
    #             if member not in placed_figures:
    #                 building.place_within(obj=member)
    #                 placed_figures.append(member)
    #
    #         # Ug
    #         building.add_housed_objects_to_map()
    #
    #     ### Adding agents from the economy to the city
    #     profession_to_business = {'Blacksmith':'Foundry', 'Potter':'Kiln', 'Carpenter':'Carpenter Workshop', 'Clothier':'Clothier Workshop'}
    #
    #     unplaced_homeseekers = 0
    #     for good_producer in self.city_class.econ.good_producers:
    #         if len(self.industries) and len(self.houses):
    #             work_tiles = random.choice(self.industries)
    #             home_tiles = random.choice(self.houses)
    #
    #             self.industries.remove(work_tiles)
    #             self.houses.remove(home_tiles)
    #
    #             ## Choose a title for the business
    #             professions = [it.Profession(name=good_producer.name, category='commoner')]
    #             ptype = good_producer.name.split(' ')[1]
    #             new_building = self.city_class.create_building(zone='commercial', type_=profession_to_business[ptype],
    #                                     template='TEST', professions=professions, inhabitants=[], tax_status='commoner')
    # 
    #
    #             ## Fill positions
    #             new_building.fill_initial_positions()
    #             # The first employee listed is the actual economy agent
    #             new_building.current_workers[0].creature.economy_agent = good_producer
    #
    #             new_building.add_physical_property_rect(physical_property_rect=work_tiles)
    #
    #             for employee in new_building.current_workers:
    #                 new_building.place_within(obj=employee)
    #                 placed_figures.append(employee)
    #
    #             #### WILL ONLY CREATE HOUSE FOR FIRST EMPLOYEE
    #             # And will not place employee in house
    #             household = self.city_class.create_building(zone='residential', type_='house', template='TEST', professions=[], inhabitants=[new_building.current_workers[0]], tax_status='commoner')
    #
    #             household.add_physical_property_rect(physical_property_rect=home_tiles)
    #
    #         # TODO - find out why there aren't enough houses in the city
    #         else:
    #             unplaced_homeseekers += 1
    #
    #     print '{0} unplaced figures looking for either home or work'.format(unplaced_homeseekers)
    #
    #     taverns = [building for building in self.city_class.buildings if building.type_ == 'Tavern']
    #     #for figure in self.city_class.figures:
    #     for entity in self.figures:
    #         if entity not in placed_figures:
    #             tavern = random.choice(taverns)
    #             tavern.place_within(obj=entity)

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
            if building.type_ == 'house':
                big_house = False
                for figure in building.inhabitants:
                    if figure.creature.profession and figure.creature.profession.category in big_house_categories:
                        big_house = True
                        break

                if big_house and len(self.noble_houses):
                    b_rect = random.choice(self.noble_houses)
                    self.noble_houses.remove(b_rect)
                else:
                    b_rect = random.choice(self.houses)
                    self.houses.remove(b_rect)

                building.add_physical_property_rect(physical_property_rect=b_rect)


    def historize_buildings(self):
        ## Add in historical figures from the city info to the city
        market = self.city_class.get_building('Market')
        for x, y in self.markets[0]:
            self.usemap.tiles[x][y].building = market
        market.physical_property = self.markets[0]

        min_industry_size = 5
        ## Loop through the list of historical buildings
        for i, building in enumerate(self.city_class.buildings):
            if building.type_ != 'house' and not building.physical_property:
                # Adding a quick hack to make sure buildings, especially taverns, get a reasonable minimum size
                potential_buildings = [plot for plot in self.industries if plot.get_dimensions()[0] > min_industry_size and plot.get_dimensions()[1] > min_industry_size]

                if potential_buildings:
                    phys_building = random.choice(potential_buildings)
                    self.industries.remove(phys_building)
                    building.add_physical_property_rect(physical_property_rect=phys_building)
                    #print 'adding {0}'.format(building.type_)

                    # If the building is linked to an economy agent but doesn't has a generated figure, it does so
                    if building.linked_economy_agent:
                        if building.linked_economy_agent.attached_to is None:
                            profession = it.Profession(name=building.linked_economy_agent.name, category='commoner')
                            building.add_profession(profession=profession)

                            # Create the entity
                            born = g.WORLD.time_cycle.years_ago(roll(18, 40))
                            entity = building.site.create_inhabitant(sex=1, born=born, char='o', dynasty=None, important=0, house=None)

                            # Set profession of figure and link to economy agent
                            profession.give_profession_to(figure=entity)
                            building.linked_economy_agent.update_holder(figure=entity)

                        # Additionally, add the building's inventory as objects
                        amount = building.linked_economy_agent.sell_inventory[building.linked_economy_agent.sold_commodity_name]

                        # Placeholder way to show agent's inventory on the map
                        if amount:
                            sold_commodity_name = building.linked_economy_agent.sold_commodity_name
                            material = data.commodity_manager.get_material_from_commodity_name(commodity_name=sold_commodity_name)
                            obj = it.assemble_object(object_blueprint=phys.object_dict['crate'], force_material=material, wx=self.usemap.wx, wy=self.usemap.wy)
                            obj.name = 'Stack of {0} {1}'.format(amount, sold_commodity_name)
                            obj.description = 'This is a stack of {0} {1}'.format(amount, sold_commodity_name)

                            building.place_within(obj)

                            # Place some dummy example objects for now
                            for n_obj in building.linked_economy_agent.get_sold_objects():
                                n_obj = it.assemble_object(object_blueprint=phys.object_dict[n_obj], force_material=material, wx=self.usemap.wx, wy=self.usemap.wy)
                                building.place_within(n_obj)


                else:
                    print 'Not enough buildings matching criteria'
                    break

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