
from __future__ import division
from math import ceil
from collections import defaultdict

import libtcodpy as libtcod

class Chunk:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.tiles = []

    def add_tile(self, tile):
        self.tiles.append(tile)
        # Make sure the tile knows its chunk
        tile.chunk = self


class RegionChunk(Chunk):
    def __init__(self, x, y):
        Chunk.__init__(self, x, y)

        self.entities = []
        self.populations = []

        self.sites = []
        self.minor_sites = []
        self.caves = []

        # Will be stored as resource: [location1, location2, ...] where locations are tuples
        self.resources = defaultdict(list)

    def get_all_sites(self):
        return self.sites + self.minor_sites + self.caves

    def add_site(self, site):
        self.sites.append(site)

    def add_minor_site(self, site):
        self.minor_sites.append(site)

    def add_cave(self, cave):
        self.caves.append(cave)

    def add_entity(self, entity):
        self.entities.append(entity)

    def remove_entity(self, entity):
        self.entities.remove(entity)

    def add_population(self, population):
        self.populations.append(population)

    def remove_population(self, population):
        self.populations.remove(population)

class TileChunk(Chunk):
    def __init__(self, x, y):
        Chunk.__init__(self, x, y)

        self.objects = []



class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.tiles = []
        # Tiles to be chunked
        self.chunk_tiles = []
        self.chunk_width = None
        self.chunk_height = None

    def is_val_xy(self, coords):
        return (0 < coords[0] < self.width) and (0 < coords[1] < self.height)

    def get_astar_distance_to(self, x, y, target_x, target_y):
        libtcod.path_compute(self.path_map, x, y, target_x, target_y)
        new_path_len = libtcod.path_size(self.path_map)

        return new_path_len


    def setup_chunks(self, chunk_size, map_type):
        ''' Set up "chunks" of tiles, useful for checking nearby things without having to loop through all map tiles '''

        # How many chunks in the world (width and height)
        self.chunk_width = int(ceil(self.width/chunk_size))
        self.chunk_height = int(ceil(self.height/chunk_size))

        if map_type == 'world':
            for x in xrange(self.chunk_width):
                col = []
                for y in xrange(self.chunk_height):
                    chunk = RegionChunk(x, y)
                    # Loop through the tiles, but ensure we never go outside map bounds
                    for wx in xrange(x*chunk_size, min(self.width, (x*chunk_size)+chunk_size)):
                        for wy in xrange(y*chunk_size, min(self.height, (y*chunk_size)+chunk_size)):
                            chunk.add_tile(self.tiles[wx][wy])
                    col.append(chunk)

                self.chunk_tiles.append(col)

        if map_type == 'human':
            for x in xrange(self.chunk_width):
                col = []
                for y in xrange(self.chunk_height):
                    chunk = TileChunk(x, y)
                    # Loop through the tiles, but ensure we never go outside map bounds
                    for wx in xrange(x*chunk_size, min(self.width, (x*chunk_size)+chunk_size)):
                        for wy in xrange(y*chunk_size, min(self.height, (y*chunk_size)+chunk_size)):
                            chunk.add_tile(self.tiles[wx][wy])
                    col.append(chunk)

                self.chunk_tiles.append(col)

    def get_nearby_chunks(self, chunk, distance):
        ''' Return nearby chunks bordering which are <distance> away from chunk.x, chunk.y '''
        return [self.chunk_tiles[cx][cy] for cy in xrange(chunk.y - distance, chunk.y + distance + 1)
                for cx in xrange(chunk.x - distance, chunk.x + distance + 1) if 0 <= cx < self.chunk_width and 0 <= cy < self.chunk_height]
