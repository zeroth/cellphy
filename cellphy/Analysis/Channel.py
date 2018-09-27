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
        self.tracks_hash_map = {}
        self.suffix = suffix
        self.header = header

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

        self.max_time_point = self.raw_data['time'].max()

        for _id in self.track_ids:
            t = Track(track_id=_id, name=self.name, color=self.base_color, suffix=self.suffix,
                      raw_data=self.raw_data[self.raw_data[f'trackid{self.suffix}'] == _id], parent=self)

            self.tracks.append(t)
            self.tracks_hash_map[_id] = t

    def get_time_point_position_map(self):
        # filter tracks
        _tracks = [tr for tr in self.tracks if len(tr.get_vtk_track()) > 1]
        time_point_position_map = {}
        for i in range(self.max_time_point+1):
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
                time_pos_distance_mean_map[time] = [statistics.mean(pos), statistics.stdev(pos)]
            time_pos_distance_mean_map[time] = [pos[0], pos[0]]

        return time_pos_distance_mean_map

    def bin_tracks(self, binsize=10):
        tracks_bin = {}
        # it_track = copy.deepcopy(self.tracks)
        m_track = self.tracks
        for sb in range(0, self.max_time_point, binsize):
            it_track = m_track
            # print(f'len(it_track){len(it_track)}')
            for t in it_track:
                tk = np.array(list(t.time_point_position_map.keys()))
                if np.any((sb >= tk) * (sb <= (sb+binsize))):
                    if not tracks_bin.get(sb, False):
                        tracks_bin[sb] = []
                    tracks_bin[sb].append(t)
                    m_track.remove(t)

        return tracks_bin

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