from __future__ import division
from math import ceil

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
        self.behaviors_to_accomplish = [FindOutWhereItemIsLocated(self.item, self.entity), SearchForItem(self.item, self.entity)]
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




def find_actions(goal_state, action_list, r_level):
    ''' Recursive function to find all possible behaviors which can be undertaken to get to a particular goal '''
    #print ' --- ', r_level, goal_state.status, [a.behavior for a in action_list], ' --- '
    for behavior_option in goal_state.set_behaviors_to_accomplish():
        unmet_conditions = behavior_option.get_unmet_conditions()

        # If there are conditions that need to be met, then we find the actions that can be taken to complete each of them
        if unmet_conditions:
            for condition in unmet_conditions:
                find_actions(goal_state=condition, action_list=action_list + [behavior_option], r_level=r_level+1)

        # If all conditions are met, then this behavior can be accomplished, so it gets added to the list
        elif not unmet_conditions:
            path_list.append(action_list + [behavior_option])


path_list = []
action_list = []

test_entity = TestEntity()
find_actions(goal_state=HaveItem(item=GOAL_ITEM, entity=test_entity), action_list=action_list, r_level=0)
for p in path_list:
    print [b.behavior for b in p]



# test_entity = TestEntity()
#
# all_possible_paths = find_all_paths(goal_state=HaveItem(item=GOAL_ITEM, entity=test_entity))
# print '\n === Paths === \n'
# for p in all_possible_paths:
#     print [g.behavior for g in p]

# print test_entity.creature.knowledge['objects'][GOAL_ITEM]['location']['accuracy']
