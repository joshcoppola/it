from __future__ import division
from math import ceil
import random
from random import randint as roll
from collections import defaultdict
from time import time
import libtcodpy as libtcod

from helpers import infinite_defaultdict, libtcod_path_to_list
from traits import TRAIT_INFO
import config as g

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
        self.behaviors_to_accomplish = [MoveToLocation(initial_location=self.initial_location, target_location=self.target_location, entity=self.entity)]

    def is_completed(self):
        return (self.entity.wx, self.entity.wy) == self.target_location


class GoodsAreUnloaded:
    def __init__(self, target_city, goods, entity):
        self.target_city = target_city
        self.goods = goods
        self.entity = entity

        self.behaviors_to_accomplish = [UnloadGoodsBehavior(target_city=target_city, entity=entity)]

    def is_completed(self):
            return self.entity in self.target_city.caravans

class GoodsAreLoaded:
    def __init__(self, target_city, goods, entity):
        self.target_city = target_city
        self.goods = goods
        self.entity = entity

        self.behaviors_to_accomplish = [LoadGoodsBehavior(target_city=target_city, entity=entity)]

    def is_completed(self):
            return self.entity in self.target_city.caravans




class HaveItem:
    def __init__(self, item_name, entity):
        self.status = 'have_item'
        self.item_name = item_name
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [BuyItem(self.item_name, self.entity)] #, StealItem(self.item, self.entity)]

    def is_completed(self):
        return self.item_name in self.entity.creature.possessions


class KnowWhereItemisLocated:
    def __init__(self, item, entity):
        self.status = 'know_where_item_is_located'
        self.item = item
        self.entity = entity
        self.behaviors_to_accomplish = [FindOutWhereItemIsLocated(self.item, self.entity)]

    def is_completed(self):
        return self.entity.creature.knowledge['objects'][self.item]['location']['accuracy'] == 1


class HaveRoughIdeaOfLocation:
    def __init__(self, item, entity):
        self.status = 'have_rough_idea_of_location'
        self.item = item
        self.entity = entity
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.knowledge['objects'][self.item]['location']['accuracy'] <= 2


class HaveMoney:
    def __init__(self, money, entity):
        self.status = 'have_item'
        self.money = money
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [GetMoneyThroughWork(self.money, self.entity), StealMoney(self.money, self.entity)]

    def is_completed(self):
        return 1
        #return self.entity.creature.gold >= self.money


class HaveJob:
    def __init__(self, entity):
        self.status = 'have_job'
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [GetJob(self.entity)]

    def is_completed(self):
        return self.entity.creature.profession


class AmAvailableToAct:
    def __init__(self, entity):
        self.status = 'am_available_to_act'
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.is_available_to_act()



class ActionBase:
    ''' The base action class, providing some default methods for other actions '''
    def __init__(self):
        self.checked_for_movement = 0

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]

    def get_repeats(self):
        return 1

    def get_behavior_location(self, current_location):
        return roll(0, 10), roll(0, 10)



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

        self.costs = {'money':-1, 'time':1, 'distance':0, 'morality':0, 'legality':0}

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
    def __init__(self, item_name, entity):
        ActionBase.__init__(self)
        self.behavior = 'buy_item'
        self.item_name = item_name
        self.entity = entity
        self.preconditions = [HaveMoney(self.item_name, self.entity)]

        # Set in get_behavior_location()
        self.site = None

        self.costs = {'money':50, 'time':.1, 'distance':0, 'morality':0, 'legality':0}

    def get_behavior_location(self, current_location):
        ''' Find what cities sell the item we want, and then which of those cities is closest '''
        possible_cities = [city for city in g.WORLD.cities if self.item_name in city.object_to_agents_dict]

        closest_city, closest_dist = g.WORLD.get_closest_city(x=current_location[0], y=current_location[1], valid_cities=possible_cities)

        self.costs['distance'] += closest_dist
        self.costs['time'] += closest_dist

        self.site = closest_city

        return closest_city.x, closest_city.y

    def take_behavior_action(self):

        target_agent = random.choice([agent for agent in self.site.econ.agents if agent.reaction.is_finished_good and self.item_name in agent.get_sold_objects()])
        self.entity.creature.buy_object(obj=self.item_name, sell_agent=target_agent, price=target_agent.perceived_values[target_agent.buy_economy][target_agent.sold_commodity_name].center, material=None, create_object=1)

        # print target_agent.name, 'just sold', self.item_name, 'to', self.entity.fulltitle(), 'for', target_agent.perceived_values[target_agent.finished_good.name].center
        #print '{0} just bought a {1}'.format(self.entity.fulltitle(), self.item_name)

    def is_completed(self):
        return 1

class StealItem(ActionBase):
    def __init__(self, item, entity):
        ActionBase.__init__(self)
        self.behavior = 'steal_item'
        self.item = item
        self.entity = entity
        self.preconditions = [KnowWhereItemisLocated(self.item, self.entity)]

        self.costs = {'money':0, 'time':1, 'distance':0, 'morality':50, 'legality':50}



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

        if g.WORLD: # This would otherwise stop this module running as __main__, leaving this in for testing purposes
            target_site = g.WORLD.tiles[self.target_location[0]][self.target_location[1]].site
            current_site = g.WORLD.tiles[self.entity.wx][self.entity.wy].site

            if target_site in g.WORLD.cities and current_site in g.WORLD.cities:
                full_path = current_site.path_to[target_site][:]
            else:
                # Default - use libtcod's A* to create a path to destination
                path = libtcod.path_compute(p=g.WORLD.path_map, ox=self.entity.wx, oy=self.entity.wy, dx=self.target_location[0], dy=self.target_location[1])
                full_path = libtcod_path_to_list(path_map=g.WORLD.path_map)

            # Add path to brain
            self.entity.world_brain.path = full_path
            # Update the cost of this behavior
            self.costs['time'] += len(full_path)
            self.costs['distance'] += len(full_path)

        else:
            # Stuff to give this movement a random cost
            cost = roll(1, 10)
            self.costs['distance'] = cost
            self.costs['time'] = cost


    def get_name(self):
        goal_name = '{0} to {1}'.format(self.travel_verb, g.WORLD.tiles[self.target_location[0]][self.target_location[1]].get_location_description())
        return goal_name

    def is_completed(self):
        return (self.entity.wx, self.entity.wy) == self.target_location

    def take_behavior_action(self):
        self.entity.w_move_along_path(path=self.entity.world_brain.path)



class UnloadGoodsBehavior(ActionBase):
    def __init__(self, target_city, entity):
        ActionBase.__init__(self)
        self.behavior = 'unload goods'
        self.target_city = target_city
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

        self.costs = {'money':0, 'time':.1, 'distance':0, 'morality':0, 'legality':0}

    def get_name(self):
        goal_name = 'unload goods in {0}'.format(self.target_city.name)
        return goal_name

    def is_completed(self):
        return self.entity in self.target_city.caravans

    def get_behavior_location(self, current_location):
        return self.target_city.x, self.target_city.y

    def take_behavior_action(self):
        if self.entity not in self.target_city.caravans:
            self.target_city.receive_caravan(self.entity)
        else:
            g.game.add_message('{0} tried to unload caravan goods and was already in {1}.caravans'.format(self.entity.fulltitle(), self.target_city.name), libtcod.red)


class LoadGoodsBehavior(ActionBase):
    def __init__(self, target_city, entity):
        ActionBase.__init__(self)
        self.behavior = 'load goods'
        self.target_city = target_city
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

        self.costs = {'money':0, 'time':.1, 'distance':0, 'morality':0, 'legality':0}

    def get_name(self):
        goal_name = 'load goods in {0}'.format(self.target_city.name)
        return goal_name

    def is_completed(self):
        return self.entity in self.target_city.caravans

    def get_behavior_location(self, current_location):
        return self.target_city.x, self.target_city.y

    def take_behavior_action(self):
        if self.entity not in self.target_city.caravans:
            self.target_city.receive_caravan(self.entity)
        else:
            g.game.add_message('{0} tried to pick up caravan goods and was already in {1} caravans'.format(self.entity.fulltitle(), self.target_city.name), libtcod.red)

# class WaitBehavior:
#     ''' Used anytime a figure wants to wait somewhere and do some activity '''
#     def __init__(self, figure, location, num_days, travel_verb, activity_verb):
#         self.goal = None # will be set when added to a Goal
#         self.figure = figure
#         self.location= location
#         self.num_days = num_days
#         self.num_days_left = num_days
#         self.travel_verb = travel_verb
#         self.activity_verb = activity_verb
#
#         self.is_active = 0
#
#     def get_name(self):
#         if (self.figure.wx, self.figure.wy) != self.location:
#             goal_name = '{0} to {1} to {2} for {3} days'.format(self.travel_verb, g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description(), self.activity_verb, self.num_days)
#         else:
#             goal_name = '{0} in {1} for {2} days'.format(self.activity_verb, g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description(), self.num_days)
#
#         return goal_name
#
#     def initialize_behavior(self):
#         # If we're not in the location, travel there
#         if (self.figure.wx, self.figure.wy) != self.location:
#             self.goal.behavior_list.insert(0, MovLocBehavior(location=self.location, figure=self.figure, travel_verb=self.travel_verb))
#             self.goal.behavior_list[0].initialize_behavior()
#
#             #g.game.add_message('{0} has decided to {1}'.format(self.figure.fulltitle(), self.get_name()), libtcod.color_lerp(g.PANEL_FRONT, self.figure.color, .5))
#
#             event = hist.TravelStart(date=g.WORLD.time_cycle.get_current_date(), location=(self.figure.wx, self.figure.wy),
#                                      to_location=self.location, figures=self.figure.creature.commanded_figures + [self.figure], populations=self.figure.creature.commanded_populations)
#             g.game.add_message(event.describe(), libtcod.color_lerp(g.PANEL_FRONT, self.figure.color, .3))
#         else:
#             self.is_active = 1
#
#     def is_completed(self):
#         ''' Add event when we reach destination'''
#         if self.num_days_left == 0:
#             event = hist.TravelEnd(date=g.WORLD.time_cycle.get_current_date(), location=(self.figure.wx, self.figure.wy),
#                                    figures=self.figure.creature.commanded_figures  + [self.figure], populations=self.figure.creature.commanded_populations)
#             g.game.add_message(event.describe(), libtcod.color_lerp(g.PANEL_FRONT, self.figure.color, .3))
#             return 1
#
#         else:
#             return 0
#
#     def take_behavior_action(self):
#         self.num_days_left -= 1


class KillTargBehavior:
    ''' Behavior for moving to something that's not a city (a historical figure, perhaps)'''
    def __init__(self, target, figure):
        self.target = target
        # The object
        self.figure = figure

        self.is_active = 0
        self.has_attempted_kill = 0

    def initialize_behavior(self):
        self.is_active= 1

    def get_name(self):
        goal_name = 'Kill {0}'.format(self.target.fulltitle())
        return goal_name

    def is_completed(self):
        # return self.target.creature.status == 'dead'
        return self.has_attempted_kill

    def take_behavior_action(self):

        battle = combat.WorldBattle(date=g.WORLD.time_cycle.get_current_date(), location=(self.figure.wx, self.figure.wy),
                                    faction1_named=[self.figure], faction1_populations=[], faction2_named=[self.target], faction2_populations=[])
        g.game.add_message(battle.describe(), libtcod.color_lerp(g.PANEL_FRONT, self.figure.color, .3))

        self.has_attempted_kill = 1

        #if roll(0, 1):
        #    self.target.creature.die()

#
# class CaptureTargBehavior:
#     ''' Behavior for capturing a target '''
#     def __init__(self, target, figure):
#         self.target = target
#         # The object
#         self.figure = figure
#
#         self.is_active = 0
#
#     def initialize_behavior(self):
#         self.is_active= 1
#
#     def is_completed(self):
#         return self.target in self.figure.creature.captives
#
#     def take_behavior_action(self):
#         pass
#
#
# class ImprisonTargBehavior:
#     ''' Behavior for moving a captive from an ary into a building '''
#     def __init__(self, target, figure, building):
#         self.target = target
#         # The object
#         self.figure = figure
#         self.building = building
#
#         self.is_active = 0
#
#     def initialize_behavior(self):
#         self.is_active= 1
#
#     def is_completed(self):
#         if self.target in self.building.captives:
#             g.game.add_message('WOOT', libtcod.dark_chartreuse)
#
#         return self.target in self.building.captives
#
#     def take_behavior_action(self):
#         pass
#         #self.figure.creature.army.transfer_captive_to_building(figure=self.target, target_building=self.building)





def get_movement_behavior_subtree(entity, current_location, target_location):

    if current_location and target_location and current_location != target_location:
        movement_behavior_subtree = find_actions_leading_to_goal(goal_state=AtLocation(initial_location=current_location , target_location=target_location, entity=entity), action_path=[], all_possible_paths=[])
    else:
        movement_behavior_subtree = []

    return movement_behavior_subtree


def find_actions_leading_to_goal(goal_state, action_path, all_possible_paths):
    ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal '''
    #print ' --- ', r_level, goal_state.status, [a.behavior for a in action_list], ' --- '

    for behavior_option in goal_state.behaviors_to_accomplish:
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
    g.init()
    # No traits
    test_entity_normal = TestEntity()
    # Honest trait
    test_entity_moral = TestEntity()
    test_entity_moral.creature.traits['honest'] = 2
    # Disonest Trait
    test_entity_amoral = TestEntity()
    test_entity_amoral.creature.traits['dishonest'] = 2

    begin = time()
    best_path = test_entity_normal.world_brain.set_goal(goal_state=HaveItem(item_name=GOAL_ITEM, entity=test_entity_normal), reason='because')
    print 'done in {0}'.format(time() - begin)
    #print [b.behavior for b in best_path]

    print ''

    begin = time()
    best_path = test_entity_amoral.world_brain.set_goal(goal_state=HaveItem(item_name=GOAL_ITEM, entity=test_entity_amoral), reason='because')
    print 'done in {0}'.format(time() - begin)

    best_path = test_entity_moral.world_brain.set_goal(goal_state=GoodsAreUnloaded(target_city='debug', goods='lol', entity=test_entity_moral), reason='because')
    #print [b.behavior for b in best_path]
#
# path_list = find_actions_leading_to_goal(goal_state=HaveItem(item_name=GOAL_ITEM, entity=test_entity_normal), action_path=[], all_possible_paths=[])
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