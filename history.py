from __future__ import division
import config as g

historical_events = []
event_id = 0

class HistoricalEvent:
    def __init__(self, date, location):
        global event_id
        self.date = date
        self.location = location

        self.id_ = event_id
        event_id += 1

        self.save_event()

    def save_event(self):
        historical_events.append(self)

    def describe_location(self):
        return g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description()


class TravelStart(HistoricalEvent):
    def __init__(self, date, location, to_location, figure, reason=None):
        HistoricalEvent.__init__(self, date, location)

        self.to_location = to_location
        self.figure = figure
        self.reason = reason

    def describe(self):
        des = 'On {0}, {1} set out for {2} from {3}'.format(g.WORLD.time_cycle.get_current_date(), self.figure.fullname(),
                                                            g.WORLD.tiles[self.to_location[0]][self.to_location[1]].get_location_description(),
                                                            g.WORLD.tiles[self.location[0]][self.location[1]].get_location_description() )
        return des


class TravelEnd(HistoricalEvent):
    def __init__(self, date, location, figure):
        HistoricalEvent.__init__(self, date, location)

        self.figure = figure

    def describe(self):
        des = 'On {0}, {1} arrived at {2}'.format(g.WORLD.time_cycle.get_current_date(), self.figure.fullname(), self.describe_location())
        return des
