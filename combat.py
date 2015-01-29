
from __future__ import division
import csv
import os
import random
from random import randint as roll

from helpers import weighted_choice

def load_combat_matrix():
    global combat_matrix, combat_moves

    file_path = os.path.join('data', 'combat_matrix.csv')

    with open(file_path, 'rb') as csv_file:
        reader = csv.reader(csv_file)

        combat_matrix = {}

        first_row = 1
        for row in reader:
            # Save the first row (to use as column headers)
            if first_row:
                columns = row[:]
                first_row = 0
            # Otherwise, compare this move vs the others and save resulting probabilities
            else:
                current_move = row[0]

                for i in xrange(len(row)-1):
                    column_index = i + 1
                    probs = row[column_index]

                    if probs != '':
                        # Split probabilities into 2 integers (they had been separated by a space)
                        probs = tuple(map(int, probs.split(' ')))
                        # current_move is the move in the 0th position of the row, other_move will be the move at the nth position in the current column index
                        other_move = columns[column_index]

                        # Create dict of dicts, so that moves can later be looked up as combat_matrix[move_1][move_2]
                        if current_move not in combat_matrix.keys():
                            combat_matrix[current_move] = {other_move: probs}
                        else:
                            combat_matrix[current_move][other_move] = probs

                        # Need to make sure matrix knows what to do when in opposite order
                        if other_move not in combat_matrix.keys():
                            combat_matrix[other_move] = {current_move: (probs[1], probs[0])}
                        else:
                            combat_matrix[other_move][current_move] = (probs[1], probs[0])


    combat_moves = tuple(combat_matrix.keys())
    #print current_move, 'vs', columns[column_index], ':', probs
    #print combat_matrix


def get_combat_odds(combatant_1, combatant_1_move, combatant_2, combatant_2_move):

    c1_dict = {}
    c2_dict = {}

    c1_dict['{0} vs {1}'.format(combatant_1_move, combatant_2_move)] = combat_matrix[combatant_1_move][combatant_2_move][0]
    c2_dict['{0} vs {1}'.format(combatant_2_move, combatant_1_move)] = combat_matrix[combatant_2_move][combatant_1_move][0]

    # Get weapon properties and add any bonus
    c1_weapon_properties = combatant_1.creature.get_current_weapon().get_weapon_properties()
    if combatant_1_move in c1_weapon_properties.keys():
        c1_dict['{0} bonus to {1}'.format(combatant_1.creature.get_current_weapon().name, combatant_1_move)] = c1_weapon_properties[combatant_1_move]

    c2_weapon_properties = combatant_2.creature.get_current_weapon().get_weapon_properties()
    if combatant_2_move in c2_weapon_properties.keys():
        c2_dict['{0} bonus to {1}'.format(combatant_2.creature.get_current_weapon().name, combatant_2_move)] = c2_weapon_properties[combatant_2_move]

    # Add participant fighting skills
    c1_dict['Fighting skill'] = combatant_1.creature.cskills['Fighting']
    c2_dict['Fighting skill'] = combatant_2.creature.cskills['Fighting']


    return c1_dict, c2_dict


def calculate_winner_of_opening_round(c1_dict, c2_dict):
    c1_total = max(1, sum(c1_dict.values()))
    c2_total = max(1, sum(c2_dict.values()))

    num = roll(0, c1_total + c2_total)

    if num <= c1_total:
        return 1
    else:
        return 2

def calculate_combat(combatant_1, combatant_1_move, combatant_2, combatant_2_move):

    combat_log = []
    if combatant_2_move != None:
        # Assuming both combatants attacked each other, compare their moves and sum
        c1_dict, c2_dict = get_combat_odds(combatant_1, combatant_1_move, combatant_2, combatant_2_move)

        # 1 means combatant 1 one, 2 means combatant 2 won
        if calculate_winner_of_opening_round(c1_dict, c2_dict) == 1:
            winner = combatant_1
            loser = combatant_2
        else:
            winner = combatant_2
            loser = combatant_1

        combat_log.append(('{0}\'s {1} with {2} {3} countered {4}\'s {5} with {6} {7}.'.format(combatant_1.fulltitle(), combatant_1_move,
            'his', combatant_1.creature.get_current_weapon().name, combatant_2.fulltitle(), combatant_2_move, 'his', combatant_2.creature.get_current_weapon().name), winner.color))
        # Winner performs single attack on loser
        combat_log.extend(simple_combat_attack(winner, loser))

    else:
        # Attacker gets 2 opportunities to attack
        combat_log.extend(simple_combat_attack(winner=combatant_1, loser=combatant_2))

        combat_log.extend(simple_combat_attack(winner=combatant_1, loser=combatant_2))

    return combat_log


def simple_combat_attack(winner, loser):

    combat_log = []
    # Hacking in some defaults for now
    attacking_weapon = winner.creature.get_current_weapon()
    attacking_object_component = attacking_weapon.components[0]
    force = attacking_weapon.get_mass()
    target_component = random.choice(loser.components)

    attack_modifiers, defend_modifiers = winner.creature.get_attack_odds(attacking_object_component=attacking_object_component, force=force, target=loser, target_component=target_component)

    attack_chance = sum(attack_modifiers.values())
    defend_chance = int(sum(defend_modifiers.values())/2)

    if roll(1, attack_chance + defend_chance) < attack_chance:
        # Lists the top layers (outermost layer first)
        layers = target_component.get_coverage_layers()

        chances_to_hit = []
        running_coverage_amt = 0
        for layer, coverage_amt in layers:
            # Chance to hit is this layer's coverage minus previous layer's coverage
            # Exception - if this layer's coverage is smaller, it's essentially un-hittable
            # TODO - ensure that chance_to_hit and running_coverage_amt work correctly with layers with weird cvg amounts
            chance_to_hit = max(coverage_amt, running_coverage_amt) - running_coverage_amt
            running_coverage_amt += chance_to_hit

            chances_to_hit.append((layer, chance_to_hit))

        #print chances_to_hit
        # Weighted choice, from stackoverflow
        targeted_layer = weighted_choice(chances_to_hit)

        # Use the poorly-written physics module to compute damage
        total_force, layer_resistance, blunt_damage = targeted_layer.apply_force(other_obj_comp=attacking_object_component, total_force=force)

        if targeted_layer.owner == target_component:
            preposition = 'on'
        else:
            preposition = 'covering'
        #combat_log.append(('{0}\'s attack hits {1}\'s {2} - the total force of {3:.1f} is diluted by the layer resistance of {4:.1f} for a total of {5:.1f} blunt damage.'.format(winner.fulltitle(), loser.fulltitle(), targeted_layer.get_name(), total_force, layer_resistance, blunt_damage), winner.color))
        combat_log.append(('{0}\'s {1} hits the {2} {3} {4}\'s {5} - {6:.1f}/{7:.1f} = {8:.1f} damage.'.format(winner.fullname(), winner.creature.get_current_weapon().name, targeted_layer.get_name(), preposition, loser.fullname(), target_component.name, total_force, layer_resistance, blunt_damage), winner.color))

    # Attack didn't connect
    else:
        combat_log.append(('{0} dodged {1}\'s attack!'.format(loser.fullname(), winner.fullname()), loser.color))

    return combat_log



load_combat_matrix()









