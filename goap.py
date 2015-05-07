from __future__ import division
from collections import namedtuple



class TestCreature:
    def __init__(self):
        self.possessions = set([])
        self.gold = 10
        self.profession = None

class TestEntity:
    def __init__(self):
        self.creature = TestCreature()




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
        #return self.entity.creature.is_available_to_act()
        return 1

    def set_behaviors_to_accomplish(self):
        self.behaviors_to_accomplish = []
        return self.behaviors_to_accomplish



class GetJob:
    def __init__(self, entity):
        self.behavior = 'get_job'
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]


class GetMoneyThroughWork:
    def __init__(self, money, entity):
        self.behavior = 'get_money_through_work'
        self.money = money
        self.entity = entity

        self.preconditions = [HaveJob(self.entity)]

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]


class StealMoney:
    def __init__(self, money, entity):
        self.behavior = 'steal_money'
        self.money = money
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]


class BuyItem:
    def __init__(self, item, entity):
        self.behavior = 'buy_item'
        self.item = item
        self.entity = entity

        self.preconditions = [HaveMoney(self.item, self.entity)]

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]


class StealItem:
    def __init__(self, item, entity):
        self.behavior = 'steal_item'
        self.item = item
        self.entity = entity

        self.preconditions = [AmAvailableToAct(self.entity)]

    def get_unmet_conditions(self):
        return [precondition for precondition in self.preconditions if not precondition.is_completed()]



def find_all_paths(goal_state):

    all_possible_paths = []

    # Start by finding which behaviors we can take to accomplish the goal
    goal_state.set_behaviors_to_accomplish()
    tmp_paths = [[behavior] for behavior in goal_state.behaviors_to_accomplish]

    while tmp_paths:
        # The goal is to build an end-to-end path of behaviors
        for i, path in enumerate(tmp_paths[:]):
            first_path_iteration = 0

            last_behavior = path[-1]
            unmet_preconditions = last_behavior.get_unmet_conditions()

            # If no unmet preconditions, we've found a complete behavior!
            if not unmet_preconditions:
                # Make sure to remove from tmp_paths
                tmp_paths.remove(path)
                all_possible_paths.append(path)
                break

            # Otherwise, go through all the
            for condition in unmet_preconditions:
                for behavior_option in condition.set_behaviors_to_accomplish():
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


test_entity = TestEntity()

all_possible_paths = find_all_paths(goal_state=HaveItem(item='cheese', entity=test_entity))
print '\n === Paths === \n'
for p in all_possible_paths:
    print [g.behavior for g in p]


