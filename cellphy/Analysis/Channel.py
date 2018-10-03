from cellphy.Analysis import Track
import pandas as pd
from pathlib import PurePath
from functools import reduce
import numpy as np
import itertools
import statistics
from cellphy.Analysis.functions import distance


class Channel:

    def __init__(self, file_path=None, channel_name='Untitled', header=1,
                 data=None, color=[255, 255, 255], suffix='_C0'):

        self.name = channel_name
        self.data_file = file_path
        self.raw_data = data
        self.tracks = []
        self.tracks_backup = []
        self.tracks_hash_map = {}
        self.suffix = suffix
        self.header = header
        self.filter_size = 4
        self.bin_value = 0
        self.base_color = color
        self.max_time_point = 0
        self.time_point_position_map = {}
        self.track_ids = None
        if self.data_file is not None:
            self.load_data(self.data_file)

    def load_data(self, data_file):
        names = [f'X{self.suffix}', f'Y{self.suffix}', f'Z{self.suffix}', 'unit', 'category', 'collection', 'time',
                 f'trackid{self.suffix}', 'id']
        self.name = PurePath(data_file).name
        self.raw_data = pd.read_csv(data_file, names=names, header=self.header)
        self.raw_data.pop('unit')
        self.raw_data.pop('category')
        self.raw_data.pop('collection')
        self.raw_data.pop('id')

        self.track_ids = self.raw_data[f'trackid{self.suffix}'].unique()

        for _id in self.track_ids:
            if len(list(self.raw_data[self.raw_data[f'trackid{self.suffix}'] == _id]['time'])) >= 4:
                t = Track(track_id=_id, name=self.name, color=self.base_color, suffix=self.suffix,
                          raw_data=self.raw_data[self.raw_data[f'trackid{self.suffix}'] == _id], parent=self)

                self.tracks_backup.append(t)
        self.apply_filter(self.filter_size)
        self.max_time_point = self._get_max_time_point()

    def apply_filter(self, filter_value=4):
        self.filter_size = filter_value
        self.tracks = []
        self.tracks_hash_map = {}
        for t in self.tracks_backup:
            if len(t.time_position_map) >= filter_value:
                self.tracks.append(t)
                self.tracks_hash_map[t.track_id] = t

    def _get_max_time_point(self):
        times = []
        for t in self.tracks:
            times.append(t.max_time_point)
        return max(times)

    # def add_track(self, _track):
    #     self.tracks_backup.append(_track)

    def set_track(self, _tracks):
        self.tracks_backup = _tracks
        self.apply_filter(self.filter_size)

    def get_time_point_position_map(self):
        # filter tracks
        _tracks = [tr for tr in self.tracks if len(tr.time_position_map) > 1]
        time_point_position_map = {}
        for i in range(self._get_max_time_point()+1):
            for t in _tracks:
                pos = t.get_position_by_time_point(i)
                if pos:
                    if not time_point_position_map.get(i, 0):
                        time_point_position_map[i] = []
                    time_point_position_map[i].append(pos)
        return time_point_position_map

    def get_distance_between_pos_by_time(self):
        time_pos_map = self.get_time_point_position_map()
        time_pos_distance_map = {}
        for time, pos in time_pos_map.items():
            for p1, p2 in itertools.combinations(pos, 2):
                if not time_pos_distance_map.get(time, 0):
                    time_pos_distance_map[time] = []
                time_pos_distance_map[time].append(distance(np.array(p1), np.array(p2)))
        return time_pos_distance_map

    def get_time_point_mean_and_stdev(self):
        time_point_distance = self.get_distance_between_pos_by_time()
        time_pos_distance_mean_map = {}
        for time, pos in time_point_distance.items():
            if len(pos) > 1:
                time_pos_distance_mean_map[time] = [time, statistics.mean(pos), statistics.stdev(pos)]
            time_pos_distance_mean_map[time] = [time, pos[0], pos[0]]

        return time_pos_distance_mean_map

    def bin_tracks(self, bin_value=0, radius=0):
        # tracks_bin = {}
        total_dict = {}
        _channels = []
        self.bin_value = bin_value
        # it_track = copy.deepcopy(self.tracks)
        m_track = self.tracks.copy()
        if bin_value:
            for sb in range(0, self._get_max_time_point(), bin_value):
                it_track = m_track.copy()
                # print(f'len(it_track){len(it_track)}')
                tb = []
                for t in it_track:
                    tk = np.array(list(t.time_position_map.keys()))
                    if np.any((sb >= tk) * (sb <= (sb + bin_value))):
                        # if not tracks_bin.get(sb, False):
                        #     tracks_bin[sb] = []
                        # tracks_bin[sb].append(t)
                        tb.append(t)
                        m_track.remove(t)
                if len(tb) > 0:
                    _channel = Channel(channel_name=f'{sb-bin_value}-{sb}_{radius:.1f}',
                                       suffix=self.suffix, color=self.base_color.copy())
                    _channel.set_track(tb)
                    _channels.append(_channel)
                    if not total_dict.get(f'{sb-bin_value}-{sb}', False):
                        total_dict[f'{sb-bin_value}-{sb}'] = {'total': 0, 'lt': 0, 'gt': 0}

                    current = total_dict[f'{sb-bin_value}-{sb}']
                    current['total'] = len(tb)
                    for t in tb:
                        alfa, _ = t.basic_fit()
                        if alfa > 1.4:
                            current['gt'] += 1
                        else:
                            current['lt'] += 1
        else:
            _channels.append(self)
            total_dict[f'all'] = {'total': 0, 'lt': 0, 'gt': 0}
            current = total_dict[f'all']
            current['total'] = len(self.tracks)
            for t in self.tracks:
                alfa, _ = t.basic_fit()
                if alfa > 1.4:
                    current['gt'] += 1
                else:
                    current['lt'] += 1

        return _channels, total_dict

    def size(self):
        return len(self.tracks)

    def get_track(self, track_id):
        return self.tracks_hash_map.get(track_id, None)

    def add_track(self, _track):
        self.tracks.append(_track)


if __name__ == '__main__':
    channel = Channel('../data/16_Position.csv')
    channel_tracks = channel.get_tracks()
    for track_index, track in enumerate(channel_tracks):
        for pindex, p in enumerate(track.get_vtk_track()):
            print(pindex, p)