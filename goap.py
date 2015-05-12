from __future__ import division
from math import ceil
from random import randint as roll

from helpers import infinite_defaultdict


GOAL_ITEM = 'cheese'



class TestCreature:
    def __init__(self):
        self.possessions = set([])
        self.gold = 10
        self.profession = None

        self.knowledge = infinite_defaultdict()
        self.knowledge['objects'][GOAL_ITEM]['location']['accuracy'] = 2

    def is_available_to_act(self):
        return 1

class TestEntity:
    def __init__(self):
        self.creature = TestCreature()

        self.wx = 10
        self.wy = 10




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
    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]

    def get_repeats(self):
        return 1

    def get_possible_locations(self):
        return [(roll(0, 10), roll(0, 10))]

    def choose_location(self):
        return roll(0, 10), roll(0, 10)


class FindOutWhereItemIsLocated(ActionBase):
    def __init__(self, item, entity):
        self.behavior = 'find_out_where_item_is_located'
        self.item = item
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]


class SearchForItem(ActionBase):
    def __init__(self, item, entity):
        self.behavior = 'search_for_item'
        self.item = item
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity), HaveRoughIdeaOfLocation(self.item, self.entity)]


class GetJob(ActionBase):
    def __init__(self, entity):
        self.behavior = 'get_job'
        self.entity = entity
        self.preconditions = [AmAvailableToAct(self.entity)]


class GetMoneyThroughWork(ActionBase):
    def __init__(self, money, entity):
        self.behavior = 'get_money_through_work'
        self.money = money
        self.entity = entity
        self.preconditions = [HaveJob(self.entity)]

    def get_repeats(self):
        return ceil(self.money / self.entity.profession.monthly_pay)

    def get_behavior_location(self):
        return self.entity.profession.current_work_building.site.x, self.entity.profession.current_work_building.site.y

    def is_at_location(self):
        return (self.entity.wx, self.entity.wy) == self.get_behavior_location()


class StealMoney(ActionBase):
    def __init__(self, money, entity):
        self.behavior = 'steal_money'
        self.money = money
        self.entity = entity
        self.preconditions = [AmAvailableToAct(self.entity)]


class BuyItem(ActionBase):
    def __init__(self, item, entity):
        self.behavior = 'buy_item'
        self.item = item
        self.entity = entity
        self.preconditions = [HaveMoney(self.item, self.entity)]


class StealItem(ActionBase):
    def __init__(self, item, entity):
        self.behavior = 'steal_item'
        self.item = item
        self.entity = entity
        self.preconditions = [KnowWhereItemisLocated(self.item, self.entity), AmAvailableToAct(self.entity)]




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

    return all_possible_paths


def check_movement_required_by_possible_action_paths(entity, all_possible_paths):
    ''' Check all possible behavior paths for necessary movement, and extend the behavior paths if movement is required '''
    all_possible_paths_worked = []

    for path in all_possible_paths:
        path_worked = []
        current_location = (entity.wx, entity.wy)

        for behavior in path:
            # If we don't need to move, then we just append the existing behavior
            if current_location in behavior.get_possible_locations():
                path_worked.append(behavior)

            else:
                current_location = behavior.choose_location()
                path_worked.extend(['move to {0}'.format(current_location), behavior])

        all_possible_paths_worked.append(path_worked)

    return all_possible_paths_worked




test_entity = TestEntity()
path_list = find_actions_leading_to_goal(goal_state=HaveItem(item=GOAL_ITEM, entity=test_entity), action_path=[], all_possible_paths=[])
#for p in path_list:
#    print [b.behavior for b in p]


all_worked_paths = check_movement_required_by_possible_action_paths(entity=test_entity, all_possible_paths=path_list)
for p in all_worked_paths:
    print [b for b in p]
