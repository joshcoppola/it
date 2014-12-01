

import random
from random import randint as roll
import gen_languages as lang

moon_nums = (1, 1, 1, 1, 1, 2, 2, 3, 4)
moon_colors = ['red', 'grey', 'brown', 'green', 'sepia', 'dull grey', 'dull brown', 'dull red', 'dull green', 'teal', 'aqua', 'umber', 'dull cyan']

sun_nums = (1, 1, 1, 1, 1, 1, 2, 2, 2)
sun_colors = ['white', 'bright white', 'bright yellow', 'dull yellow', 'yellow', 'dull red', 'blue', 'bright blue']

spheres = ['death', 'life', 'love', 'mountains', 'forests', 'rivers', 'oceans', 'industry', 'battle',
           'music', 'dancing', 'earth_name', 'fertility', 'thunder', 'creation', 'harvests', 'craftsmen',
           'justice', 'knowledge', 'fire', 'trickery', 'deception', 'feasting', 'wisdom',
           'the sky', 'lightning', 'storms', 'cities', 'volcanoes', 'thieves']


def create_astronomy():
    moons= []
    suns = []

    num_moons = random.choice(moon_nums)
    num_suns = random.choice(sun_nums)

    available_moon_colors = moon_colors[:]
    available_sun_colors = moon_colors[:]

    for i in xrange(num_moons):
        moons.append(available_moon_colors.pop(roll(0, len(available_moon_colors)-1)))

    for i in xrange(num_suns):
        suns.append(available_sun_colors.pop(roll(0, len(available_sun_colors)-1)))

    return moons, suns

def r(tlist):
    return random.choice(tlist)

class Moon:
    def __init__(self, name, earth_name, astronomy, color):
        self.name = name
        self.earth_name = earth_name
        self.astronomy = astronomy
        self.color = color

    def describe(self):
        if len(self.astronomy.moons) == 1:
            return self.name + ', the moon'
        else:
            return ''.join([self.name, ', the ', self.color, ' moon'])

class Sun:
    def __init__(self, name, earth_name, astronomy, color):
        self.name = name
        self.earth_name = earth_name
        self.astronomy = astronomy
        self.color = color

    def describe(self):
        if len(self.astronomy.suns) == 1:
            return self.name + ', the sun'
        else:
            return ''.join([self.name, ', the ', self.color, ' sun'])


class Astrology:
    def __init__(self, moons, suns, language):

        self.moons = []
        self.suns = []

        self.language = language
        self.earth_name = lang.spec_cap(self.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20)))


        for moon_color in moons:
            name = self.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
            name = lang.spec_cap(name)
            self.moons.append(Moon(name=name, earth_name=self.earth_name, astronomy=self, color=moon_color))


        for sun_color in suns:
            name = self.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
            name = lang.spec_cap(name)
            self.suns.append(Sun(name=name, earth_name=self.earth_name, astronomy=self, color=sun_color))


    def list_suns(self):
        if len(self.suns) == 1:
            return self.suns[0].name + ', the sun'
        elif len(self.suns) == 2:
            return ' and '.join([s.describe() for s in self.suns])
        else:
            return ', '.join([s.describe() for s in self.suns[:-1]]) + ', and ', self.suns[-1].describe()

    def list_moons(self):
        if len(self.suns) == 1:
            return self.moons[0].name + ', the moon'
        elif len(self.suns) == 2:
            return ' and '.join([s.describe() for s in self.moons])
        else:
            return ', '.join([s.describe() for s in self.moons[:-1]]) + '; and ', self.moons[-1].describe()

    def list_celestial_bodies(self):
        desc = self.earth_name + ', the earth; '

        obodies = self.suns + self.moons

        desc += '; '.join([s.describe() for s in obodies[:-1]]) + '; and ' + obodies[-1].describe()

        return desc


class God:
    def __init__(self, name, sphere):
        self.name = name
        self.sphere = sphere
        self.gender = random.choice((0, 1))

        self.mother = None
        self.father = None
        self.spouse = None
        self.children = []
        self.siblings = []

    def get_g_title(self):
        if self.gender == 0:    return 'goddess'
        elif self.gender == 1:  return 'god'

    def get_pronoun(self, s=1):
        if s:
            if self.gender: return 'He'
            else:           return 'She'
        elif s == 0:
            if self.gender: return 'His'
            else:           return 'Her'

    def get_b_or_s(self):
        if self.gender: return 'brother'
        else:           return 'sister'

    def get_parents(self):
        if self.mother == None and self.father == None:
            return ''
        else:
            return ''.join([self.get_pronoun(), ' is the child of ', self.father.fulltitle(), ' and ', self.mother.fulltitle()])

    def get_spouse(self):
        if self.spouse:
            return ''.join([self.get_pronoun(), ' is the spouse of ', self.spouse.fulltitle()])

    def get_siblings(self):
        if self.siblings == []:
            return ''
        else:
            return ''.join([self.get_pronoun(), ' is the ', self.get_b_or_s(), ' of ', ' and '.join([s.fulltitle() for s in self.siblings])])

    def fulltitle(self):
        return ''.join([self.name, ', ', self.get_g_title(), ' of ', self.sphere])

    def full_description(self):
        desc = self.fulltitle() + '. '
        if self.spouse:
            desc += self.get_spouse() + '. '
        if self.father:
            desc += self.get_parents() + '. '
        if len(self.siblings):
            desc += self.get_siblings() + '. '

        return desc


    def add_sibling(self, sibling):
        self.siblings.append(sibling)
        sibling.siblings.append(self)

    def have_child(self, child):
        child.father = self
        child.mother = child.father.spouse

        child.father.children.append(child)
        child.mother.children.append(child)

        for c in child.father.children:
            if c != child:
                child.add_sibling(c)


    def add_spouse(self, spouse):
        self.spouse = spouse
        spouse.spouse = self



class Pantheon:
    def __init__(self, astrology, num_misc_gods):
        self.astrology = astrology

        self.available_spheres = spheres[:]
        self.gods = []

        self.holy_objects = []
        self.holy_sites = []

        self.create_celestial_gods()
        self.set_name()
        self.create_misc_gods(num_misc_gods=num_misc_gods)
        self.update_god_relationships()

    def create_celestial_gods(self):
        # Create gods for each celestial body
        for c_body in self.astrology.suns + self.astrology.moons:
            name = self.astrology.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
            name = lang.spec_cap(name)

            self.gods.append(God(name=name, sphere=c_body.describe()) )

    def set_name(self):
        if roll(1, 2) == 1:
            self.name = 'Pantheon of {0}'.format(self.gods[0].name)
        else:
            self.name = '{0}mites'.format(lang.spec_cap(self.astrology.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))))

    def create_misc_gods(self, num_misc_gods):
        # Create misc gods
        for i in xrange(num_misc_gods):
            sphere = self.available_spheres.pop(roll(0, len(self.available_spheres)-1))
            name = self.astrology.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
            name = lang.spec_cap(name)

            self.gods.append(God(name=name, sphere=sphere))


    def update_god_relationships(self):
        # Gods have relationships with each other
        for god in self.gods:
            if god.gender == 1 and roll(0, 1):
                potential_spouses = [g for g in self.gods if g.gender == 0 and g.spouse == None]
                if len(potential_spouses):

                    choice = random.choice(potential_spouses)
                    god.add_spouse(spouse=choice)

                    # Kids
                    for j in xrange(roll(0, 2)):
                        sphere = self.available_spheres.pop(roll(0, len(self.available_spheres)-1))
                        name = self.astrology.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
                        name = lang.spec_cap(name)

                        child = God(name=name, sphere=sphere)
                        god.have_child(child)

                        self.gods.append(child)


    def add_holy_object(self, obj):
        self.holy_objects.append(obj)

    def add_holy_site(self, site):
        self.holy_sites.append(site)
        site.is_holy_site_to.append(self)

class CreationMyth:
    def __init__(self, creator, pantheon):
        self.creator = creator
        self.pantheon = pantheon
        self.astrology = pantheon.astrology
        self.language = self.pantheon.astrology.language
        self.earth_name = self.pantheon.astrology.earth_name

        self.story_text = []

    def create_myth(self):

        creation_type = r(['ex nihilo', 'diver', 'chaos'])#, #'iteration', 'dismember'])

        opening = r(['In a time before time, ', 'In the beginning, ',
                    'Ages ago, ', 'Eons ago, '])

        ctitle = r(['He Who Has Always Been', 'The One', 'The Creator', 'The First',
                      'God of gods', 'The Prime Being', 'The Mover'])

        c_fullname = r([self.creator.name + ', ' + ctitle + ',',
                        self.creator.name + ', ' + ctitle + ',',
                        ctitle + ', ' + self.creator.name + ','
                        ])


        if creation_type == 'ex nihilo':
            #### giants/titans

            cverb = r([' created ',
                      ' summoned ', ' brought forth ', ' willed there to be '])



            s1 = r([self.creator.name + ', ' + ctitle + ',' +
                         cverb + self.astrology.list_celestial_bodies() + '.',

                         c_fullname + cverb + self.astrology.list_celestial_bodies() + '.',

                         c_fullname + cverb + self.earth_name + '; the earth_name.',

                         c_fullname + cverb + r(['the world, and named it ',
                                                 'the earth_name, and named it ',
                                                 'the world, calling it ',
                                                 'the earth_name, naming it ',
                                                 'all that is. The center of creation was the world, '
                                                 ]) + self.earth_name + '.',

                         c_fullname + cverb + self.astrology.list_celestial_bodies() + '.'
                         ])

            s2 = r([self.creator.name + r([' looked upon ', ' looked down upon ']) + self.earth_name + ' and created the oceans, the peaks and the valleys, the hills and the plains.',
                    self.creator.name + ' flooded ' + self.earth_name + ', creating oceans where the water settled and the land where it did not.',
                    self.creator.name + ' then shaped ' + self.earth_name + ' and formed its surface. Next, ' + ctitle + ' created the oceans, lakes, and rivers.'])

            ###########
            self.story_text.append(' '.join([opening + s1, s2 ]) )
            ##########

            s3 = r([self.creator.name + ' saw the earth_name, and, feeling it empty, created the all the flora, trees, and plants. ' \
                                        'Thus the first living things were made. Even so, ' + ctitle + ' still felt it empty. '\
                                        'All manner of creatures thus came to be. But ' + self.creator.name + 'still felt it empty. '\
                                        'Thus was the race of Man created, so that others could appreciate the earth_name.',

                    self.creator.name + ' created Man in ' + self.creator.get_pronoun(s=0) + ' image. So that Man was not alone, '\
                                        'all manner of beasts were created to populate ' + self.earth_name + ', along with various flora '\
                                        'to sustain both man and beast alike.',

                    self.creator.name + ' then created all living things; trees, insects, fish, and animals. Man alone received the '\
                                        'gift of Knowledge, and this elevated him above all other creatures.'
                                         ])

            self.story_text.append(' '.join([s3]))

        elif creation_type == 'diver':
            ### Covered story

            l_adj = ['inundated with', 'covered in', 'only']

            liq = r(['water'])

            s1 = self.earth_name + ', the earth_name, was ' + r(l_adj) + ' ' + liq + '.'
            s2 = ''
            s3 = ''

            #method = r(['raised', 'animal'])
            method = r(['animal'])

            if method == 'raised':

                fl_action = r([' saw the emptiness and '])

                action = r(['raised mountains from the deep.',
                            'formed the continents.',
                            'formed land.',
                            'bombarded the ' + liq + ' with great boulders until land had formed.',
                            ])

                s2 = c_fullname + r([' ', fl_action]) + action

            elif method == 'animal':
                land = r(['sand', 'mud'])
                a_type = r(['bird', 'amphibian'])
                a_name = self.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
                a_name = lang.spec_cap(a_name)

                expand_phrase = r(['which expanded into ' + r(['land.', 'the earth_name.']),
                                  'which became ' + r(['land.', 'the earth_name.', 'the continent.']),
                                  'which grew into ' + r(['land.', 'the earth_name.', 'the continent.']),
                                  ' which begat ' + r(['land.', 'the earth_name.', 'the continent.'])
                                  ])

                if a_type == 'bird':
                    animal = r(['sparrow', 'lark', 'eagle', 'hawk', 'vulture'])

                    a_method = r(['traveled to ' + self.earth_name + ' from the heavens. It',
                                  'descended to ' + self.earth_name + ' on a rope. It',
                                  'glided to ' + self.earth_name + '. It',
                                  'came upon ' + self.earth_name + '. It',
                                  'fell to ' + self.earth_name + '. Confused, it'])

                    a_action = r(['flapped its wings until the ocean gave way to land.',
                                  'splashed the water aside and packed the '+land+' into earth_name.',
                                  'dove into the waters to find ' + land + '. Slowly the ' +land+ ' was piled together to form land.',
                                  'dove into the waters and brought ' +land+ ' to the surface, ' + expand_phrase,
                                  'had nowhere to rest and dove into the waters in search of ' + land + '. ' + a_name + ' brought ' +land+ ' to the surface, ' + expand_phrase])

                elif a_type == 'amphibian':
                    animal = r(['toad', 'salamander', 'frog'])

                    a_method = r(['traveled to ' + self.earth_name + ' from the heavens. It',
                                  'descended to ' + self.earth_name + ' on a rope. It',
                                  'was cast down to ' + self.earth_name + '. It',
                                  'fell to ' + self.earth_name + '. Confused, it'])

                    a_action = r(['dove into the waters to find ' + land + '. Slowly the ' + land + ' was piled together to form land.',
                                  'had nowhere to rest, and dove into the waters in search of ' + land + '. ' + a_name + ' brought ' +land+ ' to the surface, ' + expand_phrase])


                s2 = r([a_name + ', the ' + animal + ', ' + a_method + ' ' + a_action,
                        self.creator.name + ' sent ' + a_name + ', the ' + animal + ', to ' + self.earth_name + '. It ' + a_action])


                animal_follow_up = roll(0, 1)
                if animal_follow_up:
                    a_name = self.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
                    a_name = lang.spec_cap(a_name)
                    animal = r(['sparrow', 'lark', 'eagle', 'hawk', 'vulture'])


                    s3 = r([a_name + ', the ' + animal + ', was sent to see if the landmass was dry. It was still soft, and ' +
                            a_name + '\'s wings grazed the earth_name, creating the mountains and the valleys.',

                            a_name + ', the ' + animal + ', was sent to see if the landmass was dry. It was still soft, and ' +
                            a_name + '\'s claws scraped the earth_name, creating the valleys and the mountains.'])
                else:
                    s3 = r([c_fullname + ' saw the earth_name, and shaped the land.',
                            c_fullname + ' saw the earth_name, and formed the land into mountains, and hills, and valleys.'])


            self.story_text.append( opening + ' '.join([s1, s2, s3]) )

        elif creation_type == 'chaos':
            cosmos = r(['universe ', 'cosmos ', 'entirety of existence ', 'world '])
            v_name = self.language.gen_word(syllables=roll(1, 2), num_phonemes=(3, 20))
            v_name = lang.spec_cap(v_name)

            v_adj = r(['Expanse', 'Void'])

            form = r(['formless.', 'without form.',  'an endless expanse.',
                      'formless and shapeless.', 'devoid of form.', 'void.', 'a void.',
                      'an abyss.', 'darkness.', 'shrouded in darkness.'])
            s1 = r(['the ' + cosmos + 'was ' + form])

            s2 = r([v_name + ', the ' + v_adj + ', was ' + r(['filled with ', 'composed of ', 'made up of ']) +
                    r(['a thick, foggy vapor.', 'dense, obscuring fog.', 'swirling, gaseous matter.']),

                    'The ' + v_adj + ' seethed freely with ' +
                    r(['a thick, foggy vapor.', 'dense, obscuring fog.', 'gaseous matter.'])
                    ])

            ######
            prep = r(['From this state, ', 'From the chaos, ', 'Using this material, ', ''])
            cverb = r([' brought order to the unformed void and fashioned ',
                      ' created ', ' brought forth '])

            s3 = r([ prep + c_fullname + cverb + self.earth_name + '; the earth_name.',

                     prep + c_fullname + cverb + r(['the world, and named it ',
                                                 'the earth_name, and named it ',
                                                 'the world, calling it ',
                                                 'the earth_name, naming it ',
                                                 'all that is. The center of this creation was the world, '
                                                 ]) + self.earth_name + '.',

                      prep  +   c_fullname + cverb + self.astrology.list_celestial_bodies() + '.'
                         ])

            s4 = r([self.creator.name + r([' then looked upon ', ' looked down upon ']) + self.earth_name + ' and created the oceans, the peaks and the valleys, the hills and the plains.',
                    self.creator.name + ' then flooded ' + self.earth_name + ', creating oceans ' + r([' in the basins', ' where the water settled']) + ' and dry land elsewhere.',
                    self.creator.name + ' then shaped ' + self.earth_name + ' and formed its surface. Next, ' + ctitle + ' created the oceans, lakes, and rivers.'])
            #########
            self.story_text.append(opening + ' '.join([s1, s2, s3, s4]) )
            #########
            s5 = r([self.creator.name + ' saw the earth_name, and, feeling it empty, created the all the flora, trees, and plants. ' \
                                        'Thus the first living things were made. Even so, ' + ctitle + ' still felt it empty. '\
                                        'All manner of creatures thus came to be. But ' + self.creator.name + 'still felt it empty. '\
                                        'Thus was the race of Man created, so that others could appreciate the earth_name.',

                    self.creator.name + ' created Man in ' + self.creator.get_pronoun(s=0) + ' image. So that Man was not alone, '\
                                        'all manner of beasts were created to populate ' + self.earth_name + ', along with various flora '\
                                        'to sustain both man and beast alike.',

                    self.creator.name + ' then created all living things; trees, insects, fish, and animals. Man alone received the '\
                                        'gift of Knowledge, and this elevated him above all other creatures.'
                                         ])

            self.story_text.append(' '.join([s5]))

if __name__ == '__main__':

    language = lang.Language()
    astrology = Astrology(language=language)

    pantheon = Pantheon(astrology)

    for god in pantheon.gods:
        print god.full_description(), '\n ------------------'

    cm = CreationMyth(creator=pantheon.gods[0], pantheon=pantheon)
    print ' '
    cm.create_myth()
    for paragraph in cm.story_text:
        print paragraph




