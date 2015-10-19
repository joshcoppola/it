from __future__ import division
from math import ceil
import random
from random import randint as roll
from collections import defaultdict
from time import time
from itertools import chain

import libtcodpy as libtcod

from helpers import infinite_defaultdict, libtcod_path_to_list
from traits import TRAIT_INFO
import config as g
import data_importer as data

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
        self.initial_location = initial_location
        self.target_location = target_location
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [MoveToLocation(initial_location=self.initial_location, target_location=self.target_location, entity=self.entity)]

    def is_completed(self):
        return (self.entity.wx, self.entity.wy) == self.target_location


class IsHangingOut:
    ''' State needed to get an entity moving somewhere where the movement itself is the end goal.
        Used due to issue with AtLocation directly calling the MoveToLocation behavior'''
    def __init__(self, target_location, entity):
        self.target_location = target_location
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [SetupWaitBehavior(target_location=target_location, entity=entity)]

    def is_completed(self):
        # Considered complete once we are at the location -- movement behavior will be automatically generated as this
        # behavior gets analyzed
        return (self.entity.wx, self.entity.wy) == self.target_location

    def get_name(self):
        return 'spend time at {0}'.format(g.WORLD.tiles[self.target_location[0]][self.target_location[1]].get_location_description())

class GoodsAreUnloaded:
    def __init__(self, target_city, goods, entity):
        self.target_city = target_city
        self.goods = goods
        self.entity = entity

        self.behaviors_to_accomplish = [UnloadGoodsBehavior(target_city=target_city, entity=entity)]

    def is_completed(self):
            return self.entity in self.target_city.caravans

    def get_name(self):
        return 'have goods unloaded in {0}'.format(self.target_city.name)

class GoodsAreLoaded:
    def __init__(self, target_city, goods, entity):
        self.target_city = target_city
        self.goods = goods
        self.entity = entity

        self.behaviors_to_accomplish = [LoadGoodsBehavior(target_city=target_city, entity=entity)]

    def is_completed(self):
            return self.entity in self.target_city.caravans

    def get_name(self):
        return 'have goods in {0} loaded'.format(self.target_city.name)

class HaveCommodityAtLocation:
    def __init__(self, commodity, quantity, entity, target_location):
        self.commodity = commodity
        self.quantity = quantity
        self.entity = entity
        self.target_location = target_location

        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [BringCommodityToLocation(commodity=commodity, quantity=quantity, entity=self.entity, target_location=target_location)]


    def is_completed(self):
        return self.entity.creature.econ_inventory[self.commodity] >= self.quantity and (self.entity.wx, self.entity.wy) == self.target_location

    def get_name(self):
        return 'have {0} {1} at {2}'.format(self.quantity, self.commodity, g.WORLD.tiles[self.target_location[0]][self.target_location[1]].get_location_description())

class HaveCommodity:
    ''' State of having a commodity in inventory, and potentially being at a particular location once the commodity is owned '''
    def __init__(self, commodity, quantity, entity):
        self.commodity = commodity
        self.quantity = quantity

        self.entity = entity
        # Will be set if this status isn't already completed
        # self.behaviors_to_accomplish = [BuyCommodity(self.commodity, self.entity)]
        self.behaviors_to_accomplish = []

        # Consider gathering the commodity if it is a raw resource
        if data.commodity_manager.name_is_resource(self.commodity):
            self.behaviors_to_accomplish.append(GatherCommodityBehavior(self.commodity, self.quantity, self.entity))

        # Else consider doing the reaction if it's a finished good
        elif data.commodity_manager.name_is_good(self.commodity):
            self.behaviors_to_accomplish.append(DoReaction(self.commodity, self.quantity, self.entity))

        else:
            g.game.add_message('Input is not commodity', libtcod.red)

    def is_completed(self):
        ''' Target location is optional to include, so only check for it if necessary '''
        return self.entity.creature.econ_inventory[self.commodity] >= self.quantity

    def get_name(self):
        return 'have {0} {1}'.format(self.quantity, self.commodity)

class HaveItem:
    def __init__(self, item_name, entity):
        self.item_name = item_name
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = [BuyItem(self.item_name, self.entity)] #, StealItem(self.item, self.entity)]

    def is_completed(self):
        return self.item_name in self.entity.creature.possessions

    def get_name(self):
        return 'have {0}'.format(self.item_name)

# class KnowWhereItemisLocated:
#     def __init__(self, item, entity):
#         self.item = item
#         self.entity = entity
#         self.behaviors_to_accomplish = [FindOutWhereItemIsLocated(self.item, self.entity)]
#
#     def is_completed(self):
#         return self.entity.creature.knowledge['objects'][self.item]['location']['accuracy'] == 1
#
#
# class HaveRoughIdeaOfLocation:
#     def __init__(self, item, entity):
#         self.item = item
#         self.entity = entity
#         self.behaviors_to_accomplish = []
#
#     def is_completed(self):
#         return self.entity.creature.knowledge['objects'][self.item]['location']['accuracy'] <= 2
#
# class HaveMoney:
#     def __init__(self, money, entity):
#         self.money = money
#         self.entity = entity
#         # Will be set if this status isn't already completed
#         self.behaviors_to_accomplish = [GetMoneyThroughWork(self.money, self.entity), StealMoney(self.money, self.entity)]
#
#     def is_completed(self):
#         return 1
#         #return self.entity.creature.gold >= self.money
#
#
# class HaveJob:
#     def __init__(self, entity):
#         self.entity = entity
#         # Will be set if this status isn't already completed
#         self.behaviors_to_accomplish = [GetJob(self.entity)]
#
#     def is_completed(self):
#         return self.entity.creature.profession


class AmAvailableToAct:
    def __init__(self, entity):
        self.entity = entity
        # Will be set if this status isn't already completed
        self.behaviors_to_accomplish = []

    def is_completed(self):
        return self.entity.creature.is_available_to_act()

    def get_name(self):
        return 'be available to act'


class ActionBase:
    ''' The base action class, providing some default methods for other actions '''
    def __init__(self):
        self.checked_for_movement = 0
        self.activated = 0

        self.costs = {'money':0, 'time':0, 'distance':0, 'morality':0, 'legality':0}

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]

    def get_repeats(self):
        return 1

    def get_behavior_location(self, current_location):
        return roll(0, 10), roll(0, 10)

    def activate(self):
        ''' Any specific behavior needed upon activating - will be overwritten if needed '''
        self.activated = 1



class BuyItem(ActionBase):
    def __init__(self, item_name, entity):
        ActionBase.__init__(self)
        self.item_name = item_name
        self.entity = entity
        self.preconditions = [HaveMoney(self.item_name, self.entity)]

        # Set in get_behavior_location()
        self.site = None

        self.costs['money'] += 50

    def get_behavior_location(self, current_location):
        ''' Find what cities sell the item we want, and then which of those cities is closest '''
        possible_cities = [city for city in g.WORLD.cities if self.item_name in city.object_to_agents_dict]

        closest_city, closest_dist = g.WORLD.get_closest_city(x=current_location[0], y=current_location[1], valid_cities=possible_cities)

        self.costs['distance'] += closest_dist
        self.costs['time'] += closest_dist

        self.site = closest_city

        return closest_city.x, closest_city.y

    def get_name(self):
        return 'buy {0}'.format(self.item_name)

    def take_behavior_action(self):

        target_agent = random.choice([agent for agent in self.site.econ.agents if agent.reaction.is_finished_good and self.item_name in agent.get_sold_objects()])
        self.entity.creature.buy_object(obj=self.item_name, sell_agent=target_agent, price=target_agent.perceived_values[target_agent.buy_economy][target_agent.sold_commodity_name].center, material=None, create_object=1)

        # print target_agent.name, 'just sold', self.item_name, 'to', self.entity.fulltitle(), 'for', target_agent.perceived_values[target_agent.finished_good.name].center
        #print '{0} just bought a {1}'.format(self.entity.fulltitle(), self.item_name)

    def is_completed(self):
        return 1



class MoveToLocation(ActionBase):
    ''' Specific behavior component for moving to an area.
    Will use road paths if moving from city to city '''
    def __init__(self, initial_location, target_location, entity, travel_verb='travel'):
        ActionBase.__init__(self)
        self.initial_location = initial_location
        self.target_location = target_location
        self.entity = entity
        self.travel_verb = travel_verb

        self.preconditions = [AmAvailableToAct(self.entity)]

        self.full_path = self.get_best_path(initial_location=self.initial_location, target_location=self.target_location)

        # Update the cost of this behavior
        self.costs['time'] += len(self.full_path)
        self.costs['distance'] += len(self.full_path)


    def get_name(self):
        goal_name = '{0} to {1}'.format(self.travel_verb, g.WORLD.tiles[self.target_location[0]][self.target_location[1]].get_location_description())
        return goal_name

    def is_completed(self):
        return (self.entity.wx, self.entity.wy) == self.target_location

    def activate(self):
        ''' On activation, must double check to make sure entity is still in the initial location -- if not, recalculate'''
        if (self.entity.wx, self.entity.wy) != self.initial_location:
            self.full_path = self.get_best_path(initial_location=(self.entity.wx, self.entity.wy), target_location=self.target_location)

        # Set the entity's brain to this path
        self.entity.world_brain.path = self.full_path
        self.activated = 1

    def take_behavior_action(self):
        # Don't take any action if no path has been set (e.g. we are already at the location we thought we needed to move to)
        if self.entity.world_brain.path:
            self.entity.w_move_along_path(path=self.entity.world_brain.path)

        elif self.full_path:
            print '{0} has no path to take, although the behavior has one!'.format(self.entity.fulltitle())
        elif self.full_path:
            print 'Both {0} and the behavior have no path to take!'.format(self.entity.fulltitle())

    def get_best_path(self, initial_location, target_location):
        ''' Find a path between 2 points, but take roads if both points happen to be cities '''
        target_site = g.WORLD.tiles[target_location[0]][target_location[1]].site
        current_site = g.WORLD.tiles[initial_location[0]][initial_location[1]].site

        if target_site in g.WORLD.cities and current_site in g.WORLD.cities and current_site != target_site:
            full_path = current_site.path_to[target_site][:]
        else:
            # Default - use libtcod's A* to create a path to destination
            libtcod.path_compute(p=g.WORLD.path_map, ox=initial_location[0], oy=initial_location[1], dx=target_location[0], dy=target_location[1])
            full_path = libtcod_path_to_list(path_map=g.WORLD.path_map)

        if not full_path:
            print '{0} -- has no full path to get from {1} to {2}'.format(self.entity.fulltitle(), self.initial_location, self.target_location)

        return full_path


class BringCommodityToLocation(ActionBase):
    def __init__(self, commodity, quantity, entity, target_location):
        ActionBase.__init__(self)
        self.commodity = commodity
        self.quantity = quantity
        self.entity = entity
        self.target_location = target_location

        self.preconditions = [HaveCommodity(commodity=self.commodity,  quantity=self.quantity, entity=self.entity)]

    def get_name(self):
        goal_name = 'bring {0} {1} to {2}'.format(self.quantity, self.commodity, g.WORLD.tiles[self.target_location[0]][self.target_location[1]].get_location_description())
        return goal_name

    def is_completed(self):
        return self.entity.creature.econ_inventory[self.commodity] >= self.quantity and (self.entity.wx, self.entity.wy) == self.target_location

    def get_behavior_location(self, current_location):
        return self.target_location

    def take_behavior_action(self):
        pass



class GatherCommodityBehavior(ActionBase):
    def __init__(self, commodity, quantity, entity):
        ActionBase.__init__(self)
        self.commodity = commodity
        self.quantity = quantity
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

        self.behavior_progress = 0
        # Time to gather 1 economy item is calculated based off of the weekly harvest yield specified in yaml
        self.time_to_gather = data.commodity_manager.get_days_to_harvest(resource_name=self.commodity)

    def get_name(self):
        goal_name = 'gather {0} {1}'.format(self.quantity, self.commodity)
        return goal_name

    def is_completed(self):
        return self.entity.creature.econ_inventory[self.commodity] >= self.quantity

    def get_behavior_location(self, current_location):
        # Will be the location of the closest resource for now - may take other things into account in the future
        _, closest_resource_location = g.WORLD.get_closest_resource(x=current_location[0], y=current_location[1], resource=self.commodity)

        if closest_resource_location is None:
            print self.entity.fullname(), 'at', current_location, 'going for', self.commodity, 'COULD NOT FIND CLOSEST'

        return closest_resource_location

    def take_behavior_action(self):
        ''' Increment progress counter, and gather resource if we've toiled long enough '''
        self.behavior_progress += 1
        if self.behavior_progress >= self.time_to_gather:
            self.entity.creature.econ_inventory[self.commodity] += 1
            self.behavior_progress = 0


class DoReaction(ActionBase):
    def __init__(self, commodity, quantity, entity):
        ActionBase.__init__(self)
        self.commodity = commodity
        self.quantity = quantity
        self.entity = entity

        # Store this reaction
        self.reaction = data.commodity_manager.reactions[commodity]
        self.consumed_in_this_reaction = {}
        self.number_of_reactions = int(ceil(quantity / self.reaction.output_amount))
        assert self.number_of_reactions > 0, self.number_of_reactions

        # Amount we need total for the reacion, accounting for the amount input / output quantities
        input_quantity =  self.number_of_reactions * self.reaction.input_amount
        self.preconditions = [HaveCommodity(commodity=self.reaction.input_commodity_name, quantity=input_quantity, entity=entity)]

        ## For consumed items, we mut have enough to fuel the entire reaction
        for commodity_type, quantity in self.reaction.commodities_consumed.iteritems():
            commodity = random.choice(data.commodity_manager.get_names_of_commodities_of_type(commodity_type=commodity_type))
            quantity_needed_for_this_goal = quantity * self.number_of_reactions
            self.consumed_in_this_reaction[commodity] = quantity_needed_for_this_goal
            self.preconditions.append(HaveCommodity(commodity=commodity, quantity=quantity_needed_for_this_goal, entity=entity))

        ## For required items, just having the # specified in the yaml is sufficient, and these do not get consumed in the reaction
        for commodity_type, quantity in self.reaction.commodities_required.iteritems():
            commodity = random.choice(data.commodity_manager.get_names_of_commodities_of_type(commodity_type=commodity_type))
            self.preconditions.append(HaveCommodity(commodity=commodity, quantity=quantity, entity=entity))

        self.behavior_progress = 0

        # Time to do 1 reaction is calculated based off of the weekly reaction yield specified in yaml
        self.days_of_reaction = int(ceil(7 / (quantity / self.reaction.output_amount) ))


    def get_name(self):
        goal_name = 'do reactions to create {0} {1}'.format(self.quantity, self.commodity)
        return goal_name

    def is_completed(self):
        return self.entity.creature.econ_inventory[self.commodity] >= self.quantity

    def get_behavior_location(self, current_location):
        # Does not need to be done at particular location for now
        return current_location

    def take_behavior_action(self):
        ''' Increment progress counter, and do reaction if we've toiled long enough '''
        self.behavior_progress += 1
        if self.behavior_progress >= self.days_of_reaction:

            self.entity.creature.econ_inventory[self.commodity] += (self.number_of_reactions * self.reaction.output_amount)

            self.entity.creature.econ_inventory[self.reaction.input_commodity_name] -= (self.number_of_reactions * self.reaction.input_amount)
            assert self.entity.creature.econ_inventory[self.reaction.input_commodity_name] >= 0, \
                                                        '{0}\'s inventory of {1} was {2} after doing reaction'.format(self.entity.fulltitle(),
                                                        self.reaction.input_commodity_name, self.entity.creature.econ_inventory[self.reaction.input_commodity_name])

            for commodity, quantity_needed_for_this_goal in self.consumed_in_this_reaction.iteritems():
                self.entity.creature.econ_inventory[commodity] -= quantity_needed_for_this_goal
                assert self.entity.creature.econ_inventory[commodity] >= 0, '{0}\'s inventory of {1} was {2} after doing reaction'.format(self.entity.fulltitle(),
                                                                            commodity, self.entity.creature.econ_inventory[commodity])

            #g.game.add_message('{0} has created {1} {2} (originally needed {3}'.format(self.entity.fulltitle(), self.number_of_reactions * self.reaction.output_amount, self.commodity, self.quantity), libtcod.red)
            #g.game.add_message(' - {0}: {1}, {2}: {3}'.format(self.commodity, self.entity.creature.econ_inventory[self.commodity],
            #                                                  self.reaction.input_commodity_name, self.entity.creature.econ_inventory[self.reaction.input_commodity_name]), libtcod.dark_red)
            self.behavior_progress = 0

class SetupWaitBehavior(ActionBase):
    ''' Used when the end goal of an entity is simply to be in an area, due to an issue using the AtLocation state directly as an end goal '''
    def __init__(self, target_location, entity):
        ActionBase.__init__(self)
        self.target_location = target_location
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

    def get_name(self):
        goal_name = 'spend some time at {0}'.format(self.target_location)
        return goal_name

    def is_completed(self):
        return 1 # Always true, so that as soon as this behavior is launched we can move on (with the auto-generated MoveToLocation behavior)

    def get_behavior_location(self, current_location):
        return self.target_location

    def take_behavior_action(self):
        pass  # No behavior needed here -


class UnloadGoodsBehavior(ActionBase):
    def __init__(self, target_city, entity):
        ActionBase.__init__(self)
        self.target_city = target_city
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

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
        self.target_city = target_city
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

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



def find_actions_leading_to_goals(goal_states, action_path, all_possible_paths):
    ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal. This
    function will drill down, checking behavior options and goal states, and return all valid paths to that goal that it can find.

    :param goal_states: <list> containing <any of the GoalStates defined in this module> - The state of the world that the goal seeker would like to change
    :param action_path: <list> contianing the current sequence of <ActionBase> behaviors to accomplish the goal - since the function is recursive, it grows on each call
    :param all_possible_paths: <list> containing sequences of <ActionBase> behaviors which have reached a valid conclusion (e.g. they have drilled down to states with no unmet conditions)
    :return: a <list> containing <lists> of behavior sequences which have reached a valid conclusion
    '''
    # TODO - using pop(0) is inefficient, consider using deques rather than lists throughout the function

    # Pop the first goal in the stack to evaluate
    goal_state = goal_states.pop(0)

    # Loop through each behavior option. These are different possibilities for how a goal can be completed, meaning
    # there may be multiple valid paths an agent can take to reach a goal
    for behavior_option in goal_state.behaviors_to_accomplish:
        # Find goal states which need to be accomplished for the behavior to be valid. Then add the current set of goal
        # states to the end of this list - ensuring that these sub-goals get evaluated first
        unmet_goal_states = behavior_option.get_unmet_conditions()
        unmet_goal_states.extend(goal_states)

        # The new action path is the old action path with the new one inserted at the beginning
        current_action_path = [behavior_option] + action_path  # TODO - this is making a copy of the list each time - evaluate if needed

        # If there are unment goal states (either as prerequisites to this behavior, or "left over" from previous calls
        # of this function, recursively call this function to find valid behavior paths.
        if unmet_goal_states:
            find_actions_leading_to_goals(goal_states=unmet_goal_states, action_path=current_action_path, all_possible_paths=all_possible_paths)

        # If all conditions are met, then this behavior can be accomplished, so the current set of behavior paths get
        # added to the master list of valid behavior paths to reach this goal
        elif not unmet_goal_states:
            all_possible_paths.append(current_action_path)

    return all_possible_paths



# def find_actions_leading_to_goal(goal_state, other_goals, action_path, all_possible_paths):
#     # Loop through each behavior option. These are different possibilities
#     for behavior_option in goal_state.behaviors_to_accomplish:
#         unmet_conditions = behavior_option.get_unmet_conditions()
#         current_action_path = [behavior_option] + action_path # Copy of the new behavior + action_path
#
#         if unmet_conditions:
#             main_goal = unmet_conditions.pop(0)
#             find_actions_leading_to_goal(goal_state=main_goal, other_goals=unmet_conditions, action_path=current_action_path, all_possible_paths=all_possible_paths)
#
#         # If there are other goals, we can pop that into the goal slot
#         elif (not unmet_conditions) and other_goals:
#             main_goal = other_goals.pop(0)
#             find_actions_leading_to_goal(goal_state=main_goal, other_goals=other_goals, action_path=current_action_path, all_possible_paths=all_possible_paths)
#
#         # If all conditions are met, then this behavior can be accomplished, so it gets added to the list
#         elif (not unmet_conditions) and (not other_goals):
#             all_possible_paths.append(current_action_path)
#
#     return all_possible_paths


# def find_actions_leading_to_goal(goal_state, action_path, all_possible_paths):
#     ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal '''
#     #print ' --- ', r_level, goal_state.status, [a.behavior for a in action_list], ' --- '
#
#     for behavior_option in goal_state.behaviors_to_accomplish:
#         unmet_conditions = behavior_option.get_unmet_conditions()
#         current_action_path = [behavior_option] + action_path # Copy of the new behavior + action_path
#
#         # If there are conditions that need to be met, then we find the actions that can be taken to complete each of them
#         for condition in unmet_conditions:
#             # print condition.get_name()
#             test = find_actions_leading_to_goal(goal_state=condition, action_path=current_action_path, all_possible_paths=all_possible_paths)
#             # for b_list in test:
#             #     print [b.get_name() for b in b_list]
#             # print ''
#
#         # If all conditions are met, then this behavior can be accomplished, so it gets added to the list
#         if not unmet_conditions:
#             all_possible_paths.append(current_action_path)
#
#     return all_possible_paths


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
    ''' Given a list of behavior lists, calculate the associated costs associated with each behavior list'''
    all_behaviors_costed = []

    for behavior_list in behavior_lists:
        total_costs = defaultdict(int)
        # Cost each aspect (time, distance, etc...) of each behavior
        for behavior in behavior_list:
            for aspect, cost in behavior.costs.iteritems():
                total_costs[aspect] += cost

        all_behaviors_costed.append((behavior_list, total_costs))

    return all_behaviors_costed



def get_costed_behavior_paths(goal_state, entity):
    ''' Find a set of behavior paths to get to a goal, insert any required movements, cost the resulting behavior lists, and return the costed lists '''
    # Find possible actions that can be taken to get there
    all_possible_behavior_paths = find_actions_leading_to_goals(goal_states=[goal_state], action_path=[], all_possible_paths=[])

    # Account for movement (eventually, account for movement subtrees?)
    behavior_list_including_movement = check_paths_for_movement(entity=entity, behavior_lists=all_possible_behavior_paths)

    ## DEBUG PRINT GOAL PATHS
    # if 'load' not in goal_state.get_name():
    #     print goal_state.get_name()
    #     for path in behavior_list_including_movement:
    #         print [b.get_name() for b in path]
    #     print ''

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