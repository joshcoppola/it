import yaml

with open('data/traits.yml') as t:
	raw_traits = yaml.load(t)
	TRAIT_INFO = raw_traits['traits']
	CULTURE_TRAIT_INFO = raw_traits['culture_traits']

	TRAITS = TRAIT_INFO.keys()


mult2desc = {.5:"somewhat ", 1:"", 2:"very "}

def tdesc(trait, multiplier):
	return '{0}{1}'.format(mult2desc[multiplier], trait)