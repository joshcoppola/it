''' Code for dijkstra "maps" '''

class Node:
    # A node in a Dijkstra map.
    def __init__(self, owner, x, y):
        self.owner = owner
        self.x = x
        self.y = y

        self.current_locs = [(x, y)]
        self.current_value = 0

        self.active = 1

    def expand(self):
        new_locs = []
        expanded = False
        for ox, oy in self.current_locs:
            for x, y in ((ox - 1, oy - 1), (ox, oy - 1),  (ox + 1, oy - 1),
                         (ox - 1, oy),                    (ox + 1, oy),
                         (ox - 1, oy + 1), (ox, oy + 1),  (ox + 1, oy + 1)):

                #if M.is_val_xy((x, y)) and (not self.owner.sourcemap[x][y].blocked) and (self.owner.dmap[x][y] == self.owner.range):
                if self.owner.sourcemap.is_val_xy((x, y)) and (not self.owner.sourcemap.tile_blocks_mov(x, y)) and (self.owner.dmap[x][y] == self.owner.dmrange):
                    new_locs.append((x, y))
                    self.owner.dmap[x][y] = self.current_value
                    expanded = True

        self.current_locs = new_locs
        self.current_value += 1

        if not expanded or self.current_value == self.owner.dmrange:
            self.active = 0

        return expanded


class Dijmap:
    def __init__(self, sourcemap, target_nodes, dmrange):
        self.sourcemap = sourcemap
        ## The represented map that we draw from
        self.dmrange = dmrange
        self.recalculate = 0

        empty_val = max(dmrange, 0)

        self.empty_map = [[empty_val for y in xrange(sourcemap.height)] for x in xrange(sourcemap.width)]

        self.update_map(target_nodes)

    #def tile_is_expandible(self, coords):
        # ''' When looping through nodes, this function is essentially a way to figure out if the tile has already been expanded to or not '''
        #return self.dmrange is None or self.dmap[coords[0]][coords[1]] == self.dmrange
        #if self.dmrange is None:
        #    return 1
        #elif self.dmap[coords[0]][coords[1]] == self.dmrange:
        #    return 1

    def update_map(self, target_nodes):
        self.dmap = [row[:] for row in self.empty_map]

        self.nodes = []
        for x, y in target_nodes:
            self.nodes.append(Node(self, x, y))
            self.dmap[x][y] = 0

        marked_status = True
        ## Take the target nodes, and expand each of them until none of them mark a spot
        while marked_status:
            marked_status = False
            for node in self.nodes:
                if node.active:
                    marked_status = node.expand()
                    
                    