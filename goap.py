from __future__ import division
from math import ceil
from random import randint as roll
from collections import defaultdict

from helpers import infinite_defaultdict
from traits import TRAIT_INFO


GOAL_ITEM = 'cheese'



class TestCreature:
    def __init__(self):
        self.possessions = set([])
        self.gold = 10
        self.profession = None

        self.traits = {}

        self.knowledge = infinite_defaultdict()
        self.knowledge['objects'][GOAL_ITEM]['location']['accuracy'] = 2

    def is_available_to_act(self):
        return 1

class TestEntity:
    def __init__(self):
        self.creature = TestCreature()

        self.wx = 10
        self.wy = 10

        self.world_brain = BasicWorldBrain()
        self.world_brain.owner = self





class AtLocation:
    def __init__(self, initial_location, target_location, entity):
        self.status = 'at_location'
        self.initial_location = initial_location
        self.target_location = target_location
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return (self.entity.wx, self.entity.wy) == self.target_location

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = [MoveToLocation(initial_location=self.initial_location, target_location=self.target_location, entity=self.entity)]
        return self.behaviors_to_accomplish


class HaveItem:
    def __init__(self, item, entity):
        self.status = 'have_item'
        self.item = item
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.item in self.entity.creature.possessions

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = [BuyItem(self.item, self.entity), StealItem(self.item, self.entity)]
        return self.behaviors_to_accomplish


class KnowWhereItemisLocated:
    def __init__(self, item, entity):
        self.status = 'know_where_item_is_located'
        self.item = item
        self.entity = entity
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.knowledge['objects'][self.item]['location']['accuracy'] == 1

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = [FindOutWhereItemIsLocated(self.item, self.entity)]
        return self.behaviors_to_accomplish


class HaveRoughIdeaOfLocation:
    def __init__(self, item, entity):
        self.status = 'have_rough_idea_of_location'
        self.item = item
        self.entity = entity
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.knowledge['objects'][self.item]['location']['accuracy'] <= 2

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = []
        return self.behaviors_to_accomplish


class HaveMoney:
    def __init__(self, money, entity):
        self.status = 'have_item'
        self.money = money
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.gold >= self.money

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = [GetMoneyThroughWork(self.money, self.entity), StealMoney(self.money, self.entity)]
        return self.behaviors_to_accomplish


class HaveJob:
    def __init__(self, entity):
        self.status = 'have_job'
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.profession

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = [GetJob(self.entity)]
        return self.behaviors_to_accomplish

class AmAvailableToAct:
    def __init__(self, entity):
        self.status = 'am_available_to_act'
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.is_available_to_act()

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = []
        return self.behaviors_to_accomplish



class ActionBase:
    ''' The base action class, providing some default methods for other actions '''
    def __init__(self):
        self.checked_for_movement = 0

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]

    def get_repeats(self):
        return 1

    def get_possible_locations(self):
        return [(roll(0, 10), roll(0, 10))]

    def get_behavior_location(self, current_location):
        return roll(0, 10), roll(0, 10)


class MoveToLocation(ActionBase):
    ''' Specific behavior component for moving to an area.
    Will use road paths if moving from city to city '''
    def __init__(self, initial_location, target_location, entity, travel_verb='travel'):
        ActionBase.__init__(self)
        self.behavior = 'move'
        self.initial_location = initial_location
        self.target_location = target_location
        self.entity = entity

        self.travel_verb = travel_verb

        self.preconditions = [AmAvailableToAct(self.entity)]

        self.costs = {'money':0, 'time':0, 'distance':0, 'morality':0, 'legality':0}

        cost = roll(1, 10)
        self.costs['distance'] = cost
        self.costs['time'] = cost

    def get_name(self):
        goal_name = '{0} to {1}'.format(self.travel_verb, g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description())
        return goal_name

    def initialize_behavior(self):
        ''' Will be run as soon as this behavior is activated '''
        target_site = g.WORLD.tiles[self.x][self.y].site
        current_site = g.WORLD.tiles[self.entity.wx][self.entity.wy].site

        if target_site in g.WORLD.cities and current_site in g.WORLD.cities:
            full_path = current_site.path_to[target_site][:]
        else:
            # Default - use libtcod's A* to create a path to destination
            path = libtcod.path_compute(p=g.WORLD.path_map, ox=self.entity.wx, oy=self.entity.wy, dx=self.x, dy=self.y)
            full_path = libtcod_path_to_list(path_map=g.WORLD.path_map)

        # Add path to brain
        self.entity.world_brain.path = full_path
        # Update the cost of this behavior
        self.costs['time'] += len(full_path)
        self.costs['distance'] += len(full_path)


    def is_completed(self):
        return (self.figure.wx, self.figure.wy) == (self.x, self.y)

    def take_behavior_action(self):
        self.figure.w_move_along_path(path=self.figure.world_brain.path)



class FindOutWhereItemIsLocated(ActionBase):
    def __init__(self, item, entity):
        ActionBase.__init__(self)
        self.behavior = 'find_out_where_item_is_located'
        self.item = item
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

        self.costs = {'money':0, 'time':.1, 'distance':0, 'morality':0, 'legality':0}

    def get_behavior_location(self, current_location):
        return None

class SearchForItem(ActionBase):
    def __init__(self, item, entity):
        ActionBase.__init__(self)
        self.behavior = 'search_for_item'
        self.item = item
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity), HaveRoughIdeaOfLocation(self.item, self.entity)]

        self.costs = {'money':0, 'time':1, 'distance':0, 'morality':0, 'legality':0}

class GetJob(ActionBase):
    def __init__(self, entity):
        ActionBase.__init__(self)
        self.behavior = 'get_job'
        self.entity = entity
        self.preconditions = [AmAvailableToAct(self.entity)]

        self.costs = {'money':0, 'time':0, 'distance':0, 'morality':0, 'legality':0}

class GetMoneyThroughWork(ActionBase):
    def __init__(self, money, entity):
        ActionBase.__init__(self)
        self.behavior = 'get_money_through_work'
        self.money = money
        self.entity = entity
        self.preconditions = [HaveJob(self.entity)]

        self.costs = {'money':0, 'time':10, 'distance':0, 'morality':0, 'legality':0}

    def get_repeats(self):
        return ceil(self.money / self.entity.profession.monthly_pay)

    # def get_behavior_location(self):
    #     return self.entity.profession.current_work_building.site.x, self.entity.profession.current_work_building.site.y

    #def is_at_location(self):
    #    return (self.entity.wx, self.entity.wy) == self.get_behavior_location()


class StealMoney(ActionBase):
    def __init__(self, money, entity):
        ActionBase.__init__(self)
        self.behavior = 'steal_money'
        self.money = money
        self.entity = entity
        self.preconditions = [AmAvailableToAct(self.entity)]

        self.costs = {'money':0, 'time':1, 'distance':0, 'morality':50, 'legality':50}


class BuyItem(ActionBase):
    def __init__(self, item, entity):
        ActionBase.__init__(self)
        self.behavior = 'buy_item'
        self.item = item
        self.entity = entity
        self.preconditions = [HaveMoney(self.item, self.entity)]

        self.costs = {'money':50, 'time':.1, 'distance':0, 'morality':0, 'legality':0}

class StealItem(ActionBase):
    def __init__(self, item, entity):
        ActionBase.__init__(self)
        self.behavior = 'steal_item'
        self.item = item
        self.entity = entity
        self.preconditions = [KnowWhereItemisLocated(self.item, self.entity)]

        self.costs = {'money':0, 'time':1, 'distance':0, 'morality':50, 'legality':50}


def get_movement_behavior_subtree_old(action_path, new_behavior):

    loc1 = new_behavior.get_behavior_location()
    loc2 = action_path[0].get_behavior_location() if action_path else None

    if loc1 and loc2 and loc1 != loc2 and new_behavior.behavior != 'move':
        movement_behavior_subtree = find_actions_leading_to_goal(goal_state=AtLocation(initial_location=loc1, target_location=loc2, entity=action_path[0].entity), action_path=[], all_possible_paths=[])
    else:
        movement_behavior_subtree = [[]]

    return movement_behavior_subtree


def find_actions_leading_to_goal_old(goal_state, action_path, all_possible_paths):
    ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal '''
    #print ' --- ', r_level, goal_state.status, [a.behavior for a in action_list], ' --- '

    for behavior_option in goal_state.set_behaviors_to_accomplish():
        ## CHECK IF MOVEMENT IS NEEDED
        movement_behavior_subtree = get_movement_behavior_subtree(action_path=action_path, new_behavior=behavior_option)
        unmet_conditions = behavior_option.get_unmet_conditions()

        for subtree in movement_behavior_subtree:
            current_action_path = [behavior_option] + subtree + action_path # Copy of the new behavior + action_path

            # If there are conditions that need to be met, then we find the actions that can be taken to complete each of them
            for condition in unmet_conditions:
                find_actions_leading_to_goal(goal_state=condition, action_path=current_action_path, all_possible_paths=all_possible_paths)

            # If all conditions are met, then this behavior can be accomplished, so it gets added to the list
            if not unmet_conditions and behavior_option != 'move':
                movement_behavior_subtree = get_movement_behavior_subtree(action_path=action_path, new_behavior=behavior_option)
                for new_subtree in movement_behavior_subtree:
                    all_possible_paths.append(new_subtree + current_action_path)

    return all_possible_paths





def get_movement_behavior_subtree(entity, current_location, target_location):

    if current_location and target_location and current_location != target_location:
        movement_behavior_subtree = find_actions_leading_to_goal(goal_state=AtLocation(initial_location=current_location , target_location=target_location, entity=entity), action_path=[], all_possible_paths=[])
    else:
        movement_behavior_subtree = []

    return movement_behavior_subtree


def find_actions_leading_to_goal(goal_state, action_path, all_possible_paths):
    ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal '''
    #print ' --- ', r_level, goal_state.status, [a.behavior for a in action_list], ' --- '

    for behavior_option in goal_state.set_behaviors_to_accomplish():
        unmet_conditions = behavior_option.get_unmet_conditions()
        current_action_path = [behavior_option] + action_path # Copy of the new behavior + action_path

        # If there are conditions that need to be met, then we find the actions that can be taken to complete each of them
        for condition in unmet_conditions:
            find_actions_leading_to_goal(goal_state=condition, action_path=current_action_path, all_possible_paths=all_possible_paths)

        # If all conditions are met, then this behavior can be accomplished, so it gets added to the list
        if not unmet_conditions:
            all_possible_paths.append(current_action_path)
            #print [a.behavior for a in current_action_path]
            #all_paths_worked = adjust_path_for_movement(entity=test_entity, initial_location=(goal_state.entity.wx, goal_state.entity.wy), action_path=current_action_path, all_paths_worked=[])
            #for i, p in enumerate(all_paths_worked):
                # print i, [a.behavior for a in p]
                #all_possible_paths.append(p)

    return all_possible_paths


def check_paths_for_movement(entity, behavior_lists):
    ''' This will adjust an input list of behavior lists to account for movement between behaviors. Any additional
        behaviors required by the movement behavior will be evaluated before the movement '''
    all_behavior_lists_worked = []

    for behavior_list in behavior_lists:
        # Reset current_location to be the entity's current location for each behavior tree in the list
        current_location = entity.wx, entity.wy
        behavior_list_worked = []

        for behavior in behavior_list:
            target_location = behavior.get_behavior_location(current_location=current_location)
            ## Only need to worry about moving if the behavior A) Requires movement and B) is different than the current location
            if target_location and (target_location != current_location):
                behavior_list_worked.append(MoveToLocation(initial_location=current_location, target_location=target_location, entity=entity))
                # Update "current_location" (even though this will be in the future) since we will need to know whether we'll need to move from this spot to the next behavior
                current_location = target_location
            # Whether or not we move, we must make sure to add the behavior back into our adjusted list
            behavior_list_worked.append(behavior)

        all_behavior_lists_worked.append(behavior_list_worked)

    return all_behavior_lists_worked


def get_behavior_list_costs(behavior_lists):

    all_behaviors_costed = []

    for behavior_list in behavior_lists:
        total_costs = defaultdict(int)

        for behavior in behavior_list:
            for aspect, cost in behavior.costs.iteritems():
                total_costs[aspect] += cost

        all_behaviors_costed.append((behavior_list, total_costs))

    return all_behaviors_costed


# def adjust_path_for_movement(entity, initial_location, action_path, all_paths_worked, r_level=0):
#     ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal '''
#     if r_level > 10:
#         print "MAXIMUM RECURSION!"
#         return
#     current_location = initial_location
#     current_action_path = action_path[:]
#     need_to_recurse = 0
#     for i, behavior in enumerate(action_path):
#         if (not behavior.checked_for_movement) and behavior.behavior != 'move':
#             target_location = behavior.get_behavior_location(current_location=current_location)
#             behavior.checked_for_movement = 1
#
#             if target_location and target_location != current_location:
#                 movement_behavior_subtree = get_movement_behavior_subtree(entity=entity, current_location=current_location, target_location=target_location)
#                 # print 'movement to', behavior.behavior, 'from', action_path[i-1].behavior if i > 0 else 'beginning', 'is', movement_behavior_subtree
#                 for subtree in movement_behavior_subtree:
#                     current_action_path_including_movement = current_action_path[:]
#                     for s_behavior in reversed(subtree):
#                         current_action_path_including_movement.insert(i, s_behavior)
#
#                     need_to_recurse = 1
#                     adjust_path_for_movement(entity=entity, initial_location=initial_location, action_path=current_action_path_including_movement, all_paths_worked=all_paths_worked, r_level=r_level+1)
#
#             behavior.checked_for_movement = 0
#
#     #unchecked_for_movement = [a for a in current_action_path if (a.behavior != 'move' and not a.checked_for_movement)]
#     #if not unchecked_for_movement:
#     if not need_to_recurse:
#         #print len(current_action_path)-
#         all_paths_worked.append(current_action_path)
#
#     return all_paths_worked

def get_costed_behavior_paths(goal_state, entity):
    # Find possible actions that can be taken to get there
    all_possible_behavior_paths = find_actions_leading_to_goal(goal_state=goal_state, action_path=[], all_possible_paths=[])
    # Account for movement (eventually, account for movement subtrees?)
    behavior_list_including_movement = check_paths_for_movement(entity=entity, behavior_lists=all_possible_behavior_paths)
    # With movement now factored in, get costs
    behavior_lists_costed = get_behavior_list_costs(behavior_lists=behavior_list_including_movement)

    return behavior_lists_costed


if __name__ == '__main__':
    from it import BasicWorldBrain
    # No traits
    test_entity_normal = TestEntity()
    # Honest trait
    test_entity_moral = TestEntity()
    test_entity_moral.creature.traits['honest'] = 2
    # Disonest Trait
    test_entity_amoral = TestEntity()
    test_entity_amoral.creature.traits['dishonest'] = 2

    best_path = test_entity_normal.world_brain.set_goal(goal_state=HaveItem(item=GOAL_ITEM, entity=test_entity_normal), reason='because')
    #print [b.behavior for b in best_path]

    print ''

    best_path = test_entity_amoral.world_brain.set_goal(goal_state=HaveItem(item=GOAL_ITEM, entity=test_entity_amoral), reason='because')
    #print [b.behavior for b in best_path]
#
# path_list = find_actions_leading_to_goal(goal_state=HaveItem(item=GOAL_ITEM, entity=test_entity_normal), action_path=[], all_possible_paths=[])
# #for p in path_list:
# #    print [b.behavior for b in p]
#
# behavior_list_including_movement = check_paths_for_movement(entity=test_entity_normal, behavior_lists=path_list)
# for list_ in behavior_list_including_movement:
#     print [b.behavior for b in list_]
#
# behavior_lists_costed = get_behavior_list_costs(behavior_lists=behavior_list_including_movement)
# for behavior_list, cost in behavior_lists_costed:
#     print [b.behavior for b in behavior_list]
#     print cost
#     print ''
#
# cheapest = test_entity_normal.world_brain.find_cheapest_behavior_path(behavior_paths_costed=behavior_lists_costed)
# print [b.behavior for b in cheapest]
#
# cheapest = test_entity_amoral.world_brain.find_cheapest_behavior_path(behavior_paths_costed=behavior_lists_costed)
# print [b.behavior for b in cheapest]