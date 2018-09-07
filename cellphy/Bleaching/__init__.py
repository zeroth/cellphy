import numpy as np
from cellphy.lib.utils import imread, imsave, file_name_patter_matcher
from timeit import default_timer as timer
from pathlib import Path
import os


def bleach_dir(args):
    start_time = timer()
    print('will bleach from path ', args.path)
    root_dir = Path(args.path)
    tiffs = list(root_dir.glob('*.[tT][iI][fF]'))
    bleached_dir = os.path.abspath(os.path.join(root_dir.resolve(), f'{root_dir.name}_bleachcr'))
    os.makedirs(bleached_dir, exist_ok=True)

    print("tiff_root", root_dir.resolve())
    tiffs.sort(key=file_name_patter_matcher)

    print(tiffs[0])

    total_files = len(tiffs)
    ref_image = imread(os.path.abspath(os.path.join(root_dir.resolve(), tiffs[0])))

    # hist_ref, _ = np.histogram(ref_image.flatten(), bins=256)
    imsave(ref_image, os.path.abspath(os.path.join(bleached_dir, Path(tiffs[0]).name)))

    for i in range(1, total_files):
        current_file = tiffs[i]
        print("processing", current_file)
        target_image = imread(os.path.abspath(os.path.join(root_dir.resolve(), current_file)))
        hist_matched = hist_match(target_image, ref_image)
        imsave(hist_matched.astype(dtype='uint16'), os.path.abspath(os.path.join(bleached_dir, Path(current_file).name)))

    print(f'total time bleach correct {timer()-start_time}')


def hist_map(prob_cum_hist, prob_cum_hist_ref):
    K = 256
    new_values = np.zeros((K), dtype='uint16')
    for a in np.arange(K):
        j = K - 1
        while True:
            new_values[a] = j
            j = j - 1
            if j < 0 or prob_cum_hist[a] > prob_cum_hist_ref[j]:
                break
    return new_values


def hist_match(source, template):
    """
    Adjust the pixel values of a grayscale image such that its histogram
    matches that of a target image

    Arguments:
    -----------
        source: np.ndarray // target
            Image to transform; the histogram is computed over the flattened
            array
        template: np.ndarray // referance
            Template image; can have different dimensions to source
    Returns:
    -----------
        matched: np.ndarray
            The transformed output image
    """

    oldshape = source.shape
    source = source.ravel()
    template = template.ravel()

    # get the set of unique pixel values and their corresponding indices and
    # counts
    s_values, bin_idx, s_counts = np.unique(source, return_inverse=True,
                                            return_counts=True)
    t_values, t_counts = np.unique(template, return_counts=True)

    # take the cumsum of the counts and normalize by the number of pixels to
    # get the empirical cumulative distribution functions for the source and
    # template images (maps pixel value --> quantile)
    s_quantiles = np.cumsum(s_counts).astype(np.float64)
    s_quantiles /= s_quantiles[-1]
    t_quantiles = np.cumsum(t_counts).astype(np.float64)
    t_quantiles /= t_quantiles[-1]

    # interpolate linearly to find the pixel values in the template image
    # that correspond most closely to the quantiles in the source image
    interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)

    return interp_t_values[bin_idx].reshape(oldshape)
