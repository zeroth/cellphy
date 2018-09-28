import argparse
import os
import sys
from cellphy.lib import libinstall
from cellphy.Bleaching import bleach_dir
from cellphy.Analysis.Tools import calculate_msd, calculate_msb_by_bin, track_analyze, analyze_mean_stddev
from cellphy.tracking_analyzer_gui import start_ui

is_linux = False
if sys.platform.startswith('linux'):
    is_linux = True

if is_linux:
    from cellphy.preprocessing import deskew_dir
    from cellphy.preprocessing import decon_dir


def process_args():
    arguments = argparse.ArgumentParser(description="analysis, bleach, deskew, decon or install")

    commands = arguments.add_subparsers(dest='func')

    a_arguments = commands.add_parser('analysis')
    b_arguments = commands.add_parser('bleach')

    m_arguments = commands.add_parser('msd')
    bm_arguments = commands.add_parser('binmsd')
    t_arguments = commands.add_parser('track')
    ui_arguments = commands.add_parser('gui')

    # bleach
    b_arguments.add_argument('path', default='.')
    b_arguments.set_defaults(func=bleach_dir)

    # Analysis
    a_arguments.add_argument('path', default='.')
    a_arguments.set_defaults(func=analyze_mean_stddev)

    # msd
    m_arguments.add_argument('path', default='.')
    m_arguments.set_defaults(func=calculate_msd)

    # msd_bin
    bm_arguments.add_argument('path', default='.')
    bm_arguments.add_argument('--fit', action='store_true')
    bm_arguments.set_defaults(func=calculate_msb_by_bin)

    # track
    t_arguments.add_argument('path', nargs='+')
    t_arguments.add_argument('--radius', type=float, default=1)
    t_arguments.set_defaults(func=track_analyze)

    # start gui
    ui_arguments.set_defaults(func=start_ui)

    if is_linux:
        # specific to linux
        d_arguments = commands.add_parser('deskew')
        i_arguments = commands.add_parser('install')
        dc_arguments = commands.add_parser('decon')

        # install
        i_arguments.add_argument('path', default='.')
        i_arguments.set_defaults(func=install)

        # decon
        dc_arguments.add_argument('path', default='.')
        dc_arguments.add_argument('--channel', type=int, required=True)
        dc_arguments.set_defaults(func=decon_dir)

        # deskew
        d_arguments.add_argument('path', default='.')
        d_arguments.add_argument('--angle', default=31.5, type=float)
        d_arguments.add_argument('--dz', default=0.4, type=float)
        d_arguments.add_argument('--pixelsize', default=0.104, type=float)
        d_arguments.set_defaults(func=deskew_dir)


    args = arguments.parse_args()

    args.func(args)


def install(args):
    """Install cudaDeconv libraries and binaries to LLSPY.

    Provided PATH argument can be a LIB or BIN directory, or a parent
    directory that contains both the LIB and BIN directories.  The appropriate
    library and binary files will be installed to the LLSpy installation.

    """
    if os.environ.get('CONDA_DEFAULT_ENV', '') in ('root', 'base'):
        print('It looks like you\'re in the root conda environment... '
              'It is recommended that you install cellphy in its own environment.\n Continue?')
        return
    libinstall.install(args.path)


if __name__ == '__main__':
    process_args()
