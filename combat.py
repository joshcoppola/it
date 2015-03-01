
from __future__ import division
import csv
import yaml
import os
import random
from random import randint as roll

from helpers import weighted_choice
import config as g

def load_combat_data():
    global combat_matrix, combat_moves, melee_armed_moves

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

    ## Open file containing data on melee combat moves
    melee_armed_moves = []

    combat_file_path = os.path.join('data', 'combat_moves.yml')
    with open(combat_file_path) as yaml_file:
        combat_move_info = yaml.load(yaml_file)

        for m in combat_move_info['armed_melee']:

            move = CombatAttack(name=m['name'], position=m['position'], method=m['method'], distance=m['distance'])
            melee_armed_moves.append(move)

    #print current_move, 'vs', columns[column_index], ':', probs
    #print combat_matrix

class CombatAttack:
    def __init__(self, name, position, method, distance):
        self.name = name
        self.position = position
        self.method = method
        self.distance = distance


class WorldBattle:
    def __init__(self, faction1_named, faction1_population, faction2_named, faction2_population):
        self.faction1_named = faction1_named
        self.faction1_population = faction1_population
        self.faction2_named = faction2_named
        self.faction2_population = faction2_population

        self.battle_type = None
        self.determine_battle_type_and_execute_battle()

    def determine_battle_type_and_execute_battle(self):
        if self.faction1_population is None and self.faction2_population is None:
            self.battle_type = 'small-scale'

            self.small_scale_battle()

    def small_scale_battle(self):


        for f1_member in self.faction1_named:
            target = random.choice(self.faction2_named)

            while f1_member.creature.status not in ('dead', 'unconscious') and target.creature.status not in ('dead', 'unconscious'):

                f1_member.local_brain.attack_enemy(enemy=target)
                target.local_brain.attack_enemy(enemy=f1_member)

                #print "{0} vs {1} combat".format(f1_member.fullname(), target.fullname())
                handle_combat_round(actors=[f1_member, target])





def handle_combat_round(actors):
    for entity in actors[:]:
        if entity.creature.needs_to_calculate_combat:
            target_entity, combatant_1_opening, combatant_1_closing = entity.creature.combat_target
            # Track these moves so they can't be used next round
            entity.creature.set_last_turn_moves([combatant_1_opening, combatant_1_closing])

            if target_entity.creature and target_entity.creature.combat_target != [] and target_entity.creature.combat_target[0] == entity:
                combatant_2_opening = target_entity.creature.combat_target[1]
                combatant_2_closing = target_entity.creature.combat_target[2]
                # Track these moves so they can't be used next round
                entity.creature.set_last_turn_moves([combatant_2_opening, combatant_2_closing])

                # Only reset the flag if they're attacking back; since they could be attacking someone else
                target_entity.creature.needs_to_calculate_combat = 0
                target_entity.creature.combat_target = []
            else:
                combatant_2_opening = None
                combatant_2_closing = None

            # Reset combat flags
            entity.creature.needs_to_calculate_combat = 0
            entity.creature.combat_target = []

            # Regardless of whether the opponent fights back, calculate the outcome
            combat_log = calculate_combat(combatant_1=entity, combatant_1_opening=combatant_1_opening, combatant_1_closing=combatant_1_closing,
                                                 combatant_2=target_entity, combatant_2_opening=combatant_2_opening, combatant_2_closing=combatant_2_closing)

            #if entity == player or target_entity == player:
            #    for line, color in combat_log:
            #        game.add_message(line, color)

        # If not needing to calculate moves, clear the tracking of moves we used last round so we can use them without restriction
        else:
            entity.creature.set_last_turn_moves([])


def get_combat_odds(combatant_1, combatant_1_move, combatant_2, combatant_2_move):

    c1_dict = {}
    c2_dict = {}

    if combatant_2.creature:
        combatant_1_move = combatant_1_move.name
        combatant_2_move = combatant_2_move.name

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
        c1_dict['Fighting skill'] = combatant_1.creature.skills['fighting']
        c2_dict['Fighting skill'] = combatant_2.creature.skills['fighting']

    else:
        c1_dict['Fighting inanimate object'] = 100
        c2_dict['Inanimate object'] = 1

    return c1_dict, c2_dict


def calculate_winner_of_opening_round(c1_dict, c2_dict):
    c1_total = max(1, sum(c1_dict.values()))
    c2_total = max(1, sum(c2_dict.values()))

    num = roll(0, c1_total + c2_total)

    if num <= c1_total:
        return 1
    else:
        return 2

def calculate_combat(combatant_1, combatant_1_opening, combatant_1_closing, combatant_2, combatant_2_opening, combatant_2_closing):

    combat_log = []
    if combatant_2_opening != None:
        # Assuming both combatants attacked each other, compare their moves and sum
        c1_dict, c2_dict = get_combat_odds(combatant_1, combatant_1_opening, combatant_2, combatant_2_opening)

        # 1 means combatant 1 one, 2 means combatant 2 won
        if calculate_winner_of_opening_round(c1_dict, c2_dict) == 1:
            winner = combatant_1
            winning_opening = combatant_1_opening
            winning_closing = combatant_1_closing

            loser = combatant_2
            losing_opening = combatant_2_opening
            losing_closing = combatant_2_closing
        else:
            winner = combatant_2
            winning_opening = combatant_2_opening
            winning_closing = combatant_2_closing

            loser = combatant_1
            losing_opening = combatant_1_opening
            losing_closing = combatant_1_closing

        combat_log.append(('{0}\'s {1} with {2} {3} countered {4}\'s {5} with {6} {7}.'.format(winner.fulltitle(), winning_opening.name,
            'his', winner.creature.get_current_weapon().name, loser.fulltitle(), losing_opening.name, 'his', loser.creature.get_current_weapon().name), winner.color))
        # Winner performs single attack on loser
        combat_log.extend(winner.creature.simple_combat_attack(combat_move=winning_closing, target=loser))

    else:
        # Attacker gets 2 opportunities to attack
        combat_log.extend(combatant_1.creature.simple_combat_attack(combat_move=combatant_1_opening, target=combatant_2))

        combat_log.extend(combatant_1.creature.simple_combat_attack(combat_move=combatant_1_opening, target=combatant_2))

    return combat_log


def main():
    load_combat_data()

main()










