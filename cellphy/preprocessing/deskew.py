from cellphy.lib.libcudawrapper import deskewGPU
import cupy as cp
import numpy as np
import sys
from cellphy.lib.utils import imread, imsave
import os
from pathlib import Path
from timeit import default_timer as timer


def deskew_dir(args):
    from cellphy.preprocessing import deskew
    m_time = timer()
    print('will deskew from path ', args.path)
    root_dir = Path(args.path)
    tiffs = root_dir.glob('*.[tT][iI][fF]')
    deskewed_dir = os.path.abspath(os.path.join(root_dir.resolve(), f'{root_dir.name}_deskewed'))
    os.makedirs(deskewed_dir, exist_ok=True)
    for f in tiffs:
        im = imread(os.path.abspath(os.path.join(root_dir.resolve(), f)))
        file_name = Path(f).name
        print('deskewing...', file_name)
        # deskewGPU(s, P.dzdata, P.drdata, P.deskew)
        imsave(deskew(im, 0.4, 0.104, 31.5), os.path.abspath(os.path.join(deskewed_dir, file_name)))
    print(f'total time to deskew {timer()-m_time}')


def deskew(image, angle, dz, pixel_size):
    deskewed = deskewGPU(image, angle, dz, pixel_size)

    image_cp = cp.array(image)
    deskewed_cp = cp.array(deskewed)

    pages, col, row = image_cp.shape
    noise_size = cp.ceil(cp.max(cp.array([row, col])) * 0.1)
    image_noise_patch = image_cp[0:noise_size, col - (noise_size + 1):col - 1, :]
    image_noise_patch = image_noise_patch.flatten()

    fill_length = deskewed_cp.size - cp.count_nonzero(deskewed_cp)
    repeat_frequency = cp.ceil(fill_length/image_noise_patch.size)
    repeat_frequency = cp.asnumpy(repeat_frequency).flatten().astype(dtype=np.uint16)[0]
    noise = cp.tile(image_noise_patch, repeat_frequency+1)
    noise = noise[0:fill_length]
    deskewed_cp[deskewed_cp == 0] = noise

    return cp.asnumpy(deskewed_cp)


