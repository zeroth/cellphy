from collections import OrderedDict
import numpy as np
from cellphy.Analysis.functions import distance


class Track:
    def __init__(self, track_id, name, color, suffix, raw_data=None, parent=None):
        self.parent = parent
        self.track_id = track_id
        self.raw_data = raw_data.copy().reset_index(drop=True)
        self.suffix = suffix
        self.color = color
        self.time_point_index_map = {}
        self.time_point_position_map = {}
        self.name = f'{name}-{self.track_id}'
        self.time_position_map = {}
        _time_position_map = {}
        for index, row in self.raw_data.iterrows():
            _time_position_map[int(row[['time']])] = list(row[[f'X{self.suffix}', f'Y{self.suffix}', f'Z{self.suffix}']])
        self.time_position_map = OrderedDict(sorted(_time_position_map.items(), key=lambda t: t[0]))

    def __str__(self):
        return f'{self.track_id}-{self.suffix}'

    def get_track_id(self):
        return self.track_id

    def get_values(self):
        return self.raw_data

    def get_position_by_time_point(self, time_point):
        if time_point in self.time_point_position_map.keys():
            return self.time_point_position_map[time_point]
        else:
            return None

    def msd(self, limit=0, diff=distance):
        _track = list(self.time_position_map.values())
        if limit:
            _track = _track[0:limit]
        tau = 1
        while tau < len(_track):
            msd_t = 0
            r = len(_track) - tau
            for i in range(r):
                msd_t += np.square(diff(_track[i + tau], _track[i])).item()
            _mean = msd_t / float(len(_track) - tau)
            yield _mean
            tau += 1
