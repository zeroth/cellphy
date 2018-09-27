import numpy as np
from scipy import optimize
import operator
import pandas as pd
import matplotlib.pyplot as plt
from functools import reduce
import itertools
from .TrackPair import TrackPair
from .Track import Track


def distance(a, b):
    return np.sqrt(np.sum((np.array(a) - np.array(b)) ** 2))


def jump_analysis(points):
    results = []
    for i in range(1, len(points)):
        results.append(distance(points[i-1], points[i]))
    return results


def fit_function(_x, d, t):
    return d * np.power(_x, t)


def fit_velocity_function(_x, d, t, v):
    return d * np.power(_x, t) + (np.power(v, 2) * np.power(_x, 2))


def get_msd_fit(_tp_msd, art):

    track_curve_fit = {}
    lgh = []
    f, (pl1, pl2) = plt.subplots(1, 2, sharey=True)
    for track_id, track_msd in _tp_msd.items():
        # print("track_msd", track_msd)
        y = np.array(track_msd)
        y = y[0:26]
        # print(f"len(y) {track_id} ", len(y))
        init = np.array([.001, .01])
        x = np.array(list(range(1, len(y)+1)))*3.8
        best_value, covar = optimize.curve_fit(fit_function, x, y, p0=init, maxfev=10000)
        # plt.subplot(2, 1, 2)
        pl1col = pl1.scatter(x, y, label="Data")
        lg_handler, = pl1.plot(x, fit_function(x, best_value[0], best_value[1]),
                               label=f'{track_id} - ({best_value[1]:.3f})')
        track_curve_fit[track_id] = best_value
        lgh.append(lg_handler)
        art.append(lgh)

        if best_value[1]> 1.4:
            best_value_v, covar_v = optimize.curve_fit(fit_velocity_function, x, y, p0=[.001, .01, .01], maxfev=1000000)
            track_curve_fit[f'{track_id}_velocity'] = best_value_v
            pl2.scatter(x, y, label="Data", edgecolors=pl1col.get_edgecolors(), facecolors=pl1col.get_facecolors())
            lg_handler_v, = pl2.plot(x, fit_velocity_function(x, best_value_v[0], best_value_v[1], best_value_v[2]),
                                   label=f'{track_id} - ({best_value_v[2]:.3f}) _v', color=pl1col.get_edgecolors()[0])
            lgh.append(lg_handler_v)
            art.append(lgh)

        plt.legend(handles=lgh, loc=9, bbox_to_anchor=(0, -0.1), ncol=2)
    return track_curve_fit


def plot_curve(y):
    x = np.array(list(range(1, len(y)+1)))*3.8
    bv, cov = optimize.curve_fit(fit_function, x, y, p0=[0.001,0.01], maxfev=10000)


def get_msd_for_tracks(_tracks):
    track_msd_map = {}
    for _track in _tracks:
        if len(_track.points) > 5:
            track_msd_map[str(_track.track_id)] = list(msd(_track.points, diff=distance))
    return track_msd_map


def msd(_track, diff=operator.sub):
    tau = 1
    while tau < len(_track):
        msd_t = 0
        r = len(_track)-tau
        for i in range(r):
            msd_t += np.square(diff(_track[i+tau], _track[i])).item()
        _mean = msd_t/float(len(_track)-tau)
        yield _mean
        tau += 1


def data_frame_splitter(df, column_name):
    chunks = []
    work = df

    start_point = work[column_name].iloc[0]
    end_point = work[column_name].iloc[work.index.size - 1]
    if (end_point - start_point) + 1 == work.index.size:
        chunks.append(work.copy())
        work = None
    else:
        work = work.drop(work.index[work.index.size - 1])


def compare_tracks(track_a, track_b, suffix_a, suffix_b, _radius):

    result = None

    # pandas apply function
    def apply_sphere(radius, sfl, sfr):
        def check_sphere(x):
            p1 = np.array([x[f'X{sfl}'], x[f'Y{sfl}'], x[f'Z{sfl}']])
            p2 = np.array([x[f'X{sfr}'], x[f'Y{sfr}'], x[f'Z{sfr}']])
            val = p1 - p2
            dot = val.dot(val)
            return (dot <= radius), dot

        return check_sphere

    def apply_direction(sfl, sfr):
        def check_direction(x):
            p1 = np.array([x[f'X{sfl}'], x[f'Y{sfl}'], x[f'Z{sfl}']])
            p2 = np.array([x[f'X{sfr}'], x[f'Y{sfr}'], x[f'Z{sfr}']])
            dot = p1.dot(p2)
            return dot > 0

        return check_direction

    # get the points which are on same time point
    same_time_points = track_a.get_values().merge(track_b.get_values(), on='time')

    if same_time_points.index.size:
        # if they are on same time point
        # check if hey are in same direction
        same_time_points['direction'] = same_time_points\
            .apply(apply_direction(suffix_a, suffix_b), axis=1)

        # get all the points in same direction
        same_time_points = same_time_points[same_time_points['direction'] == True]
        # if there are points in same direction
        if same_time_points.index.size:
            # check if they are in sphere
            same_time_points['near'], same_time_points['distance'] = zip(*same_time_points.apply(
                apply_sphere(_radius, suffix_a, suffix_b), axis=1))

            same_time_points = same_time_points[same_time_points['near'] == True]

            if same_time_points.index.size > 1:
                # print(same_time_points)
                sfl = suffix_a
                sfr = suffix_b
                tl_id = f'trackid{sfl}'
                tr_id = f'trackid{sfr}'
                left_track_id = same_time_points.iloc[0][tl_id]
                right_track_id = same_time_points.iloc[0][tr_id]
                top_pair = f'{left_track_id}{sfl}-{right_track_id}{sfr}'

                same_time_points['top_pair'] = top_pair
                same_time_points['suffix'] = f'{sfl},{sfr}'
                same_time_points[sfl] = left_track_id
                same_time_points[sfr] = right_track_id
                track_a_rd = track_a.get_values().copy()
                track_b_rd = track_b.get_values().copy()

                _time = list(same_time_points['time'])
                _track_a = Track(track_a.track_id, track_a.name, track_a.color, track_a.suffix,
                                     raw_data=track_a_rd[track_a_rd['time'].isin(_time)])
                _track_b = Track(track_b.track_id, track_b.name, track_b.color, track_b.suffix,
                                     raw_data=track_b_rd[track_b_rd['time'].isin(_time)])

                result = TrackPair(_track_a, _track_b, _time)
                # result = result.append(same_time_points)

                # further splitting of track if we want to see which time points are not together
                # splited_same_points = split_df(same_time_points)
                #
                # # print(f'after split {len(splited_same_points)}')
                # for index, pair in enumerate(splited_same_points):
                #     _pair = pair.copy()
                #     _pair['sub_pair'] = f'{top_pair}({index})'
                #
                #     result = result.append(_pair)
    return result


def compare_all_tracks(tracks, suffixes, radius):
    # do the pairing
    pairs = {}
    for track_a, track_b in itertools.combinations(tracks, 2):
        # get the points which are on same time point
        pair = compare_tracks(track_a, track_b, track_a.suffix, track_b.suffix, radius)
        if not pair.empty:
            pairs[f'{track_a.suffix}-{track_b.suffix}'] = pair

    # for p in list(pairs.values()):
    #     print(p)
    # union of the pairs
    pair_union = None

    if len(pairs) > 1:
        pair_union = reduce(lambda left, right: pd.merge(left, right, on='time'), list(pairs.values()))
        identity = []
        for t in tracks:
            identity.append(f'{t.track_id}_{t.suffix}')
        pair_union['identity'] = ','.join(identity)

    return pairs, pair_union

def split_df(_a):
    result = []
    df = _a
    a = list(_a['time'])
    r = splitter(a)
    rd = df.loc[df['time'].isin(r)]
    result.append(rd.copy())
    # print(f'{len(r)} is not {len(a)}')

    while len(r) is not len(a):
        a = [i for i in a if i not in r]
        r = splitter(a)
        _rd = df.loc[df['time'].isin(r)]
        result.append(_rd.copy())

    return result


def splitter(a):
    # print(f'input \n {a}')
    start = a[0]
    end = a[-1]
    # print(f'start {start} - end {end} len of a {len(a)} calc {((end - start) + 1)}')
    if ((end - start) + 1) == len(a):
        return a
    else:
        j = a[:len(a) - 1]
        return splitter(j)


#### old backup
"""
def extract_track_from_df(df, suffix, track_id):
    tracks = df[df['trackid' + suffix] == track_id]
    tracks_col = [col for col in tracks.columns if col.endswith(suffix)]
    tracks_col.append('time')
    tracks = tracks[tracks_col]
    tracks_col = [col.strip(suffix) for col in tracks_col]
    tracks.columns = tracks_col
    _track = Track(track_id=track_id, raw_data=tracks)
    return _track
    
def _compare_tracks(channel_a, channel_b, _radius):
    _close_channels = []
    result = pd.DataFrame()

    # pandas apply function
    def apply_sphere(radius, sfl, sfr):
        def check_sphere(x):
            p1 = np.array([x[f'X{sfl}'], x[f'Y{sfl}'], x[f'Z{sfl}']])
            p2 = np.array([x[f'X{sfr}'], x[f'Y{sfr}'], x[f'Z{sfr}']])
            val = p1 - p2
            dot = val.dot(val)
            return (dot <= radius), dot

        return check_sphere

    def apply_direction(sfl, sfr):
        def check_direction(x):
            p1 = np.array([x[f'X{sfl}'], x[f'Y{sfl}'], x[f'Z{sfl}']])
            p2 = np.array([x[f'X{sfr}'], x[f'Y{sfr}'], x[f'Z{sfr}']])
            dot = p1.dot(p2)
            return dot > 0

        return check_direction

    for track_a in channel_a.get_tracks():
        for track_b in channel_b.get_tracks():
            # get the points which are on same time point
            same_time_points = track_a.get_values().merge(track_b.get_values(), on='time',
                                                          suffixes=[channel_a.get_suffix(), channel_b.get_suffix()])

            if same_time_points.index.size:
                # if they are on same time point
                # check if hey are in same direction
                same_time_points['direction'] = same_time_points\
                    .apply(apply_direction(channel_a.get_suffix(), channel_b.get_suffix()), axis=1)

                # get all the points in same direction
                same_time_points = same_time_points[same_time_points['direction'] == True]
                # if there are points in same direction
                if same_time_points.index.size:
                    # check if they are in sphere
                    same_time_points['near'], same_time_points['distance'] = zip(*same_time_points.apply(
                        apply_sphere(_radius, channel_a.get_suffix(), channel_b.get_suffix()), axis=1))

                    same_time_points = same_time_points[same_time_points['near'] == True]

                    if same_time_points.index.size:
                        # print(same_time_points)
                        sfl = channel_a.get_suffix()
                        sfr = channel_b.get_suffix()
                        tl_id = f'trackid{sfl}'
                        tr_id = f'trackid{sfr}'
                        left_track_id = same_time_points.iloc[0][tl_id]
                        right_track_id = same_time_points.iloc[0][tr_id]
                        top_pair = f'{left_track_id}{sfl}-{right_track_id}{sfr}'

                        same_time_points['top_pair'] = top_pair
                        same_time_points['suffix'] = f'{sfl},{sfr}'
                        same_time_points[sfl] = left_track_id
                        same_time_points[sfr] = right_track_id

                        result = result.append(same_time_points)

                        # further splitting of track if we want to see which time points are not together
                        # splited_same_points = split_df(same_time_points)
                        #
                        # # print(f'after split {len(splited_same_points)}')
                        # for index, pair in enumerate(splited_same_points):
                        #     _pair = pair.copy()
                        #     _pair['sub_pair'] = f'{top_pair}({index})'
                        #
                        #     result = result.append(_pair)
    return result
"""
