from __future__ import division
import time
import random
from random import randint as roll


import libtcodpy as libtcod
from dijkstra import Dijmap
from helpers import *
import config as g
import physics as phys
import map_generation as mgen
import it



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
            if obj.creature.faction in self.factions_on_map.keys():
                self.factions_on_map[obj.creature.faction].add(obj)
            else:
                self.factions_on_map[obj.creature.faction] = set([obj])

        # Now add a dmap for each
        for faction, member_set in self.factions_on_map.iteritems():
            self.add_dmap(key=faction.faction_name, target_nodes=[(obj.x, obj.y) for obj in member_set], dmrange=g.DIJMAP_CREATURE_DISTANCE)


            # Make sure all sapients know who their enemies are
            #for other_faction, other_member_set in self.factions_on_map.iteritems():
            #    if faction.is_hostile_to(other_faction):
            #        g.game.add_message('%s: setting enemy - %s'%(faction.faction_name, other_faction.faction_name), libtcod.color_lerp(faction.color, PANEL_FRONT, .5) )
            #        for obj in member_set:
            #            obj.sapient.add_enemy_faction(other_faction)

            #for enemy_faction in faction.enemy_factions:
            #    if enemy_faction in self.factions_on_map.keys():
            #        g.game.add_message('%s: setting enemy - %s'%(faction.faction_name, enemy_faction.faction_name), libtcod.color_lerp(faction.color, PANEL_FRONT, .5) )
            #        for obj in member_set:
            #            obj.sapient.add_enemy_faction(enemy_faction)

        for figure in self.sapients:
            if figure.local_brain:
                figure.local_brain.set_enemy_perceptions_from_cached_factions()

        return self.factions_on_map


    def update_dmaps(self):
        #jobs = []
        #def stupid_function(target_nodes):
        #    self.dijmaps[faction.faction_name].update_map(target_nodes)

        for faction, member_set in self.factions_on_map.iteritems():
            target_nodes = [(obj.x, obj.y) for obj in member_set if obj.creature.status == 'alive' and (obj == g.player or (obj != g.player and obj.local_brain.ai_state != 'idle'))]
            self.dijmaps[faction.faction_name].update_map(target_nodes=target_nodes)
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
            if libtcod.heightmap_get_value(hm=hm, x=x, y=y) < (g.MOUNTAIN_HEIGHT - height - 1):
                libtcod.heightmap_add_hill(hm=hm, x=x, y=y, radius=radius, height=height)

        return hm


    def create_heightmap_from_surrounding_tiles(self, minh=-8, maxh=8, iterations=50):
        ## Create initial tiles
        #self.tiles = [[Tile(blocks_mov=False)
        #              for y in xrange(self.height)]
        #             for x in xrange(self.width)]

        hht = int(self.height/2)
        hwd = int(self.width/2)


        surrounding_heights = self.world.get_surrounding_heights(coords=(self.wx, self.wy))
        this_tile_height = min(surrounding_heights[4], g.MOUNTAIN_HEIGHT-10)

        # Which map tiles to use from surrounding_heights variable
        surrounding_heights_to_map = (
                                      (0, 0),             (hwd, 0),             (self.width-1, 0),
                                      (0, hht),           (hwd, hht),           (self.width-1, hht),
                                      (0, self.height-1), (hwd, self.height-1), (self.width-1, self.height-1)
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
            #g.game.add_message('height is %i'%libtcod.heightmap_get_value(hm, r1x, r1y), libtcod.red)
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
                if tile.height < g.WATER_HEIGHT:
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
        self.cit = mgen.CityMap(self, city_class, self.world.tiles[city_class.x][city_class.y].entities)
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

        self.tiles[x][y].objects.append(obj)

        if obj.creature and obj.creature.intelligence_level > 1:
            self.sapients.append(obj)
            obj.creature.next_tick = self.world.time_cycle.current_tick + 1
        elif obj.creature:
            self.creatures.append(obj)
            obj.creature.next_tick = self.world.time_cycle.current_tick + 1
        else:
            self.objects.append(obj)

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

        ## DIJMAPS
        factions_on_map = self.cache_factions_for_dmap()

        for obj in self.sapients:
            obj.creature.set_initial_desires(factions_on_map)

        if g.game.map_scale == 'human':
            g.game.add_message('%i objs; %i saps' %(len(self.objects), len(self.sapients)) )

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

        for sapient in self.sapients:
            if self.tiles[sapient.x][sapient.y].explored and sapient != g.player:
                sapient.draw()
        g.player.draw()

        #blit the contents of map_con to the root console
        g.game.interface.map_console.blit()

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
            self.tiles[xx][yy].char = random.choice(g.TREE_CHARS[i])
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
                road_start_positions.append(mgen.PathNode(x=i, y=j, size=5, neighbors=[]))

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
                    road_start_positions.append(mgen.PathNode(x=ii, y=jj, size=5, neighbors=[]))


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


