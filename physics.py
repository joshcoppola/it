from __future__ import division
import os
import economy as econ
import copy
import yaml
from collections import defaultdict

import random
from random import randint as roll
import libtcodpy as libtcod
from helpers import join_list, ct, infinite_defaultdict

import economy as econ

YAML_DIRECTORY = os.path.join(os.getcwd(), 'data')


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
        for component in weapon_info_dict['components']:
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
            if wproperty in properties:
                properties[wproperty] += value + random.choice((-10, -5, 0, 0, 10, 20))
            else:
                properties[wproperty] = value + random.choice((-10, -5, 0, 0, 10, 20))

        weapon_component = {'wtype':wtype, 'properties':properties}
        weapon_info_dict['weapon_component'] = weapon_component

        return weapon_info_dict


class Wound:
    def __init__(self, owner, damage_type, damage):
        self.owner = owner
        self.damage_type = damage_type
        self.damage = damage



class Material:
    ''' Basic material instance '''
    def __init__(self, name, rgb_color, density, rigid, force_diffusion, slice_resistance):
        self.name = name
        self.density = density
        self.color = libtcod.Color(*rgb_color)
        self.rigid = rigid
        self.force_diffusion = force_diffusion
        # 0 = soft (like flesh), 1 = very likely to shatter
        self.slice_resistance = slice_resistance


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
        # Wounds can be scratches, fractures... anything that needs to be fixed
        self.wounds = []

        # Will be filled in once the layer is added to an object component
        self.owner = None

        self.volume = None
        self.mass = None
        self.thickness = None

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

        # Thickness of the layer = (each inner layer - each outer layer / 3) [[average thickness]] divided by 2 since for each dimension, the layer has 2 sides
        self.thickness = (sum([width-iwidth, height-iheight, depth-idepth])/3)/2

        ## TODO- fix ugly ugly test code
        if self.material.rigid:
            self.blunt_resistance = self.thickness * self.material.density * 10
        else:
            self.absorbtion = self.thickness * self.material.density * self.material.force_diffusion

    def calculate_mass(self):
        self.mass = self.volume * self.material.density


    def apply_force_to_layer(self, blunt_force, sharpness_force):

        wound = '(no wound)'
        ## Handle blunt damage attempting to break the material
        if self.material.rigid and blunt_force > self.blunt_resistance:
            overflow_damage = blunt_force - self.blunt_resistance

            #wound = 'fracture ({0:.01f})'.format(overflow_damage)
            self.add_wound(damage_type='blunt', damage=overflow_damage)

            remaining_blunt_force = 0
            remaining_sharpness_force = 0

        ## Handle sharpness slicing into the material
        elif (not self.material.rigid) and sharpness_force > self.material.slice_resistance:
            overflow_damage = sharpness_force - self.material.slice_resistance

            #wound = 'cut ({0:.01f})'.format(overflow_damage)
            self.add_wound(damage_type='slash', damage=overflow_damage)

            remaining_blunt_force = blunt_force / max(self.absorbtion, 1)
            remaining_sharpness_force = overflow_damage

        ## Blunt damage doesn't overcome blunt resistance or sharp damage doesn't overcome slice resistance
        else:
            remaining_blunt_force = 0
            remaining_sharpness_force = 0
            #print 'no damage!'


        # A check to see if this object should be destroyed
        #self.owner.check_integrity(blunt_damage, sharpness)
        #print '{1} ({0}) takes {2},  [ {3:.01f} blunt and {4:.01f} sharpness came in, {5:.01f} blunt and {6:.01f} sharpness remain]'.format(self.owner.owner.fullname(), self.get_name(), wound, blunt_force, sharpness_force, remaining_blunt_force, remaining_sharpness_force)

        return remaining_blunt_force , remaining_sharpness_force

    def add_wound(self, damage_type, damage):

        wound = Wound(owner=self, damage_type=damage_type, damage=damage)
        self.wounds.append(wound)

        # If this belongs to a creature
        if self.owner.owner and self.owner.owner.creature:
            #self.owner.owner.creature.increment_pain(.2, 1)
            self.owner.owner.creature.evaluate_wounds()

    def get_wound_descriptions(self):
        light_wounds = 0
        medium_wounds = 0
        serious_wounds = 0
        grievous_wounds = 0

        for wound in self.wounds:
            if wound.damage <= 20:
                light_wounds += 1
            elif wound.damage <= 50:
                medium_wounds += 1
            elif wound.damage <= 80:
                serious_wounds += 1
            else:
                grievous_wounds += 1

        wound_list = []
        if light_wounds > 0:
            wound_list.append(ct('light wound', light_wounds))
        if medium_wounds > 0:
            wound_list.append(ct('medium wound', medium_wounds))
        if serious_wounds > 0:
            wound_list.append(ct('serious wound', serious_wounds))
        if grievous_wounds > 0:
            wound_list.append(ct('grievous wound', grievous_wounds))

        return join_list(wound_list)


    def strip_coverage(self, amount):
        ''' Will strip away coverage of this layer '''
        ## TODO - stripping coverage on lowest layer should actually start stripping volume
        if len(self.owner.layers) > 1:
            self.coverage = max(0, self.coverage - amount)


## The component that the object is made out of
class ObjectComponent:
    def __init__(self, name, layers, sharp, tags, attachment_info, position=None, wearing_info=None):
        self.name = name
        # Owner should be overwritten when object initializes
        self.owner = None

        ## Add layers
        self.layers = []
        for layer in layers:
            self.add_material_layer(layer, layer_is_inherent_to_object_component=True)

        self.sharp = sharp
        # The sharpness will get worn down, so this keeps track of how we can repair it
        self.maxsharp = sharp

        # Stuff attached to us
        self.attachments = []
        ## attachment_info should be (name_of_other_part, attach_strength)
        self.attachment_info = attachment_info
        self.attached_to = None
        self.attach_strength = None

        self.position = position
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

        # Any text written or engraved on the component
        self.text = defaultdict(list)
        # Any text that carries some written or engraved information on the component
        self.information = infinite_defaultdict()

        self.storage = None
        ## tags, such as attaching, holding, or grasping
        self.tags = tags
        if 'storage' in self.tags:
            self.storage = []

        self.grasped_item = None

    def add_text(self, method, language, text):
        # Method = how it's written (etched, ink, etc)
        if not method in self.text:
            self.text[method] = {}

        self.text[method][language].append(text)

    def add_person_location_information(self, language, person, date_written, date_at_loc, location, author):
        ''' Updates knowledge of the last time we learned about the location of the other '''
        self.information[language]['entities'][person]['location']['coords'] = location
        self.information[language]['entities'][person]['location']['date_written'] = date_written
        self.information[language]['entities'][person]['location']['date_at_loc'] = date_at_loc
        self.information[language]['entities'][person]['location']['author'] = author
        #self.information[language]['entities'][person]['location']['heading'] = heading
        #self.knowledge['entities'][person]['location']['destination'] = destination

    def add_information_of_event(self, language, event_id, date_written, author, location_accuracy=1):
        self.information[language]['events'][event_id] = {'description': {}, 'location': {} }

        self.information[language]['events'][event_id]['description']['date_written'] = date_written
        self.information[language]['events'][event_id]['description']['source'] = author

        self.information[language]['events'][event_id]['location']['accuracy'] = location_accuracy
        self.information[language]['events'][event_id]['location']['date_written'] = date_written
        self.information[language]['events'][event_id]['location']['source'] = author

    def add_information_of_site(self, language, site, date_written, author, location_accuracy=1, is_part_of_map=1, describe_site=0):
        #self.information[language]['sites'][site] = {'description': {}, 'location': {} }

        # Add some stuff describing the site
        if describe_site:
            self.information[language]['sites'][site]['description']['date_written'] = date_written
            self.information[language]['sites'][site]['description']['source'] = author

        self.information[language]['sites'][site]['location']['accuracy'] = location_accuracy
        self.information[language]['sites'][site]['location']['is_part_of_map'] = is_part_of_map
        self.information[language]['sites'][site]['location']['date_written'] = date_written
        self.information[language]['sites'][site]['location']['source'] = author



    def apply_force(self, other_obj_comp, total_force, targeted_layer):
        remaining_blunt_force = total_force * other_obj_comp.sharp
        remaining_sharpness_force = total_force

        begin_applying_force = 0
        for layer in reversed(self.layers):
            if layer == targeted_layer:
                begin_applying_force = 1

            # Once force application is set to begin, keep applying force to layers until there's nothing left to apply
            if begin_applying_force:
                #print other_obj_comp.name, 'applying force to', layer.get_name()
                remaining_blunt_force, remaining_sharpness_force = layer.apply_force_to_layer(remaining_blunt_force, remaining_sharpness_force)
                #print '- Remaining:', remaining_blunt_force, remaining_sharpness_force
            # Stop once there's no more force
            if remaining_blunt_force == 0 and remaining_sharpness_force == 0:
                break
        #print ' '

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

    def get_chances_to_hit_exposed_layers(self):
        ''' Originally was written elsewhere, essentially duplicates the get_coverage_layers() method
            Should refactor to make flow clearer and not need to use the above tag '''
        chances_to_hit = []
        running_coverage_amt = 0
        for layer, coverage_amt in self.get_coverage_layers():
            # Chance to hit is this layer's coverage minus previous layer's coverage
            # Exception - if this layer's coverage is smaller, it's essentially un-hittable
            # TODO - ensure that chance_to_hit and running_coverage_amt work correctly with layers with weird cvg amounts
            chance_to_hit = max(coverage_amt, running_coverage_amt) - running_coverage_amt
            running_coverage_amt += chance_to_hit

            chances_to_hit.append((layer, chance_to_hit))

        return chances_to_hit

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
    for component in clist:
        component_name = component['name']
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
                                        tags=[tag for tag in component['tags']], attachment_info=component['attachment_info'],
                                        position=component['position'], wearing_info=component['wearing_info'])

        components.append(new_component)

    return components


def import_object_yml(file_path):
    # TODO - ignore non-xml entries
    object_files = os.listdir(file_path)

    object_dict = {}

    for ofile in object_files:

        with open(os.path.join(file_path, ofile)) as yaml_file:
            objects = yaml.load(yaml_file)

        for obj in objects:

            object_dict[obj] = objects[obj]
            object_dict[obj]['name'] = obj
            object_dict[obj]['tags'] = set([])

            if object_dict[obj]['color'] != 'use_material':
                object_dict[obj]['color'] = libtcod.Color(*object_dict[obj]['color'])

            for component in object_dict[obj]['components']:
                component['attachment_info'] = (component['attaches_to'], component['attach_strength'])

                imp_layers = component['layers']
                layers = []
                for i, layer in enumerate(imp_layers):
                    ### Bottom layer has no "inner" dimensions,
                    ### Proceeding layers have the outer dimensions of the previous layer
                    if i == 0 and layer['layer_thickness'] is None:
                        inner_dimensions = (0, 0, 0, 0)
                    # If we've defined a thickness in the yaml, we can find the inner dimensions by subtracking the thickness
                    elif i == 0 and layer['layer_thickness'] is not None:
                        w = layer['dimensions'][0] - layer['layer_thickness']
                        h = layer['dimensions'][1] - layer['layer_thickness']
                        d = layer['dimensions'][2] - layer['layer_thickness']
                        f = layer['dimensions'][3]
                        inner_dimensions = (w, h, d, f)
                    # If iteration > 0, we can just use the previous layer's outer dimensions
                    else:
                        inner_dimensions = component['layers'][i-1]['dimensions']

                    component['layers'][i]['inner_dimensions'] = inner_dimensions

                ###### Find possible materials ########
                material_tokens = []
                for _component in object_dict[obj]['components']:
                    for layer in _component['layers']:
                        for material_token in layer['material_tokens']:
                            if material_token not in material_tokens:
                                material_tokens.append(material_token)

                        for material_type in layer['material_types']:
                            for material_token in econ.commodity_manager.get_commodities_of_type(material_type):
                                if material_token not in material_tokens:
                                    material_tokens.append(material_token)

                object_dict[obj]['possible_materials'] = material_tokens

                for tag in component['tags']:
                    object_dict[obj]['tags'].add(tag)
                #########################################

    #for o in object_dict.keys():
    #    print o, object_dict[o]

    return object_dict


def get_valid_assembly_materials(object_name, object_dict):
    ''' Given a blueprint, this tells us what the components can be made out of
        Returns a dict, formatted {component:['valid', 'component', 'materials']} '''

    # object_dict should be either self.object_dict or self.blueprint_dict
    obj = object_dict[object_name]

    component_materials = {}
    # Loop through all components and add the tokens of resources which can be used to create it
    for component in obj['components']:
        component_name = component['name']

        for layer in component['layers']:
            layer_valid_materials = []

            # Tokens are specific materials/resources
            for token in layer['material_tokens']:
                layer_valid_materials.append(token)

            # Types are higher up in the hierarchy, such as "ores"
            for rtype in layer['material_types']:
                for token in econ.commodity_manager.get_commodities_of_type(rtype):
                    layer_valid_materials.append(token.name)

        component_materials[component_name] = layer_valid_materials

    return component_materials


def cache_basic_weapon_types():
    basic_weapon_types = []
    ''' To save a bit of time, this will check all weapon types to see what can be made entirely out of wood '''
    # Loop through all weapons which were imported into the blueprint dict
    for weapon_name in blueprint_dict:
        # Flag, which will be set to 0 if the weapon has a component that can't be made out of wood
        weapon_is_basic = 1
        # This returns a dict, formatted {component:['valid', 'component', 'materials']}
        w_materials = get_valid_assembly_materials(object_name=weapon_name, object_dict=blueprint_dict)
        # Now loop through and check whether wood is a valid material
        for component_name, valid_materials in w_materials.iteritems():
            if not 'wood' in valid_materials:
                weapon_is_basic = 0
                break

        # If is in fact a basic weapon, it goes into the list
        if weapon_is_basic:
            basic_weapon_types.append(weapon_name)

    return basic_weapon_types

def main():
    global creature_dict, object_dict, blueprint_dict, wgenerator, basic_weapon_types, materials
    # Grab yaml file and convert it to a dictionary
    with open(os.path.join(YAML_DIRECTORY, 'materials.yml')) as m:
        loaded_materials = yaml.load(m)

    materials = {}
    for material_name in loaded_materials:
        materials[material_name] = Material(name=material_name, rgb_color=loaded_materials[material_name]['rgb_color'],
                                       density=loaded_materials[material_name]['density'], rigid=loaded_materials[material_name]['rigid'],
                                       force_diffusion=loaded_materials[material_name]['force_diffusion'],
                                       slice_resistance=loaded_materials[material_name]['slice_resistance'])

    #### Load XML ######
    file_path = os.path.join(os.getcwd(), 'data', 'creatures')
    creature_dict = import_object_yml(file_path)

    opath = os.path.join(os.getcwd(), 'data', 'objects')
    object_dict = import_object_yml(opath)

    bpath = os.path.join(os.getcwd(), 'data', 'object_blueprints')
    blueprint_dict = import_object_yml(bpath)
    ###################

    wgenerator = WeaponGenerator(blueprint_dict=blueprint_dict)

    basic_weapon_types = cache_basic_weapon_types()


if __name__ == '__main__':
    econ.setup_resources()
    main()


