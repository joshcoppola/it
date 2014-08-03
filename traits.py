


class Trait:	
	def __init__(self, name, opposed_traits, profession_interests, skill_modifiers):
		# Name of the trait
		self.name = name
		# List of opposed traits (can't gain this trait if we have one of them already)
		self.opposed_traits = opposed_traits
		self.profession_interests = profession_interests
		self.skill_modifiers = skill_modifiers
		
TRAIT_INFO = [
Trait('Greedy', ['Charitable'], [], {} ),
Trait('Charitable', ['Greedy'], [], {} ),
Trait('Devout', ['Unbeliever'], [], {'Piety':6} ),
Trait('Unbeliever', ['Devout'], [], {'Piety':-6} ),
Trait('Vengeful', ['Mild-mannered'], [], {'Subterfuge':2} ),
Trait('Mild-mannered', ['Vengeful'], [], {'Subterfuge':-2} ),
Trait('Lazy', ['Hard-working'], ['Ambitious'], {'Command':-2, 'Management':-6, 'Subterfuge':-2} ),
Trait('Hard-working', ['Lazy'], [], {'Command':2, 'Piety':2, 'Management':2} ),
Trait('Moral', ['Dishonest', 'Amoral'], [], {'Subterfuge':-4} ),
Trait('Amoral', ['Moral', 'Honest'], [], {'Subterfuge':4} ),
Trait('Honest', ['Dishonest', 'Amoral'], [], {'Subterfuge':-2} ),
Trait('Dishonest', ['Moral', 'Honest'], [], {'Subterfuge':2} ),
Trait('Ambitious', ['Lazy'], [], {'Command':2, 'Piety':2, 'Management':2, 'Charisma':4, 'Subterfuge':4} ),
Trait('Fiscal Liberal', ['Fiscal Conservative'], [], {} ),
Trait('Fiscal Conservative', ['Fiscal Liberal'], [], {} ),
Trait('Social Liberal', ['Social Conservative'], [], {} ),
Trait('Social Conservative', ['Social Liberal'], [], {} )
]


		
TRAITS = [trait.name for trait in TRAIT_INFO]
		
		