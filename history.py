from __future__ import division
import config as g
from helpers import determine_commander, join_list

historical_events = []
event_id = 0

class HistoricalEvent:
    def __init__(self, date, location):
        ''' The base HistoricalEvent class that all others inherit from '''
        global event_id
        self.date = date
        self.location = location

        # Most events (marriages, births, traveling) have low base importance - but the event may be considered important if the people in it are famous
        self.base_importance = 0
        self.id_ = event_id
        event_id += 1

        g.WORLD.tiles[self.location[0]][self.location[1]].associated_events.add(self.id_)
        self.save_event()

    def save_event(self):
        historical_events.append(self)

    def describe_location(self):
        return g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description()

    def get_importance(self):
        ''' Get importance of the event. Uses get_entities() which returns all associated entities, defined in each individual event '''
        importance = self.base_importance
        for entity in self.get_entities():
            importance += entity.infamy

        return importance

class Marriage(HistoricalEvent):
    def __init__(self, date, location, figures):
        HistoricalEvent.__init__(self, date, location)
        self.figures = figures

        for figure in self.get_entities():
            figure.add_associated_event(event_id=self.id_)

    def describe(self):
        des = 'On {0}, {1} married {2}'.format(g.WORLD.time_cycle.date_to_text(self.date), self.figures[0].fulltitle(), self.figures[1].fulltitle())
        return des

    def get_entities(self):
        return self.figures

class Birth(HistoricalEvent):
    def __init__(self, date, location, parents, child):
        HistoricalEvent.__init__(self, date, location)
        self.parents = parents
        self.child = child

        for figure in self.get_entities():
            figure.add_associated_event(event_id=self.id_)

    def describe(self):
        des = 'On {0}, {1} was born to {2}'.format(g.WORLD.time_cycle.date_to_text(self.date), self.child.fullname(), join_list([p.fulltitle() for p in self.parents]))
        return des

    def get_entities(self):
        return self.parents + [self.child]


class TravelStart(HistoricalEvent):
    def __init__(self, date, location, to_location, figures, populations, reason=None):
        HistoricalEvent.__init__(self, date, location)

        self.to_location = to_location
        self.figures = figures
        self.commander = determine_commander(self.figures)
        self.populations = populations
        self.reason = reason

        for figure in self.get_entities():
            figure.add_associated_event(event_id=self.id_)

    def describe(self):
        des = 'On {0}, {1} set out for {2} from {3}'.format(g.WORLD.time_cycle.date_to_text(self.date), self.commander.fulltitle(),
                                                            g.WORLD.tiles[self.to_location[0]][self.to_location[1]].get_location_description(),
                                                            g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description() )
        return des

    def get_entities(self):
        return self.figures

class TravelEnd(HistoricalEvent):
    def __init__(self, date, location, figures, populations):
        HistoricalEvent.__init__(self, date, location)

        self.figures = figures
        self.commander = determine_commander(self.figures)
        self.populations = populations

        for figure in self.get_entities():
            figure.add_associated_event(event_id=self.id_)

    def describe(self):
        des = 'On {0}, {1} arrived at {2}'.format(g.WORLD.time_cycle.date_to_text(self.date), self.commander.fulltitle(), self.describe_location())
        return des

    def get_entities(self):
        return self.figures