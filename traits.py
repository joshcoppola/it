from __future__ import division
import yaml

with open('data/traits.yml') as t:
	raw_traits = yaml.load(t)
	TRAIT_INFO = raw_traits['traits']
	CULTURE_TRAIT_INFO = raw_traits['culture_traits']

	TRAITS = TRAIT_INFO.keys()

MAX_SKILL_LEVEL = 30
# For each skill level, how much XP is needed to advance to the next level
EXPERIENCE_PER_SKILL_LEVEL = {
1: 10,
2: 50,
3: 140,
4: 300,
5: 550,
6: 910,
7: 1400,
8: 2040,
9: 2850,
10: 3850,
11: 5060,
12: 6500,
13: 8190,
14: 10150,
15: 12400,
16: 14960,
17: 17850,
18: 21090,
19: 24700,
20: 28700,
21: 33110,
22: 37950,
23: 43240,
24: 49000,
25: 55250,
26: 62010,
27: 69300,
28: 77140,
29: 85550,
30: 94550
}

mult2desc = {.5:"somewhat ", 1:"", 2:"very "}

def tdesc(trait, multiplier):
	return '{0}{1}'.format(mult2desc[multiplier], trait)