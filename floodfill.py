

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