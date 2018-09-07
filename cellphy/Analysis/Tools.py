from cellphy.Analysis.Channel import Channel
from cellphy.Analysis.Track import Track
import numpy as np
import itertools
import time
import sys
from scipy import optimize
from timeit import default_timer as timer
from pathlib import Path
import os
import pandas as pd
import matplotlib.pyplot as plt
from .functions import compare_tracks, get_msd_for_tracks, get_msd_fit


def track_analyze(args):
    start_time = timer()
    if len(args.path) < 2:
        print('at least 2 track files should be provided')
        sys.exit(1)

    # print('suffix', data_file.suffix)
    for c_file in args.path:
        data_file = Path(c_file)
        if not (data_file.suffix == '.csv'):
            print('please provide a path for .csv file')
            sys.exit(1)

    # create channels
    channels = []
    for csv_file in args.path:
        channels.append(Channel(csv_file))

    an_df = compare_tracks(channels, args.radius, 0)
    processed_file = os.path.abspath(os.path.join(data_file.parent.resolve(), f'processed_{data_file.name}'))


def analyze_mean_stddev(args):
    start_time = timer()
    data_file = Path(args.path)
    print('suffix', data_file.suffix)
    if not (data_file.suffix == '.csv'):
        print('please provide a path for .csv file')
        sys.exit(1)

    processed_file = os.path.abspath(os.path.join(data_file.parent.resolve(), f'processed_{data_file.name}'))
    print("processing", data_file)

    channel = Channel(data_file)
    time_map = channel.get_time_point_mean_and_stdev()

    df = pd.DataFrame.from_dict(time_map, orient='index')
    df.set_axis(['mean', 'stddev'], axis=1, inplace=True)
    df.to_csv(processed_file)

    print(f'total time to analyze {timer()-start_time}')


def calculate_msd(args):
    start_time = timer()
    data_file = Path(args.path)
    print('suffix', data_file.suffix)
    if not (data_file.suffix == '.csv'):
        print('please provide a path for .csv file')
        sys.exit(1)

    processed_file = os.path.abspath(os.path.join(data_file.parent.resolve(), f'processed_msd_{data_file.name}'))
    print("processing", data_file)
    print("output file", processed_file)

    channel = Channel(data_file)
    csv_str = 'trackid, tau, msd\n'

    # track_msd_map = {}
    # for _track in channel.tracks:
    #     if len(_track.points) > 5:
    #         track_msd_map[str(_track.track_id)] = list(msd(_track.points, diff=distance))
    #         # for tau, tmsd in list(msd(_track.points, diff=distance)):
    #         #     csv_str += f'{_track.track_id}, {tau}, {tmsd}\n'

    # with open(processed_file, mode='w') as f:
    #     f.write(csv_str)
    # create csv
    track_msd_map = get_msd_for_tracks(channel.tracks)
    df = pd.DataFrame.from_dict(track_msd_map, orient='index')
    df = df.transpose()
    df.to_csv(processed_file)


def calculate_msb_by_bin(args):
    path = args
    start_time = timer()

    if type(args) is not 'str':
        path = args.path

    data_file = Path(path)
    print('suffix', data_file.suffix)
    if not (data_file.suffix == '.csv'):
        print('please provide a path for .csv file')
        sys.exit(1)

    print("processing", data_file)
    process_dir = os.path.join(data_file.parent.resolve(), os.path.splitext(data_file.name)[0])
    msd_dir = os.path.join(process_dir, 'msd')
    curve_fit_dir = os.path.join(process_dir, 'curve_fit')
    os.makedirs(msd_dir, exist_ok=True)
    os.makedirs(curve_fit_dir, exist_ok=True)
    channel = Channel(data_file)
    print('binning and msd')
    track_bins = channel.bin_tracks()
    curve_data = {}

    for bn, tb in track_bins.items():
        tb_msd = get_msd_for_tracks(tb)
        processed_file_msd = os.path.abspath(os.path.join(msd_dir, f'processed_msd_{bn}_{data_file.name}'))
        print("msd output file", processed_file_msd)
        df1 = pd.DataFrame.from_dict(tb_msd, orient='index')
        df1 = df1.transpose()
        df1.to_csv(processed_file_msd)
        art = []
        curve_data = {**curve_data, **get_msd_fit(tb_msd, art)}
        # plt.title(f'Curve fitted for bin {bn}')

        plt.savefig(os.path.join(curve_fit_dir, f'{bn}_{data_file.name.split(".")[0]}.svg'), format="svg",
                    bbox_inches="tight", additional_artists=art)
        plt.cla()
        plt.clf()

    processed_file_curve = os.path.abspath(os.path.join(process_dir, f'processed_curve_{data_file.name}'))
    print("curve output file", processed_file_curve)
    df2 = pd.DataFrame.from_dict(curve_data, orient='index')
    # df2 = df2.transpose()
    df2.to_csv(processed_file_curve)

    print(f'total time to binmsb  {timer()-start_time}')
