from __future__ import division
import xml.etree.ElementTree as etree
import os
import economy as econ
import copy
import yaml

import random
from random import randint as roll
import libtcodpy as libtcod

YAML_DIRECTORY = os.path.join(os.getcwd(), 'data')

#BASE_LAYER_RESISTANCE = 100
BASE_LAYER_RESISTANCE = 10


PROPERTIES = [
             'knock_bonus',
             'knock_out_chance',
             'disarm_bonus',
             'disarm_defense',
             'bleed_chance',
             'pain_chance',
             'defense_bonus',
             'attack_bonus'
             ]

'''
WEAPON_PROPERTIES = {'sword':{'defense_bonus':5},
                     'dagger':{'bleed_chance':5},
                     'mace':{'knock_bonus':5},
                     'spear':{'attack_chance':5},
                     'axe':{'pain_chance':5}
                     }
'''

WEAPON_PROPERTIES = {'sword':{
                              'high swing': 10,
                              'middle swing': 15,
                              'low swing': 10,
                              'vertical swing': 10,
                              'high thrust': 5,
                              'middle thrust': 10,
                              'low thrust': 5
                              },
                     'dagger':{
                              'high swing': -20,
                              'middle swing': -20,
                              'low swing': -20,
                              'vertical swing': -20,
                              'high thrust': 15,
                              'middle thrust': 30,
                              'low thrust': 10
                              },
                     'mace':{
                              'high swing': 10,
                              'middle swing': 15,
                              'low swing': 0,
                              'vertical swing': 20,
                              'high thrust': -20,
                              'middle thrust': -20,
                              'low thrust': -20
                              },
                     'spear':{
                              'high swing': -10,
                              'middle swing': -20,
                              'low swing': -30,
                              'vertical swing': -30,
                              'high thrust': 20,
                              'middle thrust': 30,
                              'low thrust': 20
                              },
                     'axe':{
                              'high swing': 20,
                              'middle swing': 20,
                              'low swing': 0,
                              'vertical swing': 40,
                              'high thrust': -20,
                              'middle thrust': -20,
                              'low thrust': -20
                              }
                     }

class Weapon:
    def __init__(self, wtype, properties):
        self.wtype = wtype
        self.properties = properties


class WeaponGenerator:
    def __init__(self, blueprint_dict):#, creature):
        self.blueprint_dict = blueprint_dict
        # Will be used later so that different weapons for different creatures can be created
        #self.creature = creature

    def generate_weapon(self, wtype, material, special_properties):
        ''' Will take a weapon blueprint, vary some of the parameters, and return the full blueprint for the object '''

        # Important to deepcopy ths dict or bad things may happen (components/layers referencing the same object...)
        weapon_info_dict = copy.deepcopy(blueprint_dict[wtype])
        # Loop through all components to vary their parameters
        for component_name, component in weapon_info_dict['components'].iteritems():
            # Loop through all layers of the component
            for layer in component['layers']:
                # There is a "dimensions" tuple: width/height/depth/filled.
                # TODO - Vary this a bit. Also handle cases for multiple layers so they fit inside each other correctly
                ndims = []
                for dim in layer['dimensions']:
                    ndim = round(dim + (dim * (roll(0, 15)/100)), 3)
                    ndims.append(ndim)
                ndims = tuple(ndims)
                # Re-assign the new dimensions to the layer
                layer['dimensions'] = ndims

        # Properties specified just by the weapon type
        properties = WEAPON_PROPERTIES[wtype].copy()
        # Add any other special properties
        for wproperty, value in special_properties.iteritems():
            if wproperty in properties.keys():
                properties[wproperty] += value + random.choice((-10, -5, 0, 0, 10, 20))
            else:
                properties[wproperty] = value + random.choice((-10, -5, 0, 0, 10, 20))

        weapon_component = {'wtype':wtype, 'properties':properties}
        weapon_info_dict['weapon_component'] = weapon_component

        return weapon_info_dict



class Material:
    ''' Basic material instance '''
    def __init__(self, name, rgb_color, density, hardness, brittleness):
        self.name = name
        self.density = density
        self.color = libtcod.Color(*rgb_color)
        # 1 = soft, higher factors = harder
        self.hardness = hardness
        # 0 = soft (like flesh), 1 = very likely to shatter
        self.brittleness = brittleness


class MaterialLayer:
    ''' A layer of an object component '''
    def __init__(self, material, coverage, dimensions, inner_dimensions):
        self.material = material
        self.coverage = coverage

        # Tuple - (length, width, height, filled)
        # filled is the percentage (decimal) this occupies if it's not a complete cube
        self.dimensions = dimensions
        self.inner_dimensions = inner_dimensions

        self.health = 1

        # Will be filled in once the layer is added to an object component
        self.owner = None

        self.calculate_volume()
        self.calculate_mass()

    def get_name(self):
        return self.material.name

    def get_health(self):
        return self.health

    def calculate_inner_volume(self):
        ''' Inner volume (only used when storing objects '''
        iwidth, iheight, idepth, ifilled = self.inner_dimensions
        return ( (iwidth * iheight * idepth) * ifilled )

    def calculate_volume(self):
        ''' Calculate volume '''
        width, height, depth, filled = self.dimensions
        iwidth, iheight, idepth, ifilled = self.inner_dimensions

        assert (iwidth < width and iheight < height and idepth < depth)

        # Volume is width/height/depth
        self.volume = ( (width * height * depth) * filled ) - ( (iwidth * iheight * idepth) * ifilled )

    def calculate_mass(self):
        self.mass = self.volume * self.material.density


    def apply_force(self, other_obj_comp, total_force):
        ##############################################
        #### Apply force for object getting hit ######
        ##############################################
        ## total_force is the mass of the object, multiplied
        ## by the strength of the weilder or the speed at which
        ## it is travelling
        #layer_resistance = (BASE_LAYER_RESISTANCE * self.material.density) * (self.mass * self.material.resistance)
        #layer_resistance = BASE_LAYER_RESISTANCE * (self.material.density * (self.mass/2) * self.material.hardness)
        layer_resistance = BASE_LAYER_RESISTANCE * (self.material.density * (self.volume/2) * self.material.hardness)

        ## "Raw" damage based on mass/force of original weapon
        blunt_damage = total_force / layer_resistance
        #blunt_damage = 1

        ## Certain objects may be susceptible to additional effects by sharp objects
        sharpness = other_obj_comp.sharp


        self.take_damage(blunt_damage=blunt_damage, sharpness=sharpness)

        return total_force, layer_resistance, blunt_damage


    def take_damage(self, blunt_damage, sharpness):
        ''' The layer takes damage '''

        ## Handle blunt damage
        self.health = max(self.health - blunt_damage, 0) # Original testing ...
        #total_blunt_damage = blunt_damage * self.material.brittleness  # Never used...
        # Only apply damage if the material has any degree of brittleness
        #if self.material.brittleness > 0:
        #    total_blunt_damage = blunt_damage
        #    self.health = max(self.health - total_blunt_damage , 0)
        #####################

        # Handle sharpness damage
        # Sharpness has a big effect if the layer is not brittle
        # total_sharp_damage = (1 - self.material.brittleness) * sharpness

        # Experimental; for testing purposes
        #self.strip_coverage(damage)

        # A check to see if this object should be destroyed
        self.owner.check_integrity(blunt_damage, sharpness)


        if self.owner.owner and self.owner.owner.creature:
            # If it's alive
            self.owner.owner.creature.increment_pain(blunt_damage, sharpness)


    def strip_coverage(self, amount):
        ''' Will strip away coverage of this layer '''
        ## TODO - stripping coverage on lowest layer should actually start stripping volume
        if len(self.owner.layers) > 1:
            self.coverage = max(0, self.coverage - amount)


## The component that the object is made out of
class ObjectComponent:
    def __init__(self, name, layers, sharp, functions, attachment_info, wearing_info=None):
        self.name = name
        # Owner should be overwritten when object initializes
        self.owner = None

        ## Add layers
        self.layers = []
        for layer in layers:
            self.add_material_layer(layer, layer_is_inherent_to_object_component=True)

        # 'sharp' here is really a crude pressure simulator
        # The force of the weapon swing gets multiplied by the sharp value
        # Non-weapons have a value of ~1, blunt weapons higher, and pointy bits even higher
        self.sharp = sharp
        # The sharpness will get worn down, so this keeps track of how we can repair it
        self.maxsharp = sharp

        # Stuff attached to us
        self.attachments = []
        ## attachment_info should be (name_of_other_part, attach_strength)
        self.attachment_info = attachment_info
        self.attached_to = None
        self.attach_strength = None

        ## Convoluted code to help with clothing/wearing
        if wearing_info:
            self.bodypart_covered = wearing_info[0]
            self.bodypart_attached = wearing_info[1]
            self.bodypart_attach_strength = wearing_info[2]
        else:
            self.bodypart_covered = None
            self.bodypart_attached = None
            self.bodypart_attach_strength = None
        ###############################################

        self.storage = None
        ## functions, such as attaching, holding, or grasping
        self.functions = functions
        if 'storage' in self.functions:
            self.storage = []

        self.grasped_item = None

    def grasp_item(self, other_object):
        self.grasped_item = other_object
        other_object.being_grasped_by = self

        # Set current weapon status
        if other_object.weapon:
            self.owner.creature.current_weapon = other_object

    def remove_grasp_on_item(self, other_object):
        self.grasped_item = None
        other_object.being_grasped_by = None

        # Remove current weapon status
        if other_object.weapon:
            self.owner.creature.current_weapon = None

    def check_integrity(self, blunt_damage, sharpness):
        ''' Will destroy this object if no layer has high enough health '''
        # TODO - highly brittle items can shatter
        integrity_maintained = 0

        for layer in self.layers:
            if layer.health >= .25:
                integrity_maintained = 1
                break

        if not integrity_maintained:
            self.owner.destroy_component(self)
            #print 'Need to handle object integrity disintegrating'


    def get_storage_volume(self):
        ''' Hopefully this is a storage object '''
        assert self.storage is not None, 'Attempted to get inner volume of non-storage object'

        available_volume = self.layers[-1].calculate_inner_volume()

        for item in self.storage:
            for component in item.components:
                available_volume -= component.get_volume()

        return available_volume


    def add_object_to_storage(self, other_object):
        assert self.storage is not None

        self.storage.append(other_object)
        other_object.inside = self

    def remove_object_from_storage(self, other_object):
        assert other_object.inside == self

        self.storage.remove(other_object)
        other_object.inside = None


    def get_coverage_layers(self):
        ''' Return the possible layers which are exposed to the outside
            Returns a list of tuples like (layer, coverage percentage) '''
        layers = []
        layer_index = 0
        # Check the outermost layer, and go down until you hit one with coverage of 1,
        # Or have gone through all layers
        while len(layers) != len(self.layers):
            layer_index -= 1

            outer_layer = self.layers[layer_index]
            layers.append( (outer_layer, outer_layer.coverage) )

            # Keep iterating until the topmost totally covered layer is reached
            if outer_layer.coverage == 1:
                break

        return layers

    def add_material_layer(self, layer, layer_is_inherent_to_object_component=0):
        ''' layer_is_ ... variable will be false if this is a piece of clothing or something '''
        self.layers.append(layer)
        if layer_is_inherent_to_object_component:
            layer.owner = self

    def remove_material_layer(self, layer):
        ''' Standard removal of a clothing layer '''
        self.layers.remove(layer)


    def attach_to(self, other_component, attach_strength):
        ''' Attach to an object component, with a certain strength '''
        other_component.attachments.append(self)
        self.attached_to = other_component
        self.attached_strength = attach_strength

    def disattach_from(self, other_component):
        ''' Disattach from an object component '''
        other_component.attachments.remove(self)
        self.attached_to = None
        self.attached_strength = None


    def get_mass(self):
        ''' Get mass of this component by totalling mass of layers '''
        mass = 0
        for layer in self.layers:
            mass += layer.mass
        return mass

    def get_volume(self):
        volume = 0
        for layer in self.layers:
            volume += layer.volume
        return volume

    def get_density(self):
        mass = self.get_mass()
        volume = self.get_volume()

        return mass / volume


def assemble_components(clist, force_material=None):
    ''' Assembles an objects' components based on an input dictionary '''

    components = []
    for component_name, component in clist.iteritems():

        layers = []

        for clayer in component['layers']:
            ## Figure out what material to use
            ## force_material will overwrite whatever was stored in the "canon" component list
            ## TODO - flesh out better ways which layers/components can be stored (such as storing possible types of materials they can be made from)
            if force_material:
                material = force_material
            else:
                material = materials[clayer['material_tokens'][0]]

            ## Create the material layer
            layer = MaterialLayer(material=material, coverage=clayer['coverage'], dimensions=clayer['dimensions'], inner_dimensions=clayer['inner_dimensions'])
            layers.append(layer)

        ## Now that we have the layers, create the component
        new_component = ObjectComponent(name=component_name, layers=layers, sharp=component['sharp'],
                                        functions=[function for function in component['functions']], attachment_info=component['attachment_info'],
                                        wearing_info=component['wearing_info'])

        components.append(new_component)

    return components



def import_object_xml(file_path):
    # TODO - ignore non-xml entries
    object_files = os.listdir(file_path)

    object_dict = {}

    for ofile in object_files:
        obj_tree = etree.parse(os.path.join(file_path, ofile))
        obj_root = obj_tree.getroot()

        for obj in obj_root.findall('object'):
            #print obj
            # Start off by finding basic stuff

            # If a char is an integer, intepret it as being the index of the tileset
            try:    char = int(obj.findtext('char'))
            except: char = obj.findtext('char')
            # Figure out the color
            color = obj.findtext('color')
            if color != 'use_material':
                color = map(int, color.split(', '))
                color = libtcod.Color(*color)

            current_obj = {
                'name':obj.findtext('name'),
                'char':char,
                'color':color,
                'blocks_mov':int(obj.findtext('blocks_mov')),
                'blocks_vis':int(obj.findtext('blocks_vis')),
                'description':obj.findtext('description'),
                'weapon_component':obj.findtext('weapon_component'),
                'components':{}
                }

            ## Prune the input to correct "None" strings
            if current_obj['weapon_component'] == 'None':
                current_obj['weapon_component'] = None


            for component in obj.find('components'):
                # Go through each body part to pull out all the info
                component_name = component.findtext('name')
                attaches_to = component.findtext('attaches_to')
                # Probably need to find a better way to parse things with no attachments
                if attaches_to == 'None':
                    attaches_to = None
                    attach_strength = None
                else:
                    attach_strength = float(component.findtext('attach_strength'))

                sharp = float(component.findtext('sharp'))

                wearing_info = component.findtext('wearing_info')
                if wearing_info == '0':
                    wearing_info = None

                ## Find the functions the part is used for ##
                funct_list = []
                functions = component.find('functions')

                for f in functions:
                    funct_list.append(f.text)

                ## Each component can be made up of several layers ##
                imp_layers = component.find('layers')
                layers = []
                for i, layer in enumerate(imp_layers):
                    ### Bottom layer has no "inner" dimensions,
                    ### Proceeding layers have the outer dimensions of the previous layer
                    if i == 0: inner_dimensions = (0, 0, 0, 0)
                    else:      inner_dimensions = layers[i-1]['dimensions']

                    ## Find material type, and dimensions of layer
                    material_types = []
                    material_tokens = []

                    for mtype in layer.find('material_types'):
                        material_types.append(mtype.text)
                    for mtoken in layer.find('material_tokens'):
                        material_tokens.append(mtoken.text)

                    coverage = float(layer.findtext('coverage'))
                    ## Dimensions of the body part
                    width = float(layer.findtext('width'))
                    height = float(layer.findtext('height'))
                    depth = float(layer.findtext('depth'))
                    filled = float(layer.findtext('filled'))

                    # Turn the raw info from xml into a legit layer
                    dimensions = (width, height, depth, filled)

                    #newlayer = MaterialLayer(material=materials[material], coverage=1, dimensions=dimensions, inner_dimensions=inner_dimensions)
                    newlayer = {'material_types':material_types, 'material_tokens':material_tokens,
                                'coverage':coverage, 'dimensions':dimensions, 'inner_dimensions':inner_dimensions}

                    # Add to list of layers
                    layers.append(newlayer)

                current_obj['components'][component_name] = {'layers':layers, 'attachment_info':(attaches_to, attach_strength),
                                                             'wearing_info':wearing_info, 'sharp':sharp, 'functions':funct_list}

                ###### Find possible materials ########
                material_tokens = []
                for component_name, component in current_obj['components'].iteritems():
                    for layer in component['layers']:
                        for material_token in layer['material_tokens']:
                            if material_token not in material_tokens:
                                material_tokens.append(material_token)

                        for material_type in layer['material_types']:
                            for material_token in econ.RESOURCE_TYPES[material_type]:
                                if material_token not in material_tokens:
                                    material_tokens.append(material_token)

                current_obj['possible_materials'] = material_tokens
                #########################################

            object_dict[obj.findtext('name')] = current_obj

    return object_dict


def get_valid_assembly_materials(object_name, object_dict):
    ''' Given a blueprint, this tells us what the components can be made out of
        Returns a dict, formatted {component:['valid', 'component', 'materials']} '''

    # object_dict should be either self.object_dict or self.blueprint_dict
    obj = object_dict[object_name]

    component_materials = {}
    # Loop through all components and add the tokens of resources which can be used to create it
    for component_name, component in obj['components'].iteritems():

        for layer in component['layers']:
            layer_valid_materials = []

            # Tokens are specific materials/resources
            for token in layer['material_tokens']:
                layer_valid_materials.append(token)

            # Types are higher up in the hierarchy, such as "ores"
            for rtype in layer['material_types']:
                for token in econ.RESOURCE_TYPES[rtype]:
                    layer_valid_materials.append(token.name)

        component_materials[component_name] = layer_valid_materials

    return component_materials


def cache_basic_weapon_types():
    basic_weapon_types = []
    ''' To save a bit of time, this will check all weapon types to see what can be made entirely out of wood '''
    # Loop through all weapons which were imported into the blueprint dict
    for weapon_name in blueprint_dict.keys():
        # Flag, which will be set to 0 if the weapon has a component that can't be made out of wood
        weapon_is_basic = 1
        # This returns a dict, formatted {component:['valid', 'component', 'materials']}
        materials = get_valid_assembly_materials(object_name=weapon_name, object_dict=blueprint_dict)
        # Now loop through and check whether wood is a valid material
        for component_name, materials in materials.iteritems():
            if not 'wood' in materials:
                weapon_is_basic = 0
                break

        # If is in fact a basic weapon, it goes into the list
        if weapon_is_basic:
            basic_weapon_types.append(weapon_name)

    return basic_weapon_types

def main():
    global creature_dict, object_dict, blueprint_dict, wgenerator, basic_weapon_types
    global shirtcomps, packcomps, doorcomps, materials
    # Grab yaml file and convert it to a dictionary
    with open(os.path.join(YAML_DIRECTORY, 'materials.yml')) as m:
        loaded_materials = yaml.load(m)

    materials = {}
    for material_name in loaded_materials.keys():
        materials[material_name] = Material(name=material_name, rgb_color=loaded_materials[material_name]['rgb_color'],
                                       density=loaded_materials[material_name]['density'], hardness=loaded_materials[material_name]['hardness'],
                                       brittleness=loaded_materials[material_name]['brittleness'])

    #### Load XML ######
    file_path = os.path.join(os.getcwd(), 'XML', 'creatures')
    creature_dict = import_object_xml(file_path)

    opath = os.path.join(os.getcwd(), 'XML', 'objects')
    object_dict = import_object_xml(opath)

    bpath = os.path.join(os.getcwd(), 'XML', 'object_blueprints')
    blueprint_dict = import_object_xml(bpath)
    ###################

    wgenerator = WeaponGenerator(blueprint_dict=blueprint_dict)

    basic_weapon_types = cache_basic_weapon_types()


    bone = materials['bone']
    flesh = materials['flesh']
    wood = materials['wood']
    cloth = materials['cloth']
    iron = materials['iron']

    bone_layer = MaterialLayer(material=bone, coverage=1, dimensions=(.01, .01, .8, .9), inner_dimensions=(0, 0, 0, 0) )
    flesh_layer = MaterialLayer(material=flesh, coverage=1, dimensions=(.02, .02, .9, .9), inner_dimensions=(.01, .01, .8, .9) )

    arm = ObjectComponent(name='arm', layers=[bone_layer, flesh_layer], sharp=1, functions=[], attachment_info=(None, None))


    iron_layer = MaterialLayer(material=iron, coverage=1, dimensions=(.08, .01, 1, .9), inner_dimensions=(0, 0, 0, 0) )
    iron_blade = ObjectComponent(name='sword', layers=[iron_layer], sharp=1.1, functions=[], attachment_info=(None, None) )
    swordcomps = [iron_blade]

    #iron_layer2 = MaterialLayer(material=iron, coverage=1, dimensions=(.08, .01, 1, .9), inner_dimensions=(0, 0, 0, 0) )

    force = iron_blade.get_mass()
    #print force

    flesh_layer.apply_force(other_obj_comp=iron_blade, total_force=force)
    #iron_layer2.apply_force(other_obj_comp=iron_blade, total_force=force)

    #print flesh_layer.mass
    #print iron_blade.get_mass()
    #print flesh_layer.health
    #print ''
    #print iron_layer2.health


    ## stuff
    wood_layer = [MaterialLayer(material=wood, coverage=1, dimensions=(1, 1, 1, 1), inner_dimensions=(0, 0, 0, 0) )]
    wood_component = ObjectComponent(name='wood', layers=wood_layer, sharp=1, functions=['wall'], attachment_info=(None, None))
    wallcomps = [wood_component]

    wood_layer2 = [MaterialLayer(material=wood, coverage=1, dimensions=(1, .1, 1, 1), inner_dimensions=(0, 0, 0, 0) )]
    wood_component2 = ObjectComponent(name='wood', layers=wood_layer2, sharp=1, functions=['door'], attachment_info=(None, None))
    doorcomps = [wood_component2]

    ### For testing purposes - a shirt
    clothing_layer = MaterialLayer(material=cloth, coverage=.6, dimensions=(.45, .8, .25, .75), inner_dimensions=(.4, .7, .2, .75) )
    clothing_layer2 = MaterialLayer(material=cloth, coverage=.4, dimensions=(.2, .6, .1, .75), inner_dimensions=(.15, .55, .05, .75) )
    clothing_layer3 = MaterialLayer(material=cloth, coverage=.4, dimensions=(.2, .6, .1, .75), inner_dimensions=(.15, .55, .05, .75) )

    #clothing_layer = MaterialLayer(material=iron, coverage=.6, dimensions=(.45, .8, .25, .75), inner_dimensions=(.4, .7, .2, .75) )
    #clothing_layer2 = MaterialLayer(material=iron, coverage=.4, dimensions=(.2, .6, .1, .75), inner_dimensions=(.15, .55, .05, .75) )
    #clothing_layer3 = MaterialLayer(material=iron, coverage=.4, dimensions=(.2, .6, .1, .75), inner_dimensions=(.15, .55, .05, .75) )

    shirt_component = ObjectComponent(name='torso', layers=[clothing_layer], sharp=1, functions=[], attachment_info=(None, None), wearing_info=('torso', None, None) )
    shirt_component2 = ObjectComponent(name='right arm', layers=[clothing_layer2], sharp=1, functions=[], attachment_info=('torso', 100), wearing_info=('right arm', None, None))
    shirt_component3 = ObjectComponent(name='left arm', layers=[clothing_layer3], sharp=1, functions=[], attachment_info=('torso', 100), wearing_info=('left arm', None, None) )
    shirtcomps = [shirt_component, shirt_component2, shirt_component3]
    ####################################
    clothing_layer4 = [MaterialLayer(material=cloth, coverage=1, dimensions=(.35, .45, .35, .95), inner_dimensions=(.3, .4, .3, .95) )]
    pack_component = ObjectComponent(name='pack', layers=clothing_layer4, sharp=1, functions=['storage'], attachment_info=(None, None), wearing_info=(None, 'torso', 100) )
    packcomps = [pack_component]

if __name__ == '__main__':
    econ.setup_resources()
    main()


