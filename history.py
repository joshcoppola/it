from __future__ import division
import config as g
from helpers import determine_commander

historical_events = []
event_id = 0

class HistoricalEvent:
    def __init__(self, date, location):
        global event_id
        self.date = date
        self.location = location

        self.id_ = event_id
        event_id += 1

        g.WORLD.tiles[self.location[0]][self.location[1]].associated_events.add(self.id_)
        self.save_event()

    def save_event(self):
        historical_events.append(self)

    def describe_location(self):
        return g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description()


class Marriage(HistoricalEvent):
    def __init__(self, date, location, figures):
        HistoricalEvent.__init__(self, date, location)
        self.figures = figures

    def describe(self):
        des = 'On {0}, {1} married {2}'.format(self.date, self.figures[0].fulltitle(), self.figures[1].fulltitle())
        return des

class TravelStart(HistoricalEvent):
    def __init__(self, date, location, to_location, figures, populations, reason=None):
        HistoricalEvent.__init__(self, date, location)

        self.to_location = to_location
        self.figures = figures
        self.commander = determine_commander(self.figures)
        self.populations = populations
        self.reason = reason

        for figure in self.figures:
            figure.associated_events.add(self.id_)

    def describe(self):
        des = 'On {0}, {1} set out for {2} from {3}'.format(self.date, self.commander.fullname(),
                                                            g.WORLD.tiles[self.to_location[0]][self.to_location[1]].get_location_description(),
                                                            g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description() )
        return des


class TravelEnd(HistoricalEvent):
    def __init__(self, date, location, figures, populations):
        HistoricalEvent.__init__(self, date, location)

        self.figures = figures
        self.commander = determine_commander(self.figures)
        self.populations = populations

        for figure in self.figures:
            figure.associated_events.add(self.id_)

    def describe(self):
        des = 'On {0}, {1} arrived at {2}'.format(self.date, self.commander.fullname(), self.describe_location())
        return des
