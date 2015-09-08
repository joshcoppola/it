from __future__ import division
import random
from random import randint as roll
#import cProfile
#import pstats
import os
import yaml
from collections import defaultdict

from it import Profession
import data_importer as data

try:
    import matplotlib.pyplot as plt
except:
    print 'Can\'t load matplotlib - no access to graphs'


HIST_WINDOW_SIZE = 5 # Amount of trades auctions keep in memory to determine avg price (used by agents)
MAX_INVENTORY_SIZE = 15 # A not-really-enforced max inventory limit

PROFIT_MARGIN = 1.1 # Won't sell an item for lower than this * normalized production cost

# How much gold each agent starts with
RESOURCE_GATHERER_STARTING_GOLD = 100000
GOOD_PRODUCER_STARTING_GOLD = 150000
MERCHANT_STARTING_GOLD = 1000000

PREFERRED_ITEM_MIN_GOLD = 100000

MIN_CERTAINTY_VALUE = 2 ## Within what range traders are limited to estimating the market price
BID_REJECTED_ADJUSTMENT = 5 # Adjust prices by this much when our bid is rejected
ASK_REJECTED_ADJUSTMENT = 5 # Adjust prices by this much when nobody buys our stuff
REJECTED_UNCERTAINTY_AMOUNT = 2 # We get this much more uncertain about a price when an offer is rejected
ACCEPTED_CERTAINTY_AMOUNT = 2  # Out uncertainty about a price decreases by this amount when an offer is accepted

MAX_UNCERTAINTY_PERCENT = .25 # Uncertainty maxes out this percentage of the average price (.35 means  avg price - 35% to avg price + 35%)

P_DIF_ADJ = 3  # When offer is accepted and exceeds what we thought the price value was, adjust it upward by this amount
N_DIF_ADJ = 3  # When offer is accepted and is lower than what we thought the price value was, adjust it downward by this amount
P_DIF_THRESH = 2.5  #Threshhold at which adjustment of P_DIF_ADJ is added to the perceived value of a commodity
N_DIF_THRESH = 2.5 #Threshhold at which adjustment of P_DIF_ADJ is subtracted from the perceived value of a commodity

START_VAL = 40 # Arbitrary value that sets the starting price of good (in gold)
START_UNCERT = 10 # Arbitrary uncertainty value (agent believes price is somewhere between (mean-this, mean+this)

FOOD_BID_THRESHHOLD = 4 # Will bid on food when lower than this amount
GRANARY_THRESH = 5 # # of turns before we can get free food from the granary
STARVATION_THRESH = 10 # # of turns before we starve
########################### New stuff ###########################

plot_colors = {'food':(.3, .8, .3), 'flax':(1, .5, 1), 'clay':(.25, 0, .5), 'wood':(.2, .2, .8),
               'flax clothing':(1, .2, 1), 'clay pottery':(.3, .1, .6), 'wood furniture':(.1, .1, 1),

               'copper':(.9, .5, .1), 'bronze':(0, .5, .5), 'iron':(.3, .3, .3),
               'copper tools':(.7, .3, 0), 'bronze tools':(.1, .6, .6), 'iron tools':(.1, .1, .1),
               'copper weapons':(.9, .5, .2), 'bronze weapons':(.1, .8, .8), 'iron weapons':(.7, .7, .7),
               'copper armor':(.5, .1, 0), 'bronze armor':(.3, 1, 1), 'iron armor':(0, 0, 0)}





def economy_test_run():
    native_resources = [resource.name for resource in data.commodity_manager.resources]
    print native_resources
    economy = Economy(native_resources=native_resources, local_taxes=5, owner=None)

    for i in xrange(6):
        for resource in data.commodity_manager.resources:
            if resource.name != 'food' and resource.name != 'flax':
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
            elif resource.name == 'flax':
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
            else: # Add lots of farmers
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)
                economy.add_agent_based_on_token(resource.name)

    for i in xrange(4):
        for good in data.commodity_manager.goods:
            if good.name == 'flax clothing':
                economy.add_agent_based_on_token(good.name)
                economy.add_agent_based_on_token(good.name)
                economy.add_agent_based_on_token(good.name)
            else:
                economy.add_agent_based_on_token(good.name)
                economy.add_agent_based_on_token(good.name)

    for i in xrange(20):
        #print '------------', i, '--------------'
        economy.run_simulation()

    for token, auction in economy.auctions.iteritems():
        print token, auction.price_history

    print economy.get_valid_agent_types()


def check_strategic_resources(nearby_resources):
    # Checks a set of resources to see if there's enough types of strategic resources
    unavailable_types = []
    for resource_type, resource_token_list in data.commodity_manager.strategic_types.iteritems():
        has_token = False
        for resource_token in resource_token_list:
            if resource_token.name in nearby_resources:
                has_token = True
                break
        if not has_token:
            unavailable_types.append(resource_type)
    return unavailable_types

def list_goods_from_strategic(strategic_resources):
    goods_we_can_make = []

    goods_by_resource_token = data.commodity_manager.get_goods_by_resource_token()

    for resource in strategic_resources:
        if resource in goods_by_resource_token:
            for good_class in goods_by_resource_token[resource]:
                goods_we_can_make.append(good_class.name)
    return goods_we_can_make


class PriceBelief:
    def __init__(self, center, uncertainty):
        self.center = center
        self.uncertainty = uncertainty


class Agent(object):
    def __init__(self, id_, name, type_, population_number, buy_economy, sell_economy, sold_commodity_name, sold_commodity_type, is_merchant=0, attached_to=None):
        self.id_ = id_
        self.name = name
        self.type_ = type_
        self.population_number = population_number

        self.buy_economy = buy_economy
        self.sell_economy = sell_economy

        self.sold_commodity_name = sold_commodity_name
        self.sold_commodity_type = sold_commodity_type

        self.reaction = data.commodity_manager.reactions[sold_commodity_name]

        self.is_merchant = is_merchant

        self.attached_to = attached_to
        if self.attached_to is not None:
            self.attached_to.creature.economy_agent = self

        self.turns_alive = 0
        self.buys = 0
        self.sells = 0

        self.gold = GOOD_PRODUCER_STARTING_GOLD

        self.buy_inventory = {commodity: 0 for commodity in data.commodity_manager.all_commodity_names}
        self.sell_inventory = {commodity: 0 for commodity in data.commodity_manager.all_commodity_names}

        self.merchant_travel_inventory = defaultdict(int)

        self.inventory_size = 20 * self.population_number ## TODO - evaluate

        self.last_turn = []


        self.activity_is_blocked = 0

        self.current_location = buy_economy
        self.linked_economy_building = None

        self.time_here = roll(0, 3)
        self.cycle_length = 4


        ## ============ TODO - clean up ++++++++++++ ##
        self.perceived_values = {}

        self.perceived_values[self.buy_economy] = {sold_commodity_name:PriceBelief(START_VAL, START_UNCERT)}

        for token_of_commodity in data.commodity_manager.all_commodity_names:
            self.perceived_values[self.buy_economy][token_of_commodity]  = PriceBelief(START_VAL, START_UNCERT)

        if self.is_merchant:
            self.perceived_values[self.sell_economy] = {sold_commodity_name:PriceBelief(START_VAL, START_UNCERT)}

            for token_of_commodity in data.commodity_manager.all_commodity_names:
                self.perceived_values[self.sell_economy][token_of_commodity] = PriceBelief(START_VAL, START_UNCERT)


        self.sell_inventory[self.sold_commodity_name] = 2 * self.population_number
        self.buy_inventory['food'] = self.population_number * roll(2, 5)

        self.buy_inventory['flax clothing'] = self.population_number * roll(0, 2)
        self.buy_inventory['wood furniture'] = self.population_number * roll(0, 2)

        self.buy_inventory['iron tools'] = self.population_number * roll(0, 2)


        self.future_bids = {}
        self.future_sells = {}

    def update_holder(self, figure):
        '''If the original holder we're attached to dies, we can be passed on to others'''
        # Remove self from who we were previously attached to
        if self.attached_to is not None:
            self.attached_to.creature.economy_agent = None


        if figure.creature.economy_agent is not None:
            figure.creature.economy_agent.attached_to = None
            figure.creature.economy_agent = None

        self.attached_to = figure
        self.attached_to.creature.economy_agent = self

    def adjust_gold(self, amount):
        self.gold += amount
        if self.attached_to:
            self.attached_to.creature.net_money += amount

    def take_bought_commodity(self, commodity, amount):
        self.buy_inventory[commodity] += amount

    def remove_sold_commodity(self, commodity, amount):
        self.sell_inventory[commodity] -= amount


    def increment_cycle(self):
        self.time_here += 1
        destination = None
        ## if it's part of the game, add to a list of departing merchants so they can create a caravan
        if self.time_here >= 2 and self.current_location.owner:
            if self.current_location == self.buy_economy and self.buy_inventory[self.sold_commodity_name] >= 2 * self.population_number:
                destination = self.sell_economy.owner

                amount = self.buy_inventory[self.sold_commodity_name]
                self.buy_inventory[self.sold_commodity_name] -= amount
                self.merchant_travel_inventory[self.sold_commodity_name] += amount

            elif self.current_location == self.sell_economy:
                destination = self.buy_economy.owner

            if destination:
                # Add to list of departing merchants
                self.current_location.owner.departing_merchants.append((self.attached_to, destination))
                self.current_location = None

        # Catch for when the script is run standalone, where it doesn't have a city it's attached to
        else:
            if self.current_location == self.buy_economy:    self.current_location = self.sell_economy
            elif self.current_location == self.sell_economy: self.current_location = self.buy_economy

    def pay_taxes(self, economy):
        # Pay taxes. If the economy has an owner, pay the taxes to that treasury
        self.gold -= economy.local_taxes
        # economy owner - should be the city
        if economy.owner:
            economy.owner.treasury += economy.local_taxes

    def has_token(self, type_of_commodity):
        # Test whether or not we have a token of an commodity
        for token_of_commodity in data.commodity_manager.get_names_of_commodities_of_type(type_of_commodity):
            if self.buy_inventory[token_of_commodity]:
                return True
        return False

    def get_all_commodities_of_type(self, type_of_commodity, inventory):
        ''' Return a dict of all commodities in our inventory which match the type of commodity '''
        matching_commodities = defaultdict(int)

        for token_of_commodity in data.commodity_manager.get_names_of_commodities_of_type(type_of_commodity):
            if token_of_commodity in inventory and inventory[token_of_commodity] > 0:
                matching_commodities[token_of_commodity] = inventory[token_of_commodity]

        return matching_commodities

    # def starve(self):
    #     '''What happens when we run out of food'''
    #     self.buy_economy.buy_merchants.remove(self)
    #     self.sell_economy.sell_merchants.remove(self)
    #     if self.buy_economy.owner: self.buy_economy.owner.former_agents.append(self)


    def find_token_and_place_bid(self, economy, type_of_commodity):
        token_to_bid = random.choice(self.buy_economy.available_types[type_of_commodity])

        self.place_bid(economy=economy, token_to_bid=token_to_bid)

    def place_bid(self, economy, token_to_bid):
        ## Place a bid in the economy
        est_price = self.perceived_values[economy][token_to_bid].center
        uncertainty = self.perceived_values[economy][token_to_bid].uncertainty

        bid_price = roll(est_price - uncertainty, est_price + uncertainty)


        if self.is_merchant and token_to_bid == self.sold_commodity_name:
            quantity = self.inventory_size - (sum(self.buy_inventory.values()) + 1)
        else:
            quantity = roll(1, 2) * self.population_number
        #print self.name, 'bidding on', quantity, token_to_bid, 'for', bid_price, 'at', self.current_location.owner.name
        #print self.name, 'bidding for', quantity, token_to_bid
        if quantity > 0:
            self.last_turn.append('Bid on {0} {1} for {2}'.format(quantity, token_to_bid, bid_price))
            economy.auctions[token_to_bid].bids.append(Offer(owner=self, commodity=token_to_bid, price=bid_price, quantity=quantity))

            #print '{0} offered to buy {1} {2} at {3}'.format(self.name, quantity, token_to_bid, bid_price)
        else:
            self.last_turn.append('Tried to bid on {0} but quantity not > 0'.format(token_to_bid))
            #print '{0} tried to bid on {1} {2} at {3}'.format(self.name, quantity, token_to_bid, bid_price)

    def create_sell(self, economy, sell_commodity):
        # Determines how many commoditys to sell, and at what cost
        # production_cost = self.check_min_sell_price()
        # min_sale_price = int(round( production_cost*PROFIT_MARGIN ) )
        #
        # est_price = self.sell_perceived_values[sell_commodity].center
        # uncertainty = self.sell_perceived_values[sell_commodity].uncertainty
        # # won't go below what they paid for it
        # sell_price = max(roll(est_price - uncertainty, est_price + uncertainty), min_sale_price)

        est_price = self.perceived_values[self.sell_economy][sell_commodity].center
        uncertainty = self.perceived_values[self.sell_economy][sell_commodity].uncertainty
        sell_price = roll(est_price - uncertainty, est_price + uncertainty)

        quantity_to_sell = self.sell_inventory[sell_commodity]
        #print self.name, 'selling', quantity_to_sell, sell_commodity
        if quantity_to_sell > 0:
            #print self.name, 'selling', quantity_to_sell, sell_commodity, 'for', sell_price, 'at', self.current_location.owner.name
            self.last_turn.append('Offered to sell {0} {1} for {2}'.format(quantity_to_sell, sell_commodity, sell_price))
            economy.auctions[sell_commodity].sells.append( Offer(owner=self, commodity=sell_commodity, price=sell_price, quantity=quantity_to_sell) )

            #print '{0} offered to sell {1} {2} at {3}'.format(self.name, quantity_to_sell, self.sold_commodity_name, sell_price)
        else:
            self.last_turn.append('Tried to sell {0} but inventory was empty'.format(sell_commodity))
            #print '{0} did not have any {1} to sell'.format(self.name, self.sold_commodity_name)


    def eval_trade_accepted(self, economy, type_of_commodity, price):
        # Then, adjust our belief in the price
        if self.perceived_values[economy][type_of_commodity].uncertainty >= MIN_CERTAINTY_VALUE:
            self.perceived_values[economy][type_of_commodity].uncertainty -= ACCEPTED_CERTAINTY_AMOUNT

        our_mean = (self.perceived_values[economy][type_of_commodity].center)

        if price > our_mean * P_DIF_THRESH:
            self.perceived_values[economy][type_of_commodity].center += P_DIF_ADJ
        elif price < our_mean * N_DIF_THRESH:
            # We never let it's worth drop under a certain % of tax money.
            self.perceived_values[economy][type_of_commodity].center = \
                max(self.perceived_values[economy][type_of_commodity].center - N_DIF_ADJ, (self.buy_economy.local_taxes) + self.perceived_values[economy][type_of_commodity].uncertainty)


    def adjust_uncertainty(self, economy, type_of_commodity):
        ''' Ensures that the uncertainty value is never adjusted to be too wide '''
        uncertainty_limit = int(max(economy.auctions[type_of_commodity].mean_price * MAX_UNCERTAINTY_PERCENT, 1))
        self.perceived_values[economy][type_of_commodity].uncertainty = min(self.perceived_values[economy][type_of_commodity].uncertainty + REJECTED_UNCERTAINTY_AMOUNT, uncertainty_limit)


    def eval_bid_rejected(self, economy, type_of_commodity, price=None):
        # What to do when we've bid on something and didn't get it
        if economy.auctions[type_of_commodity].supply:
            if price is None:
                self.perceived_values[economy][type_of_commodity].center += BID_REJECTED_ADJUSTMENT
                self.adjust_uncertainty(economy, type_of_commodity)
            else:
                # Radical re-evaluation of the price
                self.perceived_values[economy][type_of_commodity].center = price + self.perceived_values[economy][type_of_commodity].uncertainty
                self.adjust_uncertainty(economy, type_of_commodity)


    def produce_sold_commodity(self):
        # Gather resources, consume commodities, and account for breaking stuff

        # Check how many raw resources of input we have
        if self.reaction.commodity_input.items():
            input_commodity, input_amount = self.reaction.commodity_input.items()[0]
            available_reaction_amount = int(self.buy_inventory[input_commodity] / input_amount)

        # For raw goods producers
        else:
            available_reaction_amount = self.population_number

        # For every consumed commodity, check how many we have in inventory, and keep track of the minimum number of times
        # we can run the reaction
        for commodity_type, amount in self.reaction.commodities_consumed.iteritems():
            total_consumed_commodities = self.count_commodities_of_type(commodity_type, inventory=self.buy_inventory)
            available_reaction_amount = min(int(total_consumed_commodities / amount), available_reaction_amount)

        for commodity_type, amount in self.reaction.commodities_required.iteritems():
            total_required_commodities = self.count_commodities_of_type(commodity_type, inventory=self.buy_inventory)

            available_reaction_amount = min(int(total_required_commodities / amount), available_reaction_amount)

        ##### Run the reaction however many times we can #####
        if available_reaction_amount:
            print self.name, 'doing reaction', available_reaction_amount
            # Remove from buy inventory
            for commodity, amount_produced in self.reaction.commodity_input.iteritems():
                self.buy_inventory[commodity] -= amount_produced * available_reaction_amount

            # Also consume other needed goods

            for commodity_type, amount in self.reaction.commodities_consumed.iteritems():
                self.remove_commodities_of_type(type_of_commodity=commodity_type, inventory=self.buy_inventory, amount_to_remove=available_reaction_amount * amount)

            # Add to sell inventory
            for commodity_produced, multiplier in self.reaction.commodity_produced.iteritems():
                self.sell_inventory[commodity_produced] += available_reaction_amount * multiplier
        else:
            for commodity_produced, multiplier in self.reaction.commodity_produced.iteritems():
                self.sell_inventory[commodity_produced] += int(self.population_number / 5)
            print 'COULD NOT DO AVAILABLE REACTION'
        ########################################################


        ### ITEMS BREAKING - TODO - need to be set by actual values from data
        for commodity, amount in self.buy_inventory.iteritems():
            ## roll(1, 1000) <= data.commodity_manager.get_actual_commodity_from_name(token_of_commodity).break_chance
            # TODO - need to exclude unused production items
            self.buy_inventory[commodity] = max(self.buy_inventory[commodity] - roll(5, 10), 0)


        self.last_turn.append('Produced {0} reactions for {1}'.format(available_reaction_amount, self.sold_commodity_name))

        #print '{0} produced {1} reactions for {2}'.format(self.name, available_reaction_amount, self.sold_commodity_name)


    # def check_min_sell_price(self):
    #     production_cost = self.perceived_values[self.buy_economy][self.sold_commodity_name].center
    #     # These commodities are required for production, but not used. Find the item's cost * (break chance/1000) to find avg cost
    #     for type_of_commodity in self.consumed + self.essential + self.preferred:
    #         for token_of_commodity in data.commodity_manager.get_commodities_of_type(type_of_commodity):
    #             if self.buy_inventory[token_of_commodity]:
    #                 production_cost += int(round(self.buy_economy.auctions[token_of_commodity].mean_price * (data.commodity_manager.get_actual_commodity_from_name(token_of_commodity).break_chance/1000)))
    #                 break
    #     # Take into account the taxes we pay
    #     production_cost += self.buy_economy.local_taxes
    #     return production_cost


    def eval_sell_rejected(self, economy, type_of_commodity):
        # What to do when we put something up for sale and nobody bought it
        if economy.auctions[type_of_commodity].demand:
            # production_cost = self.check_min_sell_price()
            # min_sale_price = int(round(production_cost*PROFIT_MARGIN))

            #self.perceived_values[type_of_commodity].center = max(self.perceived_values[type_of_commodity].center - ASK_REJECTED_ADJUSTMENT, min_sale_price + self.perceived_values[type_of_commodity].uncertainty)
            self.perceived_values[economy][type_of_commodity].center -= ASK_REJECTED_ADJUSTMENT
            self.adjust_uncertainty(economy, type_of_commodity)


    def bankrupt(self):

        if self.is_merchant:
            self.gold += MERCHANT_STARTING_GOLD

        else:
            # print 'Removing {0} in {1}'.format(self.name, self.economy.owner.name)  ## DEBUG
            self.buy_economy.all_agents.remove(self)

            # Unset linked economy building from building list, if necessary
            ## TODO - Ensure that when the building is already generated, and when cities are saved / loaded, that the buildings open up for future use
            if self.linked_economy_building:
                self.buy_economy.owner.buildings.remove(self.linked_economy_building)
                self.linked_economy_building.linked_economy_agent = None
                self.linked_economy_building = None

            if self.buy_economy.owner:
                self.buy_economy.owner.former_agents.append(self)

            if self.attached_to is not None:
                self.attached_to.creature.economy_agent = None
                self.attached_to = None

                self.buy_economy.add_new_agent_to_economy()


    def get_sold_objects(self):
        ''' Return the names of the objects sold by this agent '''
        sold_objects = []
        if self.economy.owner:
            for obj in self.economy.owner.faction.unique_object_dict:
                for tag in self.economy.owner.faction.unique_object_dict[obj]['tags']:
                    if tag in data.AGENT_INFO['producers'][self.sold_commodity_name]['sold_object_tags']:
                        sold_objects.append(obj)
                        break

        return sold_objects


    def take_turn(self):
        self.last_turn = []

        if self.gold < 0:
            all_agents_of_this_type_in_this_economy = [a for a in self.buy_economy.all_agents if a.type_ == self.type_]

            if len(all_agents_of_this_type_in_this_economy) > 1:
                self.bankrupt()
                return
            elif len(all_agents_of_this_type_in_this_economy) == 1:
                # print 'bailing out {0} in {1}'.format(self.name, self.economy.owner.name)## DEBUG
                # Government bailout
                self.gold += 500

        if not self.activity_is_blocked:
            #self.check_production_ability() # <- will gather resources
            self.produce_sold_commodity()
            self.evauluate_needs_and_place_bids()
            #self.handle_bidding()
            self.pay_taxes(self.buy_economy)
            #self.handle_sells()
            self.create_sell(economy=self.sell_economy, sell_commodity=self.sold_commodity_name)
        self.turns_alive += 1

    def count_commodities_of_type(self, type_of_commodity, inventory):
        return sum(self.get_all_commodities_of_type(type_of_commodity=type_of_commodity, inventory=inventory).values())

    def remove_commodities_of_type(self, type_of_commodity, inventory, amount_to_remove):
        commodities = self.get_all_commodities_of_type(type_of_commodity=type_of_commodity, inventory=inventory)

        remaining_amount_to_remove = amount_to_remove
        for commodity_token, amount in commodities.iteritems():
            removed = min(remaining_amount_to_remove, amount)
            inventory[commodity_token] -=  removed

            remaining_amount_to_remove -= removed
            if remaining_amount_to_remove <= 0:
                break


    def evauluate_needs_and_place_bids(self):

        print self.name, 'evaluating'
        ## Eat food
        total_food_to_consume = self.population_number
        foods = self.get_all_commodities_of_type(type_of_commodity='foods', inventory=self.buy_inventory)
        #print foods, self.buy_inventory['food']
        #print ''
        for commodity, amount in foods.iteritems():
            consumed = min(amount, total_food_to_consume)
            self.buy_inventory[commodity] -= consumed
            # Adjust remaining food to consume and set breakpoint
            total_food_to_consume =- consumed
            if total_food_to_consume <= 0:
                break
        ########################

        if sum(self.get_all_commodities_of_type(type_of_commodity='foods', inventory=self.buy_inventory).values()) <= 2 * self.population_number:
            self.find_token_and_place_bid(economy=self.buy_economy, type_of_commodity='foods')

        # If there is an input to the reaction we generate, bid on it
        for commodity in self.reaction.commodity_input:
            self.place_bid(economy=self.buy_economy, token_to_bid=commodity)

        # TODO - needs to be smarter
        for commodity_type in self.reaction.commodities_consumed:
            commodity_token = random.choice(self.buy_economy.available_types[commodity_type])
            self.place_bid(economy=self.buy_economy, token_to_bid=commodity_token)

        # TODO - better
        self.place_bid(economy=self.buy_economy, token_to_bid=random.choice(self.buy_economy.available_types['furniture']))
        self.place_bid(economy=self.buy_economy, token_to_bid=random.choice(self.buy_economy.available_types['pottery']))

        # TODO - needs to be smarter
        #for commodity_type in self.reaction.commodities_required:
        #    if
        #    self.buy_economy.available_types[commodity_type]


    #def handle_bidding(self):
        #if self.future_bids == {}:
        # self.eval_need()

        # If we already have action queued ...
        #else:
        #    for token, [bid_price, bid_quantity] in self.future_bids.iteritems():
        #        self.place_bid(economy=self.buy_economy, token_to_bid=token, bid_price=bid_price, bid_quantity=bid_quantity)
        #    self.future_bids = {}


    #def handle_sells(self):
        #self.create_sell(economy=self.buy_economy, sell_commodity=self.sold_commodity_name)

        #else:
        #    for sell_commodity, (sell_price, quantity_to_sell) in self.future_sells.iteritems():
        #        self.create_sell(economy=self.buy_economy, sell_commodity=sell_commodity, sell_price=sell_price, quantity_to_sell=quantity_to_sell)
        #    self.future_sells = {}


    def player_auto_manage(self):
        tokens_to_bid = self.eval_need()

        for token in tokens_to_bid:
            bid_price, bid_quantity = self.eval_bid(token)
            self.future_bids[token] = [bid_price, bid_quantity]

        # Straight from food bidding code, except subtract one because we'll be consuming it next turn
        if self.need_food and self.inventory['food'] <= (FOOD_BID_THRESHHOLD * self.population_number):
            token = random.choice(self.economy.available_types['foods'])
            bid_price, bid_quantity = self.eval_bid(token)

            self.future_bids[token] = [bid_price, bid_quantity]

        sell_price, quantity_to_sell = self.check_sell()
        if quantity_to_sell > 0:
            self.future_sells[self.sold_commodity_name] = [sell_price, quantity_to_sell]


    #### For use with player only for now ####
    def change_bid_price(self, item_to_change, amt):
        ''' Change price of a future bid '''
        self.future_bids[item_to_change][0] = max(self.future_bids[item_to_change][0] + amt, 1)

    def change_bid_quant(self, item_to_change, amt):
        ''' Change quantity of a future bid '''
        self.future_bids[item_to_change][1] = max(self.future_bids[item_to_change][1] + amt, 1)

    def change_sell_price(self, item_to_change, amt):
        ''' Change price of a future sell offer '''
        self.future_sells[item_to_change][0] = max(self.future_sells[item_to_change][0] + amt, 1)

    def change_sell_quant(self, item_to_change, amt):
        ''' Change quantity of a future sell offer '''
        self.future_sells[item_to_change][1] = min( max(self.future_sells[item_to_change][1] + amt, 1), self.inventory[item_to_change] )
    ###########################################



class AuctionHouse:
    # Seperate "auction" for each commodity
    # Runs each round of bidding, as well as archives historical price info
    def __init__(self, economy, commodity):
        self.economy = economy
        self.commodity = commodity
        self.bids = []
        self.sells = []
        self.price_history = [START_VAL]
        # How many bids have existed each round
        self.bid_history = [0]
        # How many sells have existed each round
        self.sell_history= [0]

        self.mean_price = START_VAL
        self.iterations = 0

        self.supply = None
        self.demand = None

    def update_historical_data(self, mean_price, num_bids, num_sells):
        # Updates the history for this auction
        self.price_history.append(mean_price)
        self.bid_history.append(num_bids)
        self.sell_history.append(num_sells)

    def update_mean_price(self):
        # update the mean price for this commodity by averaging over the last HIST_WINDOW_SIZE items
        recent_prices = filter(lambda price: price is not None, self.price_history[-HIST_WINDOW_SIZE:])
        if recent_prices:
            self.mean_price = int(round(sum(recent_prices)/len(recent_prices)))

    def get_last_valid_price(self):
        # Naive way to get the last non-None price in our history
        for price in reversed(self.price_history):
            if price is not None:
                return price

    def check_auction_health(self):
        ''' Find how many times this item was requested, but was not available to buy '''
        # Get the most recent 10 entries of the auction
        recent_bids = self.bid_history[-10:]
        recent_bids.reverse()
        recent_sells = self.sell_history[-10:]
        recent_sells.reverse()

        num_times_commodity_not_present = 0
        for i, num_sells in enumerate(recent_sells):
            if num_sells == 0 and recent_bids[i] > 0:
                num_times_commodity_not_present += 1

        #if num_times_commodity_not_present > 0:
        #    print '{0}: {1} bid on in {2} out of 10 latest rounds, but was not available'.format(self.economy.owner.name, self.commodity, num_times_commodity_not_present)

class Offer:
    # An offer that goes into the auction's "bids" or "sells".
    # Bids and sells are then compared against each other and agents meet at the middle
    def __init__(self, owner, commodity, price, quantity):
        self.owner = owner
        self.commodity = commodity
        self.price = price
        self.quantity = quantity

class Economy:
    def __init__(self, native_resources, local_taxes, owner=None):
        self.native_resources = native_resources
        self.available_types = {}
        # Should be the city where this economy is located
        self.owner = owner

        # Agents belonging to this economy
        self.resource_gatherers = []
        self.good_producers = []
        self.buy_merchants = []
        self.sell_merchants = []

        self.all_agents = []

        self.starving_agents = []
        # Auctions that take place in this economy
        self.auctions = {}
        self.prices = {}

        # Amount of gold paid in taxes each turn
        self.local_taxes = local_taxes

        # Counter to be appended to agent names
        self.agent_num = 1

    def get_all_available_commodity_tokens(self):
        return [token for tokens in self.available_types.values() for token in tokens]

    def get_valid_agent_types(self):
        valid_types = [resource for resource in self.native_resources]

        valid_goods = list_goods_from_strategic(valid_types)

        return valid_types + valid_goods


    def add_commodity_to_economy(self, commodity):
        ''' Each commodity has an associated auction house, containing some price / bidding history '''
        category = data.commodity_manager.get_actual_commodity_from_name(commodity).category
        if category in self.available_types:
            if commodity not in self.available_types[category]:
                self.available_types[category].append(commodity)
                self.auctions[commodity] = AuctionHouse(economy=self, commodity=commodity)
        else:
            self.available_types[category] = [commodity]
            self.auctions[commodity] = AuctionHouse(economy=self, commodity=commodity)

    def add_new_agent_to_economy(self):
        ''' Flip between adding the most profitable commodity, or the most demanded commodity '''

        if roll(0, 1):
            token = self.find_most_profitable_agent_token(restrict_based_on_available_resource_slots=1)
            self.add_agent_based_on_token( token )
            # print 'Adding {0} in {1}'.format(token, self.economy.owner.name)## DEBUG
        else:
            token = self.find_most_demanded_commodity(restrict_based_on_available_resource_slots=1)
            self.add_agent_based_on_token( token )
            #print 'Adding {0} in {1}'.format(token, self.economy.owner.name)## DEBUG


    def add_random_agent(self):
        if roll(0, 1):
            commodity = random.choice(data.commodity_manager.resources)
            self.add_resource_gatherer(commodity.name)
        else:
            commodity = random.choice(data.commodity_manager.goods)
            self.add_good_producer(commodity.name)

    def add_merchant(self, sell_economy, traded_item, attached_to=None):
        name = '{0} merchant'.format(traded_item)

        merchant = Agent(id_=self.agent_num, name=name, type_='TEST TY{E', population_number=100, buy_economy=self, sell_economy=sell_economy, sold_commodity_name=traded_item, sold_commodity_type='TEST',
                         is_merchant=1, attached_to=attached_to)

        self.buy_merchants.append(merchant)
        sell_economy.sell_merchants.append(merchant)
        # Test if it's in the economy and add it if not
        self.add_commodity_to_economy(traded_item)
        sell_economy.add_commodity_to_economy(traded_item)

        self.agent_num += 1

        return merchant

    def add_agent_based_on_token(self, token):
        ''' If we only have a token and don't know whether it's a resource or a commodity,
        this function helps us figure out which method to call'''
        #if token in [r.name for r in data.commodity_manager.resources]:
        #    self.add_resource_gatherer(token)

        #elif token in [g.name for g in data.commodity_manager.goods]:
        #    self.add_good_producer(token)

        if token == 'food':
            population_number = 200
        if token in [r.name for r in data.commodity_manager.resources]:
            population_number = 100
        else:
            population_number = 20

        agent = Agent(id_=self.agent_num, name='{0} maker'.format(token), type_='TEST TY{E', population_number=population_number, buy_economy=self, sell_economy=self, sold_commodity_name=token, sold_commodity_type='TEST')

        self.agent_num += 1

        self.all_agents.append(agent)
        # Test if it's in the economy and add it if not
        self.add_commodity_to_economy(token)

        ###### IF RESOURCE GATHERER #############
        if token in [r.name for r in data.commodity_manager.resources]:
            ## Assign the agent to a physical slot somewhere by the city
            resource = 'land' if token == 'food' else token

            #print '----'
            for region in self.owner.territory:
                ## Special case - land!
                if resource == 'land' and region.has_open_slot('land'):
                    region.add_resource_gatherer_to_region(resource_name=resource, agent=agent)
                    return

                ## Main case - loop through all the resources in the rest of the tiles
                elif resource != 'land':
                    for tile_resource, amount in region.res.iteritems():
                        if resource == tile_resource and region.has_open_slot(resource):
                            region.add_resource_gatherer_to_region(resource_name=resource, agent=agent)
                            #print '{0} sucessfully added to {1}'.format(resource, self.owner.name)
                            return

            print 'ERROR - {0} was tried to be added to {1} and could not find open slot!!!!'.format(resource, self.owner.name)

        ###### IF GOOD PRODUCER #############
        elif token in [g.name for g in data.commodity_manager.goods]:
            if self.owner:
                building = self.owner.create_building(zone='industrial', type_='shop', template='TEST', professions=[Profession(name='{0} maker'.format(token), category='commoner')], inhabitants=[], tax_status='commoner')
                building.linked_economy_agent = agent
                agent.linked_economy_building = building


    def get_possible_resource_slots(self, restrict_based_on_available_resource_slots):
        ''' When dealing with economies attached to cities, we need to know whether, in the city's territory, there are
        available slots used to work a particular resource. This function returns a list of all available resources in
        a particular economy '''
        available_resources = []

        for region in self.owner.territory:
            ###### SPECIAL CASE - LAND IS NOT A NAMED RESOURCE #######
            if 'food' not in available_resources:
                if (not restrict_based_on_available_resource_slots) or (restrict_based_on_available_resource_slots and region.has_open_slot('land')):
                    available_resources.append('food')

            ##### Normal case - loop through each resource in the region and check whether it's been used yet, and whether there is capacity to add it #####
            for res, amount in region.res.iteritems():
                if res not in available_resources and amount:
                    if (not restrict_based_on_available_resource_slots) or (restrict_based_on_available_resource_slots and region.has_open_slot(resource_name=res)):
                        available_resources.append(res)

        return available_resources


    def find_most_profitable_agent_token(self, restrict_based_on_available_resource_slots):
        ### First build a dict of agents, their gold, and the # of agents
        # key = commodity, value = [gold, #_of_agents]
        available_resource_slots = self.get_possible_resource_slots(restrict_based_on_available_resource_slots=restrict_based_on_available_resource_slots)

        tokens_of_commodity = {}
        for agent in self.resource_gatherers:
            if agent.resource in available_resource_slots:
                if agent.resource in tokens_of_commodity:
                    tokens_of_commodity[agent.resource][0] += agent.gold
                    tokens_of_commodity[agent.resource][1] += 1
                else:
                    tokens_of_commodity[agent.resource] = [agent.gold, 1]

        for agent in self.good_producers:
            if agent.output in tokens_of_commodity:
                tokens_of_commodity[agent.output][0] += agent.gold
                tokens_of_commodity[agent.output][1] += 1
            else:
                tokens_of_commodity[agent.output] = [agent.gold, 1]

        ### Now choose the best one based off of the ratio of gold to agents
        best_ratio = 0
        best_commodity = None
        for commodity, [gold, agent_num] in tokens_of_commodity.iteritems():
            if gold/agent_num > best_ratio:
                best_commodity, best_ratio = commodity, gold/agent_num

        return best_commodity


    def find_most_demanded_commodity(self, restrict_based_on_available_resource_slots):

        available_resource_slots = self.get_possible_resource_slots(restrict_based_on_available_resource_slots=restrict_based_on_available_resource_slots)


        ### Find the item in highest demand
        greatest_demand_ratio = 0
        # Switched this to string, so that it can display in the city screen
        # TODO - find out why sometimes the answer is none!
        best_commodity = 'none'

        # Returns a list of valid commodities in this economy that can be used to create agents
        # For instance, copper miners won't be produced in a city with no access to copper
        for commodity in self.get_valid_agent_types():
            if (restrict_based_on_available_resource_slots and commodity in [r.name for r in data.commodity_manager.resources] and commodity in available_resource_slots) or not restrict_based_on_available_resource_slots:
                current_ratio = self.auctions[commodity].demand/ max(self.auctions[commodity].supply, 1) # no div/0
                if current_ratio > greatest_demand_ratio:
                    greatest_demand_ratio = current_ratio
                    best_commodity = commodity

        return best_commodity


    def find_least_demanded_commodity(self):
        ### Find the item in highest demand
        least_demand = 10000
        least_commodity = None

        for commodity, auction in self.auctions.iteritems():
            current = auction.demand # no div/0
            if current < least_demand:
                least_demand = current
                least_commodity = commodity

        return least_commodity


    def run_simulation(self):
        ''' Run a simulation '''
        # First, each agent does what they do
        # for resource_gatherer in self.resource_gatherers[:]:
        #     resource_gatherer.take_turn()
        #
        # for producer in self.good_producers[:]:
        #     producer.take_turn()
        for agent in self.all_agents:
            agent.take_turn()

        for merchant in self.buy_merchants[:]:
            merchant.last_turn = []
            #if merchant.current_location == self:
            if merchant.gold < 0:
                all_agents_of_this_type_in_this_economy = [a for a in merchant.buy_economy.buy_merchants if a.name == merchant.name]
                if len(all_agents_of_this_type_in_this_economy) > 1:
                    merchant.bankrupt()
                else:
                    # Government bailout
                    merchant.gold += 1500
                break

            merchant.evauluate_needs_and_place_bids()
            #merchant.eval_need()
            merchant.pay_taxes(self)
            merchant.place_bid(economy=self, token_to_bid=merchant.sold_commodity_name) # <- will bid max amt we can
            merchant.turns_alive += 1

        for merchant in self.sell_merchants[:]:
            #merchant.last_turn = []
            #if merchant.current_location == self:
            #if merchant.gold < 0:
            #    merchant.bankrupt()
            #    break
            #merchant.consume_food()
            #merchant.eval_need()
            #merchant.pay_taxes(self)
            merchant.create_sell(economy=self, sell_commodity=merchant.sold_commodity_name)
            #merchant.turns_alive += 1

        ## Run the auction
        for commodity, auction in self.auctions.iteritems():
            print commodity, len(auction.bids), len(auction.sells)
            auction.iterations += 1
            ## Sort the bids by price (highest to lowest) ##
            auction.bids = sorted(auction.bids, key=lambda attr: attr.price, reverse=True)
            ## Sort the sells by price (lowest to hghest) ##
            auction.sells = sorted(auction.sells, key=lambda attr: attr.price)

            self.prices[commodity] = []

            num_bids = len(auction.bids)
            num_sells = len(auction.sells)

            if num_bids > 0 or num_sells > 0:
                auction.supply = sum(offer.quantity for offer in auction.sells)
                auction.demand = sum(offer.quantity for offer in auction.bids)

            # Match bidders with sellers
            while not len(auction.bids) == 0 and not len(auction.sells) == 0:
                buyer = auction.bids[0]
                seller = auction.sells[0]
                ## Allow the buyer to make some radical readjustments the first few turns it's alive
                #if buyer.price < seller.price and (buyer.owner.turns_alive < 10 or (commodity == 'food' and buyer.owner.turns_since_food > 2)):
                #    buyer.price = int(round(seller.price * 1.5))
                #    buyer.owner.eval_bid_rejected(self, commodity, int(round(seller.price * 1.5)))

                ## If the price is still lower than the seller
                if buyer.price < seller.price:
                    buyer.owner.eval_bid_rejected(self, commodity, seller.price)
                    buyer.quantity = 0
                ## Make the transaction
                else:
                    # Determine price/amount
                    quantity = min(buyer.quantity, seller.quantity)
                    price = int(round((buyer.price + seller.price)/2))

                    if quantity > 0:
                        # Adjust buyer/seller requested amounts
                        buyer.quantity -= quantity
                        seller.quantity -= quantity

                        buyer.owner.eval_trade_accepted(self, buyer.commodity, price)
                        seller.owner.eval_trade_accepted(self, buyer.commodity, price)

                        ## Update inventories and gold counts
                        buyer.owner.take_bought_commodity(buyer.commodity, quantity)
                        seller.owner.remove_sold_commodity(seller.commodity, quantity)

                        buyer.owner.adjust_gold(-price*quantity)
                        seller.owner.adjust_gold(price*quantity)

                        buyer.owner.buys += quantity
                        buyer.owner.last_turn.append('Bought {0} {1} from {2} at {3}'.format(quantity, commodity, seller.owner.name, price))
                        seller.owner.sells += quantity
                        seller.owner.last_turn.append('Sold {0} {1} to {2} at {3}'.format(quantity, commodity, buyer.owner.name, price))

                        print ' *** {0} bought {1} {2} from {3} for {4} ***'.format(buyer.owner.name, quantity, commodity, seller.owner.name, price)

                        # Add to running tally of prices this turn
                        self.prices[commodity].append(price)

                # Now that a transaction has occurred, bump out the buyer or seller if either is satisfied
                if seller.quantity == 0: del auction.sells[0]
                if buyer.quantity == 0: del auction.bids[0]

            # All bidders re-evaluate prices
            # Added 12/13/14- only re-evaluate prices when some quantity was being offered
            if len(auction.bids) > 0:
                if num_sells > 0:
                    for buyer in auction.bids:
                        buyer.owner.eval_bid_rejected(self, buyer.commodity)
                self.auctions[commodity].bids = []

            # All sellers re-evaluate prices
            # Added 12/13/14- only re-evaluate prices when some quantity was being offered
            elif len(auction.sells) > 0:
                if num_bids > 0:
                    for seller in auction.sells:
                        seller.owner.eval_sell_rejected(self, seller.commodity)
                self.auctions[commodity].sells = []

            ## Average prices
            if len(self.prices[commodity]) > 0:
                mean_price = int(round(sum(self.prices[commodity])/len(self.prices[commodity])))
            else:
                mean_price = None
            auction.update_historical_data(mean_price, num_bids, num_sells)
            # Track mean price for last N turns
            auction.update_mean_price()

        ## Merchants evaluate whether or not to move on to the next city
        for merchant in self.buy_merchants + self.sell_merchants:
            if merchant.current_location == self:
                merchant.increment_cycle()
        ## Add some information to the city's food supply/demand
        if self.owner:
            del self.owner.food_supply[0]
            del self.owner.food_demand[0]
            self.owner.food_supply.append(self.auctions['food'].supply)
            self.owner.food_demand.append(self.auctions['food'].demand)

        #auction.check_auction_health()

    def graph_results(self, solid, dot):
        # Spit out some useful info	about the economy
        overall_history = []
        overall_bid_history = []
        overall_sell_history = []
        # Bad hack to transpose matix so plot() works correctly
        for i in xrange(len(self.auctions['food'].price_history)):
            overall_history.append([])
            overall_bid_history.append([])
            overall_sell_history.append([])
            for auction in self.auctions.itervalues():
                overall_history[i].append(auction.price_history[i])
                overall_bid_history[i].append(auction.bid_history[i])
                overall_sell_history[i].append(auction.sell_history[i])

        # Split in half so graph is easier to read
        if len(dot) == 0:
            #half_items = int(round(len(solid)/2))
            #dot = solid[:-half_items]
            #solid = solid[-half_items:]
            new_solid = []
            dot = []
            for item in solid:
                if item in [r.name for r in data.commodity_manager.resources]:
                    dot.append(item)
                elif item in [g.name for g in data.commodity_manager.goods]:
                    new_solid.append(item)

            solid = new_solid

        ## Legend for graph
        glegend = []
        for item in solid + dot:
            name_for_legend = item
            # Check for imported
            for other_city, commodities in self.owner.imports.iteritems():
                if item in commodities:
                    name_for_legend = '{0} (imported)'.format(item)
                    break
            # Check for exported
            for other_city, commodities in self.owner.exports.iteritems():
                if item in commodities:
                    name_for_legend = '{0} (exported)'.format(item)
                    break
            glegend.append(name_for_legend)

        ######### PRICES ###########
        plt.subplot(311)
        plt.title('Price history')
        #plt.grid(True)
        ## Solid lines
        for item in solid:
            plt.plot(self.auctions[item].price_history, lw=1.5, alpha=.8, c=plot_colors[item])
        for item in dot:
            plt.plot(self.auctions[item].price_history, '--', lw=1.5, alpha=.8, c=plot_colors[item])

        plt.xlim([0, len(self.auctions[item].price_history)])

        ######## BIDS ##############
        plt.subplot(312)
        plt.title('Demand (by number of agents requesting item)')
        #plt.grid(True)
        for item in solid:
            plt.plot(self.auctions[item].bid_history, lw=1.5, alpha=.8, c=plot_colors[item])
        for item in dot:
            plt.plot(self.auctions[item].bid_history, '--', lw=1.5, alpha=.8, c=plot_colors[item])

        plt.xlim([0, len(self.auctions[item].bid_history)])

        ######## SELLS ############
        plt.subplot(313)
        plt.title('Supply (by number of agents creating sell offers)')
        #plt.grid(True)
        for item in solid:
            plt.plot(self.auctions[item].sell_history, lw=1.5, alpha=.8, c=plot_colors[item])
        for item in dot:
            plt.plot(self.auctions[item].sell_history, '--', lw=1.5, alpha=.8, c=plot_colors[item])

        plt.xlim([0, len(self.auctions[item].sell_history)])

        plt.subplots_adjust(left=0.02, right=0.99, top=0.97, bottom=0.02)
        ## Show graph
        plt.subplot(311)
        plt.legend(glegend, loc=2, prop={'size':7})
        plt.show()


def main():
    #setup_resources()
    economy_test_run()

if __name__ == '__main__':
    main()

