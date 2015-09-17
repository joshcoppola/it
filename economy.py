from __future__ import division
import random
from random import randint as roll
import cProfile
import pstats
import os
import yaml
from collections import defaultdict

from it import Profession
import data_importer as data
from helpers import weighted_dict_choice

import config as g

try:
    import matplotlib.pyplot as plt
except:
    print 'Can\'t load matplotlib - no access to graphs'


HIST_WINDOW_SIZE = 5 # Amount of trades auctions keep in memory to determine avg price (used by agents)
INVENTORY_SIZE = 20 # How much stuff we can fit in our inventory, per unit of population
MERCHANT_INVENTORY_SIZE_BOOST = 1.2

PROFIT_MARGIN = 1.1 # Won't sell an item for lower than this * normalized production cost
# How much gold each agent starts with
RESOURCE_GATHERER_STARTING_GOLD = 100000
GOOD_PRODUCER_STARTING_GOLD = 150000
MERCHANT_STARTING_GOLD = 1000000


MIN_CERTAINTY_VALUE = 2 ## Within what range traders are limited to estimating the market price
BID_REJECTED_ADJUSTMENT = 5 # Adjust prices by this much when our bid is rejected
ASK_REJECTED_ADJUSTMENT = 5 # Adjust prices by this much when nobody buys our stuff
REJECTED_UNCERTAINTY_PERCENT = .05 # We get this much more uncertain about a price when an offer is rejected
ACCEPTED_CERTAINTY_PERCENT = .05  # Out uncertainty about a price decreases by this amount when an offer is accepted

MAX_UNCERTAINTY_PERCENT = .25 # Uncertainty maxes out this percentage of the average price (.35 means  avg price - 35% to avg price + 35%)

BUY_LEAST_EXPENSIVE_COMMODITY_MODIFIER = 1
BUY_MOST_EXPENSIVE_COMMODITY_MODIFIER = 100

DEFAULT_IMPORT_TAX_RATE = .1
DEFAULT_DOMESTIC_TAX_RATE = .05

P_DIF_ADJ = 3  # When offer is accepted and exceeds what we thought the price value was, adjust it upward by this amount
N_DIF_ADJ = 3  # When offer is accepted and is lower than what we thought the price value was, adjust it downward by this amount
P_DIF_THRESH = 2.5  #Threshhold at which adjustment of P_DIF_ADJ is added to the perceived value of a commodity
N_DIF_THRESH = 2.5 #Threshhold at which adjustment of P_DIF_ADJ is subtracted from the perceived value of a commodity

START_VAL = 40 # Arbitrary value that sets the starting price of good (in gold)
START_UNCERT = 10 # Arbitrary uncertainty value (agent believes price is somewhere between (mean-this, mean+this)


# Used for calculating cost of living - how heavily to weight each type of commodity
FOOD_WEIGHT_PERC = 1
FURNITURE_WEIGHT_PERC = .2
CLOTHING_WEIGHT_PERC = .3
TOOLS_WEIGHT_PERC = .5

# Used for determining at what ratio of agent.gold / economy.cost_of_living an agent will bid for certain items
# 1st number is the threshold (how many times above cost of living we need to be before we bid on it),
# and 2nd number is the ratio of # of goods / our population that we aim for
COMMODITY_BID_THRESHHOLDS = {
    'foods': (0, 2),
    'clothing': (10, 1),
    'pottery': (25, .5),
    'furniture': (30, 1),
    'cons materials': (45, 1)
}


plot_colors = {'food':(.3, .8, .3), 'flax':(1, .5, 1), 'clay':(.25, 0, .5), 'wood':(.2, .2, .8),
               'flax clothing':(1, .2, 1), 'clay pottery':(.3, .1, .6), 'wood furniture':(.1, .1, 1),
               'stone':(.5, .5, .5), 'stone cons materials':(.5, .5, .5),

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
    def __init__(self, id_, name, population_number, buy_economy, sell_economy, sold_commodity_name, is_merchant=0, attached_to=None):
        self.id_ = id_
        self.name = name
        self.population_number = population_number

        self.buy_economy = buy_economy
        self.sell_economy = sell_economy

        self.sold_commodity_name = sold_commodity_name
        self.sold_commodity_category = data.commodity_manager.get_actual_commodity_from_name(sold_commodity_name).category

        self.reaction = data.commodity_manager.reactions[sold_commodity_name]

        self.is_merchant = is_merchant

        self.attached_to = attached_to
        if self.attached_to is not None:
            self.attached_to.creature.economy_agent = self

        self.turns_alive = 0
        self.buys = 0
        self.sells = 0

        self.gold = 0
        self.adjust_gold(GOOD_PRODUCER_STARTING_GOLD)

        self.buy_inventory = defaultdict(int)
        self.input_product_inventory = defaultdict(int)
        self.sell_inventory = defaultdict(int)

        self.merchant_travel_inventory = defaultdict(int)

        # how much stuff we can hold in each of our inventories - merchants get a slight boost
        self.inventory_size = int(self.population_number * INVENTORY_SIZE * MERCHANT_INVENTORY_SIZE_BOOST) if self.is_merchant else self.population_number * INVENTORY_SIZE

        self.last_turn = []


        self.activity_is_blocked = 0

        self.current_location = buy_economy
        self.linked_economy_building = None
        self.resource_gathering_regions = None

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


        self.sell_inventory[self.sold_commodity_name] = self.population_number * roll(0, 3)

        if self.reaction.is_finished_good and not self.is_merchant:
            self.input_product_inventory[self.reaction.input_commodity_name] += self.population_number * roll(1, 3)

        if not self.is_merchant:
            for commodity_category in self.reaction.commodities_consumed:
                self.buy_inventory[random.choice(data.commodity_manager.get_names_of_commodities_of_type(commodity_category))] += self.population_number * roll(0, 3)

            for commodity_category in self.reaction.commodities_required:
                self.buy_inventory[random.choice(data.commodity_manager.get_names_of_commodities_of_type(commodity_category))] += self.population_number * roll(0, 3)

        self.buy_inventory['food'] = self.population_number * roll(2, 5)
        self.buy_inventory['flax clothing'] = self.population_number * roll(0, 2)
        self.buy_inventory['wood furniture'] = self.population_number * roll(0, 2)
        self.buy_inventory['iron tools'] = self.population_number * roll(0, 5)
        if self.sold_commodity_category == 'tools':
            self.buy_inventory['wood'] += self.population_number * roll(1, 5)


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
        ''' Placing a bought commodity in the right inventory '''
        # If this is the particular procduct we need as an input, or we are a merchant and this is the item we trade, put it in our special product inventory
        if (self.reaction.is_finished_good and commodity == self.reaction.input_commodity_name) or (self.is_merchant and commodity == self.sold_commodity_name):
            self.input_product_inventory[commodity] += amount
        else:
            self.buy_inventory[commodity] += amount

    def remove_sold_commodity(self, commodity, amount):
        ''' Proper handling for removing a commodity once we've sold it '''
        self.sell_inventory[commodity] = max(0, self.sell_inventory[commodity] - amount)


    def increment_cycle(self):
        ''' Increment the time spent at this economy, and if it has goods, add to a list of departing merchants so they can create a caravan '''
        self.time_here += 1

        if self.current_location.owner:
            destination = None
            # If we have returned home to the city where we buy things, and have filled our inventory (either it's full,
            # or we've been here a few turns and have a reasonable amount), ship out to the destination
            if self.current_location == self.buy_economy and self.input_product_inventory[self.sold_commodity_name] >= 2 * self.population_number:
                destination = self.sell_economy.owner

                # Load the goods onto the caravan
                amount = self.input_product_inventory[self.sold_commodity_name]
                self.input_product_inventory[self.sold_commodity_name] -= amount
                self.merchant_travel_inventory[self.sold_commodity_name] += amount
                # print self.name, 'departing with', amount, self.sold_commodity_name

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

    def unload_goods(self, economy):
        ''' Merchants unloading their goods in a city must pay a percentage as import tax '''
        amount_to_unload = self.merchant_travel_inventory[self.sold_commodity_name]

        # Pay taxes on import to the city government
        tax_amount = int(amount_to_unload * economy.imported_commodity_tax_rates[self.sold_commodity_name])
        if tax_amount:
            economy.collected_taxes[self.sold_commodity_name] += tax_amount
            amount_to_unload -= tax_amount

        self.merchant_travel_inventory[self.sold_commodity_name] -= amount_to_unload
        self.sell_inventory[self.sold_commodity_name] += amount_to_unload

    def pay_taxes(self):
        ''' Pay taxes. If the economy has an owner, pay the taxes to that treasury '''
        self.adjust_gold( -int(self.buy_economy.local_taxes * self.population_number) )

        # economy owner - should be the city
        if self.buy_economy.owner:
            self.buy_economy.owner.treasury += self.buy_economy.local_taxes

    def pay_production_taxes(self, commodity_name, amount_to_be_taxed):
        ''' Each agent also gets taxed based on the goods they produce '''
        tax_amount = int(amount_to_be_taxed * self.buy_economy.commodity_tax_rates[commodity_name])
        self.buy_economy.collected_taxes[self.sold_commodity_name] += tax_amount

        # Return how much of the item is left after taxes
        return amount_to_be_taxed - tax_amount

    def get_available_inventory_space(self, inventory):
        ''' Return how much space is available in a given inventory '''
        return max(self.inventory_size - sum(inventory.values() ), 0)

    def get_all_commodities_of_type(self, type_of_commodity, inventory):
        ''' Return a dict of all commodities in our inventory which match the type of commodity '''
        matching_commodities = defaultdict(int)

        for token_of_commodity in data.commodity_manager.get_names_of_commodities_of_type(type_of_commodity):
            if token_of_commodity in inventory and inventory[token_of_commodity] > 0:
                matching_commodities[token_of_commodity] = inventory[token_of_commodity]

        return matching_commodities


    def find_token_and_place_bid(self, economy, type_of_commodity, quantity):
        ''' Given an particular type of commodity that we need (e.g. tools), figure out what to bid on based on our income and what's available '''
        commodities_with_supply = [c for c in self.buy_economy.available_types[type_of_commodity] if self.buy_economy.auctions[c].supply]

        # If there's only one type of commodity with supply, offered, we will must buy it
        if len(commodities_with_supply) == 1:
            token_to_bid = commodities_with_supply[0]

        # What to bid on if we have options
        ## NOTE ##   This also includes cases where there are no commodities with supply - but we will still preserve the bidding behavior
        elif len(commodities_with_supply) != 1:
            # Calculate the gold per population and the commodity: price dict
            gold_per_population = self.gold / self.population_number
            # If there are none of the commodity available, agents will preserve the same bidding behavior -
            # but we must first open up the commodities list to all commodities of that type
            valid_commodities = commodities_with_supply if commodities_with_supply else self.buy_economy.available_types[type_of_commodity]
            prices = {commodity: self.buy_economy.auctions[commodity].get_last_valid_price() for commodity in valid_commodities}

            cheapest_commodity = min(prices, key=prices.get)
            # Buy the cheapest stuff if we're poor  -- but only if it's plentiful (supply / demand > 1)
            if gold_per_population < self.buy_economy.cost_of_living * BUY_LEAST_EXPENSIVE_COMMODITY_MODIFIER and \
                    self.buy_economy.auctions[cheapest_commodity].supply / max(1, self.buy_economy.auctions[cheapest_commodity].demand) >= 1:
                        token_to_bid = cheapest_commodity

            # Buy the most expensive stuff if we're rich
            #elif gold_per_population > self.buy_economy.cost_of_living * BUY_MOST_EXPENSIVE_COMMODITY_MODIFIER:
            #    token_to_bid = max(prices, key=prices.get)
                #print self.name, 'bidding max on', token_to_bid, ', gold =', gold_per_population, '; modifier =', self.buy_economy.cost_of_living * BUY_MOST_EXPENSIVE_COMMODITY_MODIFIER

            # If we're in the middle, pick a random commodity weighted by its supply
            else:
                choices = {c: self.buy_economy.auctions[c].supply for c in valid_commodities}
                token_to_bid = weighted_dict_choice(choices)
                #token_to_bid = random.choice(valid_commodities)


        self.place_bid(economy=economy, token_to_bid=token_to_bid, quantity=quantity)

    def place_bid(self, economy, token_to_bid, quantity, minimum=0):
        ''' Place a bid in the economy '''
        est_price = self.perceived_values[economy][token_to_bid].center
        uncertainty = self.perceived_values[economy][token_to_bid].uncertainty

        bid_price = roll(est_price - uncertainty, est_price + uncertainty)

        # Favorability is the ratio of how well it has done in the past HIST_WINDOW_SIZE rounds to what we believe the current price is
        # This means a lower price than the historical average is likely to make us want to bid on more items
        if token_to_bid != 'food':
            favorability = economy.auctions[token_to_bid].mean_price / ((self.perceived_values[economy][token_to_bid].center + economy.auctions[token_to_bid].last_price) / 2)
            # If a minimum has been set, never bid less quantity than that minimum
            quantity = max(minimum, int(round(quantity * favorability)) )

        #print self.name, 'bidding on', quantity, token_to_bid, 'for', bid_price, 'at', self.current_location.owner.name
        if quantity > 0:
            self.last_turn.append('Bid on {0} {1} for {2}'.format(quantity, token_to_bid, bid_price))
            economy.auctions[token_to_bid].bids.append(Offer(owner=self, commodity=token_to_bid, price=bid_price, quantity=quantity))
        else:
            self.last_turn.append('Tried to bid on {0} but quantity not > 0'.format(token_to_bid))

    def create_sell(self, economy, sell_commodity, quantity):
        ''' Determines how many commoditys to sell, and at what cost '''
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

        # If the last price of the item is lower than the mean price, we may be inclined to offer less for sale
        favorability = ((self.perceived_values[economy][sell_commodity].center + economy.auctions[sell_commodity].last_price) / 2) / economy.auctions[sell_commodity].mean_price
        # However, we can never offer more than the original amount
        quantity = min(int(round(quantity * favorability)), quantity)

        #print self.name, 'selling', quantity_to_sell, sell_commodity
        if quantity > 0:
            #print self.name, 'selling', quantity_to_sell, sell_commodity, 'for', sell_price, 'at', self.current_location.owner.name
            self.last_turn.append('Offered to sell {0} {1} for {2}'.format(quantity, sell_commodity, sell_price))
            economy.auctions[sell_commodity].sells.append( Offer(owner=self, commodity=sell_commodity, price=sell_price, quantity=quantity) )

            #print '{0} offered to sell {1} {2} at {3}'.format(self.name, quantity_to_sell, self.sold_commodity_name, sell_price)
        else:
            self.last_turn.append('Tried to sell {0} but inventory was empty'.format(sell_commodity))
            #print '{0} did not have any {1} to sell'.format(self.name, self.sold_commodity_name)


    def eval_trade_accepted(self, economy, type_of_commodity, price):
        ''' Adjust our belief in the price of a commodity after accepting a trade '''
        if self.perceived_values[economy][type_of_commodity].uncertainty >= MIN_CERTAINTY_VALUE:
            self.perceived_values[economy][type_of_commodity].uncertainty -= int(self.perceived_values[economy][type_of_commodity].uncertainty * ACCEPTED_CERTAINTY_PERCENT)

        our_mean = self.perceived_values[economy][type_of_commodity].center

        if price > our_mean * P_DIF_THRESH:
            self.perceived_values[economy][type_of_commodity].center += P_DIF_ADJ
        elif price < our_mean * N_DIF_THRESH:
            # We never let it's worth drop under a certain % of tax money.
            self.perceived_values[economy][type_of_commodity].center = \
                max(self.perceived_values[economy][type_of_commodity].center - N_DIF_ADJ, (self.buy_economy.local_taxes) + self.perceived_values[economy][type_of_commodity].uncertainty)


    def adjust_uncertainty(self, economy, type_of_commodity):
        ''' Ensures that the uncertainty value is never adjusted to be too wide '''
        uncertainty_limit = int(max(economy.auctions[type_of_commodity].mean_price * MAX_UNCERTAINTY_PERCENT, 1))
        self.perceived_values[economy][type_of_commodity].uncertainty += \
            min( int(self.perceived_values[economy][type_of_commodity].uncertainty * REJECTED_UNCERTAINTY_PERCENT), uncertainty_limit)


    def eval_bid_rejected(self, economy, type_of_commodity, price=None):
        ''' What to do when we've bid on something and didn't get it '''

        assert economy.auctions[type_of_commodity].supply

        if price is None:
            self.perceived_values[economy][type_of_commodity].center += BID_REJECTED_ADJUSTMENT
            self.adjust_uncertainty(economy, type_of_commodity)
        else:
            # Radical re-evaluation of the price
            self.perceived_values[economy][type_of_commodity].center = price + self.perceived_values[economy][type_of_commodity].uncertainty
            self.adjust_uncertainty(economy, type_of_commodity)


    def produce_sold_commodity(self):
        ''' Gather resources, consume commodities, and account for breaking stuff '''

        # Start by setting the # of reactions we can produce to the size of the population
        if not self.reaction.is_finished_good:
            available_reaction_amount = self.population_number
        else:
            available_reaction_amount = min(self.population_number, self.input_product_inventory[self.reaction.input_commodity_name])

        # For every consumed commodity, check how many we have in inventory, and keep track of the minimum number of times
        # we can run the reaction
        for commodity_type, amount in self.reaction.commodities_consumed.iteritems():
            total_consumed_commodities = self.count_commodities_of_type(commodity_type, inventory=self.buy_inventory)
            available_reaction_amount = min(int(total_consumed_commodities / amount), available_reaction_amount)

        for commodity_type, amount in self.reaction.commodities_required.iteritems():
            total_required_commodities = self.count_commodities_of_type(commodity_type, inventory=self.buy_inventory)
            available_reaction_amount = min(int(total_required_commodities / amount), available_reaction_amount)

        # Reaction limited by how much output space we have available
        available_space = self.get_available_inventory_space(inventory=self.sell_inventory)
        available_reaction_amount = min( int(available_space / self.reaction.output_amount), available_reaction_amount)

        ##### Run the reaction however many times we can #####
        if available_reaction_amount:
            # If we need to Remove from buy inventory
            if self.reaction.is_finished_good:
                self.input_product_inventory[self.reaction.input_commodity_name] = max(self.reaction.input_amount * available_reaction_amount, 0)

            # Also consume other needed goods
            for commodity_type, amount in self.reaction.commodities_consumed.iteritems():
                self.remove_commodities_of_type(type_of_commodity=commodity_type, inventory=self.buy_inventory, amount_to_remove=available_reaction_amount * amount)

            # Tax the production
            pre_tax_amount = self.reaction.output_amount * available_reaction_amount
            after_tax_amount = self.pay_production_taxes(commodity_name=self.reaction.output_commodity_name, amount_to_be_taxed=pre_tax_amount)

            # Add to sell inventory
            self.sell_inventory[self.reaction.output_commodity_name] += after_tax_amount

        ## If we cannot officially run the reaction, still produce a little bit, simulating working in poor conditions with broken tools, etc
        else:
            self.sell_inventory[self.reaction.output_commodity_name] = min( int(self.population_number / 5) + self.sell_inventory[self.reaction.output_commodity_name], self.inventory_size )


        self.last_turn.append('Produced {0} reactions for {1}'.format(available_reaction_amount, self.sold_commodity_name))


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
        ''' What to do when we put something up for sale and nobody bought it '''
        if economy.auctions[type_of_commodity].demand:
            # production_cost = self.check_min_sell_price()
            # min_sale_price = int(round(production_cost*PROFIT_MARGIN))

            #self.perceived_values[type_of_commodity].center = max(self.perceived_values[type_of_commodity].center - ASK_REJECTED_ADJUSTMENT, min_sale_price + self.perceived_values[type_of_commodity].uncertainty)
            self.adjust_uncertainty(economy, type_of_commodity)
            self.perceived_values[economy][type_of_commodity].center = \
                max(self.perceived_values[economy][type_of_commodity].center - ASK_REJECTED_ADJUSTMENT, self.perceived_values[economy][type_of_commodity].uncertainty + 1)


    def bankrupt(self):
        ''' Figure out what to do when we run out of money '''
        if self.is_merchant:
            self.adjust_gold(MERCHANT_STARTING_GOLD)
            g.game.add_message('{0} in {1} has gone bankrupt, but was reimpursed'.format(self.name, self.buy_economy.owner.name))
            return

        all_agents_of_this_type_in_this_economy = [a for a in self.buy_economy.all_agents if a.name == self.name]

        if len(all_agents_of_this_type_in_this_economy) == 1:
            # Government bailout
            self.adjust_gold(RESOURCE_GATHERER_STARTING_GOLD)
            g.game.add_message('{0} in {1} has gone bankrupt, but was reimpursed'.format(self.name, self.buy_economy.owner.name))

        # Main action - remove agent from economy, etc
        elif len(all_agents_of_this_type_in_this_economy) > 1:
            # print 'Removing {0} in {1}'.format(self.name, self.economy.owner.name)  ## DEBUG
            g.game.add_message('{0} in {1} has gone bankrupt'.format(self.name, self.buy_economy.owner.name))
            self.buy_economy.all_agents.remove(self)
            if self.resource_gathering_regions:
                resource_name = 'land' if self.sold_commodity_name == 'food' else self.sold_commodity_name
                self.resource_gathering_region.remove_resource_gatherer_from_region(resource_name=resource_name, agent=self)

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
        if self.buy_economy.owner:
            for obj in self.buy_economy.owner.faction.unique_object_dict:
                for tag in self.buy_economy.owner.faction.unique_object_dict[obj]['tags']:
                    if tag in data.AGENT_INFO['producers'][self.sold_commodity_name]['sold_object_tags']:
                        sold_objects.append(obj)
                        break

        return sold_objects


    def create_sells_for_turn(self):
        ''' Beginning of the turn - produce items and create sells '''
        self.last_turn = []
        self.pay_taxes()

        if self.gold < 0:
            self.bankrupt()

        if self.is_merchant:
            self.create_sell(economy=self.sell_economy, sell_commodity=self.sold_commodity_name, quantity=int(self.sell_inventory[self.sold_commodity_name] * .75))

        elif not self.activity_is_blocked:
            self.produce_sold_commodity()
            #quantity = min(self.population_number, int(self.sell_inventory[self.sold_commodity_name] * 1.0) )
            quantity = int(self.sell_inventory[self.sold_commodity_name] * .75)
            self.create_sell(economy=self.sell_economy, sell_commodity=self.sold_commodity_name, quantity=quantity)

    def create_bids_for_turn(self):
        ''' Second part of the turn - consume stuff, place bids, pay taxes '''

        if not self.activity_is_blocked:
            self.consume_food_and_break_commodities()
            self.evaluate_needs_and_place_bids()

        self.turns_alive += 1

    def count_commodities_of_type(self, type_of_commodity, inventory):
        ''' In one of our inventories, find all commodities of a given type '''
        return sum(self.get_all_commodities_of_type(type_of_commodity=type_of_commodity, inventory=inventory).values())

    def remove_commodities_of_type(self, type_of_commodity, inventory, amount_to_remove):
        ''' In the case where we consume or break a type of item, this method will remove the appropriate tokens in our inventory '''
        commodities = self.get_all_commodities_of_type(type_of_commodity=type_of_commodity, inventory=inventory)

        remaining_amount_to_remove = amount_to_remove
        for commodity_token, amount in commodities.iteritems():
            removed = min(remaining_amount_to_remove, amount)
            inventory[commodity_token] -=  removed

            remaining_amount_to_remove -= removed
            if remaining_amount_to_remove <= 0:
                break

    def get_all_inventory_by_type(self):
        ''' Return a dictionary for all commodities in our (buy) inventory, arranged as commodity_type : amount'''
        inventory_by_type = defaultdict(int)
        for commodity_name, amount in self.buy_inventory.iteritems():
            inventory_by_type[data.commodity_manager.get_actual_commodity_from_name(commodity_name).category] += amount

        return inventory_by_type


    def consume_food_and_break_commodities(self):
        ''' Here is where an agent consumes food, (potentially) breaks some items '''
        #### Roll through everything - consume food, and have stuff break ####
        for commodity_name, amount in self.buy_inventory.iteritems():
            # If we're not a farmer, each population eats a food
            if commodity_name == 'food' and self.sold_commodity_name != 'food':
                self.buy_inventory['food'] -= min(self.population_number, self.buy_inventory['food'])

            # For every other commodity, if it's not one we use in our input...
            elif (not self.reaction.is_finished_good) or (self.reaction.is_finished_good and commodity_name != self.reaction.input_commodity_name):
                # Certain amount of an item breaks
                amount_to_break =  int( max(data.commodity_manager.get_actual_commodity_from_name(commodity_name).break_chance * .01, 1) * roll(1, 10))
                self.buy_inventory[commodity_name] = \
                    max(self.buy_inventory[commodity_name] - amount_to_break, 0)

    def evaluate_needs_and_place_bids(self):
        ''' Here, agents see what they need and bid on it '''

        #### Roll through cost-of-living stuff, and bid on whatever we need ####
        inventory_by_type = self.get_all_inventory_by_type()

        normalized_gold = self.gold / self.population_number
        # Our standard of living is a ratio of how much gold we have per person, to the cost of living in the economy
        our_standard_of_living = normalized_gold / self.buy_economy.cost_of_living

        for commodity_category, (standard_of_living_threshhold, ideal_number_per_person) in COMMODITY_BID_THRESHHOLDS.iteritems():
            amount_of_commodity_to_bid = int(self.population_number * ideal_number_per_person) - inventory_by_type[commodity_category]
            # We will consider bidding on commodities if they don't match the type of commodity we output, and if
            # we have a high enough standard of living
            if commodity_category != self.sold_commodity_category and our_standard_of_living > standard_of_living_threshhold and amount_of_commodity_to_bid > 0:
                self.find_token_and_place_bid(economy=self.buy_economy, type_of_commodity=commodity_category, quantity=amount_of_commodity_to_bid)

        # Non-merchants will check for commodities input and consumed by their reactions
        if not self.is_merchant:
            ## For goods like wood to be burned by a blacksmith; which we need to consume in order to make our output
            ideal_number_per_person = 2
            for commodity_category in self.reaction.commodities_consumed:
                if inventory_by_type[commodity_category] < self.population_number * ideal_number_per_person:
                    amount_of_commodity_to_bid = (self.population_number * ideal_number_per_person) - inventory_by_type[commodity_category]
                    self.find_token_and_place_bid(economy=self.buy_economy, type_of_commodity=commodity_category, quantity=amount_of_commodity_to_bid)

            ## For goods like tools, which we need in order to make our output
            for commodity_category in self.reaction.commodities_required:
                if inventory_by_type[commodity_category] < self.population_number * ideal_number_per_person:
                    amount_of_commodity_to_bid = (self.population_number * ideal_number_per_person) - inventory_by_type[commodity_category]
                    self.find_token_and_place_bid(economy=self.buy_economy, type_of_commodity=commodity_category, quantity=amount_of_commodity_to_bid)


            # If there is an input to the reaction we generate, bid on it
            if self.reaction.is_finished_good:
                if normalized_gold < self.buy_economy.cost_of_living * 1000:
                    # At minimum, try to maintain just enough so we can perform the max reactions
                    quantity_to_bid = self.population_number - self.input_product_inventory[self.reaction.input_commodity_name]
                else:
                    # Otherwise, we're feeling bold enough to bid a bigger amount
                    quantity_to_bid = self.get_available_inventory_space(inventory=self.input_product_inventory)

                # If we have acheived a base quantity to bid, execute it
                if quantity_to_bid:
                    self.place_bid(economy=self.buy_economy, token_to_bid=self.reaction.input_commodity_name, quantity=quantity_to_bid, minimum=quantity_to_bid)


        # Or, if we're a merchant, bid on the items we trade
        elif self.is_merchant and self.sell_inventory[self.sold_commodity_name] < self.inventory_size:
            quantity = min(self.get_available_inventory_space(inventory=self.input_product_inventory), self.get_available_inventory_space(inventory=self.sell_inventory))
            self.place_bid(economy=self.buy_economy, token_to_bid=self.sold_commodity_name, quantity=quantity)

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


    # def player_auto_manage(self):
    #     tokens_to_bid = self.eval_need()
    #
    #     for token in tokens_to_bid:
    #         bid_price, bid_quantity = self.eval_bid(token)
    #         self.future_bids[token] = [bid_price, bid_quantity]
    #
    #     # Straight from food bidding code, except subtract one because we'll be consuming it next turn
    #     if self.need_food and self.inventory['food'] <= (FOOD_BID_THRESHHOLD * self.population_number):
    #         token = random.choice(self.economy.available_types['foods'])
    #         bid_price, bid_quantity = self.eval_bid(token)
    #
    #         self.future_bids[token] = [bid_price, bid_quantity]
    #
    #     sell_price, quantity_to_sell = self.check_sell()
    #     if quantity_to_sell > 0:
    #         self.future_sells[self.sold_commodity_name] = [sell_price, quantity_to_sell]


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
        self.commodity_category = data.commodity_manager.get_actual_commodity_from_name(self.commodity).category
        self.economy.auctions_by_category[self.commodity_category].append(self)

        self.bids = []
        self.sells = []
        self.price_history = [START_VAL]
        # How many bids have existed each round
        self.bid_history = [0]
        # How many sells have existed each round
        self.sell_history= [0]

        self.last_price = START_VAL
        self.mean_price = START_VAL

        self.iterations = 0

        self.supply = 0
        self.demand = 0

    def update_historical_data(self, mean_price_last_round, num_bids, num_sells):
        # Updates the history for this auction
        self.price_history.append(mean_price_last_round)
        self.bid_history.append(num_bids)
        self.sell_history.append(num_sells)

        # This tracks the last price paid for the item, used when figuring Favorability ratings for agents
        if mean_price_last_round is not None:
            self.last_price = mean_price_last_round

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

    def get_recent_ds_ratio(self):
        ''' Return the demand to supply ratio for recent turns '''
        return sum(self.bid_history[-HIST_WINDOW_SIZE:]) / sum(self.sell_history[-HIST_WINDOW_SIZE:])


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
        self.buy_merchants = []
        self.sell_merchants = []

        self.all_agents = []

        self.starving_agents = []
        # Auctions that take place in this economy
        self.auctions = {}
        self.prices = {}

        # Grouping the auctions by category; used in calculating cost of living
        self.auctions_by_category = defaultdict(list)
        self.cost_of_living = int( (START_VAL * FOOD_WEIGHT_PERC) + (START_VAL * FURNITURE_WEIGHT_PERC) +
                                   (START_VAL * CLOTHING_WEIGHT_PERC) + (START_VAL * TOOLS_WEIGHT_PERC) )

        # Amount of gold paid in taxes each turn
        self.local_taxes = local_taxes
        # Percentage of agent yields the government collects
        self.commodity_tax_rates = defaultdict(int)

        self.imported_commodity_tax_rates = defaultdict(int)

        # The actual commoditied we've collected from agents
        self.collected_taxes = defaultdict(int)

        # Counter to be appended to agent names
        self.agent_num = 1

    def get_all_available_commodity_tokens(self):
        return [token for tokens in self.available_types.values() for token in tokens]

    def get_valid_agent_types(self):
        valid_types = [resource for resource in self.native_resources]

        valid_goods = list_goods_from_strategic(valid_types)

        return valid_types + valid_goods


    def calculate_cost_of_living(self):
        ''' Intended as a rough measure of the cost of living; used in agents' evaluations of how well they're doing '''
        cost_of_food = min(self.auctions_by_category['foods'], key=lambda auction: auction.mean_price).mean_price

        cost_of_furniture = min(self.auctions_by_category['furniture'], key=lambda auction: auction.mean_price).mean_price
        cost_of_clothing = min(self.auctions_by_category['clothing'], key=lambda auction: auction.mean_price).mean_price
        cost_of_tools = min(self.auctions_by_category['tools'], key=lambda auction: auction.mean_price).mean_price

        # Perform the calculation
        self.cost_of_living = int( (cost_of_food * FOOD_WEIGHT_PERC) + (cost_of_furniture * FURNITURE_WEIGHT_PERC) +
                                   (cost_of_clothing * CLOTHING_WEIGHT_PERC) + (cost_of_tools * TOOLS_WEIGHT_PERC) )


    def add_commodity_to_economy(self, commodity):
        ''' Each commodity has an associated auction house, containing some price / bidding history '''
        category = data.commodity_manager.get_actual_commodity_from_name(commodity).category
        if category in self.available_types:
            if commodity not in self.available_types[category]:
                self.available_types[category].append(commodity)
                self.auctions[commodity] = AuctionHouse(economy=self, commodity=commodity)
                self.commodity_tax_rates[commodity] = DEFAULT_DOMESTIC_TAX_RATE
        else:
            self.available_types[category] = [commodity]
            self.auctions[commodity] = AuctionHouse(economy=self, commodity=commodity)
            self.commodity_tax_rates[commodity] = DEFAULT_DOMESTIC_TAX_RATE

    def add_new_agent_to_economy(self):
        ''' Flip between adding the most profitable commodity, or the most demanded commodity '''
        if roll(0, 1):
            token = self.find_most_profitable_agent_token(restrict_based_on_available_resource_slots=1)
            self.add_agent_based_on_token( token )
            # g.game.add_message('Adding a new {0} in {1} (based on profit)'.format(token, self.owner.name))
            # print 'Adding {0} in {1}'.format(token, self.economy.owner.name)## DEBUG
        else:
            token = self.find_most_demanded_commodity(restrict_based_on_available_resource_slots=1)
            self.add_agent_based_on_token( token )
            # g.game.add_message('Adding a new {0} in {1} (based on demand)'.format(token, self.owner.name))
            #print 'Adding {0} in {1}'.format(token, self.economy.owner.name)## DEBUG


    def add_merchant(self, sell_economy, sold_commodity_name, attached_to=None):
        name = '{0} merchant'.format(sold_commodity_name)

        # TODO - merchants will get default Reaction based on their traded item - should find a way around this
        merchant = Agent(id_=self.agent_num, name=name, population_number=20, buy_economy=self, sell_economy=sell_economy, sold_commodity_name=sold_commodity_name,
                         is_merchant=1, attached_to=attached_to)

        self.buy_merchants.append(merchant)
        sell_economy.sell_merchants.append(merchant)
        # Test if it's in the economy and add it if not
        self.add_commodity_to_economy(sold_commodity_name)
        sell_economy.add_commodity_to_economy(sold_commodity_name)

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
            population_number = 100
        elif token in [r.name for r in data.commodity_manager.resources]:
            population_number = 100
        else:
            population_number = 20

        name = data.COMMODITY_TO_PRODUCER_NAMES[token] if token in data.COMMODITY_TO_PRODUCER_NAMES else '{0} maker'.format(token)

        agent = Agent(id_=self.agent_num, name=name, population_number=population_number, buy_economy=self, sell_economy=self, sold_commodity_name=token)

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
                building = self.owner.create_building(zone='industrial', type_='shop', template='TEST', professions=[Profession(name, category='commoner')], inhabitants=[], tax_status='commoner')
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

        gold_per_commodity = defaultdict(int)
        agents_per_commodity = defaultdict(int)

        for agent in self.all_agents:
            # If it's a finished good, or it's a raw material that is available for us to use...
            if agent.reaction.is_finished_good or ( (not agent.reaction.is_finished_good) and agent.sold_commodity_name in available_resource_slots):
                gold_per_commodity[agent.sold_commodity_name] += agent.gold / agent.population_number
                agents_per_commodity[agent.sold_commodity_name] += 1

        ### Now choose the best one based off of the ratio of gold to agents
        best_ratio = 0
        best_commodity = None
        for commodity in gold_per_commodity:
            # If the gold to agent ratio is high, then keep track of it
            current_gold_to_agent_ratio = gold_per_commodity[commodity] / agents_per_commodity[commodity]
            if current_gold_to_agent_ratio > best_ratio:
                best_commodity, best_ratio = commodity, current_gold_to_agent_ratio

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
            is_resource = commodity in [r.name for r in data.commodity_manager.resources]
            if (restrict_based_on_available_resource_slots and is_resource and commodity in available_resource_slots) or \
                    (not is_resource) or (not restrict_based_on_available_resource_slots):
                current_ratio = self.auctions[commodity].get_recent_ds_ratio()
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
        # First, each agent produces items and puts them for sale
        for agent in self.all_agents[:] + self.sell_merchants[:]:
            agent.create_sells_for_turn()
        # Next, agents place bids based on what's available
        for agent in self.all_agents[:] + self.buy_merchants[:]:
            agent.create_bids_for_turn()

        ## Run the auction
        for commodity, auction in self.auctions.iteritems():
            #print commodity, len(auction.bids), len(auction.sells)
            auction.iterations += 1
            ## Sort the bids by price (highest to lowest) ##
            auction.bids = sorted(auction.bids, key=lambda attr: attr.price, reverse=True)
            ## Sort the sells by price (lowest to hghest) ##
            auction.sells = sorted(auction.sells, key=lambda attr: attr.price)

            commodity_sell_prices = []

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

                        #print ' *** {0} bought {1} {2} from {3} for {4} ***'.format(buyer.owner.name, quantity, commodity, seller.owner.name, price)

                        # Add to running tally of prices this turn
                        commodity_sell_prices.append(price)

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
            if commodity_sell_prices:
                mean_price_last_round = int(round(sum(commodity_sell_prices)/len(commodity_sell_prices)))
            else:
                mean_price_last_round = None
            #auction.update_historical_data(mean_price, num_bids, num_sells)
            auction.update_historical_data(mean_price_last_round, auction.demand, auction.supply)
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
        self.calculate_cost_of_living()

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

        plt.subplots_adjust(left=0.03, right=0.99, top=0.97, bottom=0.02)
        ## Show graph
        plt.subplot(311)
        plt.legend(glegend, loc=2, prop={'size':7})

        # Zoom in
        wm = plt.get_current_fig_manager()
        wm.window.state('zoomed')

        plt.show()


def main():
    #setup_resources()
    economy_test_run()

if __name__ == '__main__':
    main()

