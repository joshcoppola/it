from __future__ import division
import config as g


class HistoricalEvent:
    def __init__(self, id_, year, location):
        self.id_ = id_
        self.year = year
        self.location = location