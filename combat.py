
from __future__ import division
import csv
import os
from random import randint as roll

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
    c1_dict['{0} bonus to {1}'.format(combatant_1.creature.get_current_weapon().name, combatant_1_move)] = c1_weapon_properties[combatant_1_move]

    c2_weapon_properties = combatant_2.creature.get_current_weapon().get_weapon_properties()
    c2_dict['{0} bonus to {1}'.format(combatant_2.creature.get_current_weapon().name, combatant_2_move)] = c2_weapon_properties[combatant_2_move]

    # Add participant fighting skills
    c1_dict['Fighting skill'] = combatant_1.creature.cskills['Fighting']
    c2_dict['Fighting skill'] = combatant_2.creature.cskills['Fighting']


    return c1_dict, c2_dict


def calculate_winner_of_round(c1_dict, c2_dict):
    c1_total = sum(c1_dict.values())
    c2_total = sum(c2_dict.values())

    num = roll(0, c1_total + c2_total)

    if num <= c1_total:
        return 1
    else:
        return 0

load_combat_matrix()









