from __future__ import division
from collections import namedtuple


# Which actions set which actions as true
status_to_behaviors = {
    'at_location': ['move'],
    'have_item': ['buy_item', 'steal_item'],
    'have_money': ['get_money_through_work', 'steal_money'],
    'have_job': ['get_job'],
    'have_weapon': ['buy_item']
}

behavior_to_preconditions = {
    'move': ['at_location'],
    'buy_item': ['have_money', 'at_location'],
    'get_money_through_work': ['have_job', 'at_location'],
    'steal_money': ['am_alive', 'at_location'],
    'steal_item': ['am_alive', 'at_location'],
    'get_job': ['am_alive', 'at_location']
}

current_state = {
    'at_location': 1,
    'have_item': 0,
    'have_money': 0,
    'have_job': 0,
    'have_weapon': 0,
    'item_nearby': 0,
    'am_alive': 1
}


def check_preconditions(behavior):
    # For a given behavior, return the conditions which need to be true in order for the behavior to complete
    conditions = behavior_to_preconditions[behavior]
    unmet_conditions = [c for c in conditions if not current_state[c]]

    return unmet_conditions


def find_all_paths(goal_state):

    all_possible_paths = []
    tmp_paths = [[behavior] for behavior in status_to_behaviors[goal_state]]

    while tmp_paths:
        # The goal is to build an end-to-end path of behaviors
        for i, path in enumerate(tmp_paths[:]):

            first_path_iteration = 0

            last_behavior = path[-1]
            unmet_preconditions = check_preconditions(last_behavior)

            # If no unmet preconditions, we've found a complete behavior!
            if not unmet_preconditions:
                # Make sure to remove from tmp_paths
                tmp_paths.remove(path)
                all_possible_paths.append(path)
                break

            # Otherwise, go through all the
            for condition in unmet_preconditions:
                for behavior_option in status_to_behaviors[condition]:

                    if not first_path_iteration:
                        # On first pass through, just append the behavior option
                        tmp_paths[i].append(behavior_option)
                        first_path_iteration = 1
                    else:
                        # On subsequent passes, copy the path and then replace the last element with the current behavior
                        new_branched_path = tmp_paths[i][:]
                        new_branched_path[-1] = behavior_option
                        # Append to tmp_paths, which won't be iterated over since outer loop is making a copy of tmp_paths
                        tmp_paths.append(new_branched_path)

    return all_possible_paths


all_possible_paths = find_all_paths(goal_state='have_item')
print '\n\n === Paths === \n\n'
for p in all_possible_paths:
    print p


