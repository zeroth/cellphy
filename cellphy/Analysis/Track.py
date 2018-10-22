from collections import OrderedDict
import numpy as np
from scipy.optimize import curve_fit
import itertools


def fit_function(delta, d, alfa):
    return (4*d) * np.power(delta, alfa)


def fit_velocity_function(delta, d, alfa, v):
    return (4*d) * np.power(delta, alfa) + (np.power(v, 2) * np.power(delta, 2))


def distance(a, b):
    return np.sqrt(np.sum((np.array(a) - np.array(b)) ** 2))


class Track:
    def __init__(self, track_id, name, color, suffix, raw_data=None, parent=None):
        self.parent = parent
        self.track_id = track_id
        self.raw_data = raw_data.copy().reset_index(drop=True)
        self.suffix = suffix
        self.color = color

        self.name = f'{name}-{self.track_id}'
        self.time_position_map = {}
        self.limit = 26
        _time_position_map = {}
        for index, row in self.raw_data.iterrows():
            _time_position_map[int(row[['time']])] = list(row[[f'X{self.suffix}', f'Y{self.suffix}', f'Z{self.suffix}']])
        self.time_position_map = OrderedDict(sorted(_time_position_map.items(), key=lambda t: t[0]))

        self.max_time_point = self.raw_data['time'].max()

    def __str__(self):
        return f'{self.track_id}-{self.suffix}'

    def get_track_id(self):
        return self.track_id

    def get_values(self):
        return self.raw_data

    def get_position_by_time_point(self, time_point):
        if time_point in self.time_position_map.keys():
            return self.time_position_map[time_point]
        else:
            return None

    def msd(self, limit=26, diff=distance):
        # 26 ~= 100 sec (3.8)
        self.limit = limit
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

    def ied_distance(self):
        for p1, p2 in itertools.combinations(list(self.time_position_map.values()), 2):
            yield distance(p1, p2)

    def basic_fit(self):

        y = np.array(list(self.msd(limit=self.limit)))
        x = np.array(list(range(1, len(y) + 1))) * 3.8

        init = np.array([.001, .01])
        best_value, _ = curve_fit(fit_function, x, y, p0=init, maxfev=10000)
        _y = fit_function(x, best_value[0], best_value[1])

        return best_value[1], _y

    def velocity_fit(self):
        y = np.array(list(self.msd(limit=self.limit)))
        x = np.array(list(range(1, len(y) + 1))) * 3.8

        init = np.array([.001, .01, .01])
        best_value, _ = curve_fit(fit_velocity_function, x, y, p0=init, maxfev=1000000)
        _y = fit_velocity_function(x, best_value[0], best_value[1], best_value[2])

        return best_value[1], best_value[2], _y