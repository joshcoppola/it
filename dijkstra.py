''' Code for dijkstra "maps" '''

class Node:
    # A node in a Dijkstra map.
    def __init__(self, owner, x, y):
        self.owner = owner
        self.x = x
        self.y = y

        self.current_locs = [(x, y)]
        self.current_value = 1

    def expand(self):
        new_locs = []
        expanded = False

        # Check each location's 8 neighbors and update dmap with value
        for ox, oy in self.current_locs:
            for x, y in ((ox - 1, oy - 1), (ox, oy - 1),  (ox + 1, oy - 1),
                         (ox - 1, oy),                    (ox + 1, oy),
                         (ox - 1, oy + 1), (ox, oy + 1),  (ox + 1, oy + 1)):

                # Can't use tile_blocks_mov() function because it will set all tiles with objects in them to 0
                if self.owner.sourcemap.is_val_xy((x, y)) and (self.owner.dmap[x][y] is None) and (not self.owner.sourcemap.tiles[x][y].blocks_mov): # (not self.owner.sourcemap.tile_blocks_mov(x, y)) :
                    new_locs.append((x, y))
                    self.owner.dmap[x][y] = self.current_value
                    expanded = True

        self.current_locs = new_locs
        self.current_value += 1

        # Remove from owner's nodes when this node has hit the maximum dmap range, or did not expand
        if not expanded or self.current_value == self.owner.dmrange:
            self.owner.nodes.remove(self)


class Dijmap:
    def __init__(self, sourcemap, target_nodes, dmrange):
        self.sourcemap = sourcemap
        ## The represented map that we draw from
        self.dmrange = dmrange

        self.empty_map = [[None for y in xrange(sourcemap.height)] for x in xrange(sourcemap.width)]

        self.nodes = []
        self.dmap = None

        # Automatically create a map on initializing
        self.update_map(target_nodes)


    def update_map(self, target_nodes):
        # Seed empty map - faster to copy off of empty_map than create a new one
        self.dmap = [row[:] for row in self.empty_map]

        # Clear nodes and then add new ones
        self.nodes = []
        for x, y in target_nodes:
            self.nodes.append(Node(self, x, y))
            self.dmap[x][y] = 0

        ## Take the target nodes, and expand each of them until none of them mark a spot
        while self.nodes:
            for node in self.nodes:
                node.expand()
