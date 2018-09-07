import os
import sys
import fnmatch
import warnings
import tifffile
import numpy as np
import json
import ctypes
import cupy
import re

PLAT = sys.platform
if PLAT == 'linux2':
    PLAT = 'linux'
elif PLAT == 'cygwin':
    PLAT = 'win32'


def file_name_patter_matcher(x):
    r = r'_T[\d\.-]+.'
    rs = re.search(r, x.name)
    if rs:
        span = rs.span()
        return x.name[span[0]+2:span[1]-1]
    return '0'


def get_cdf(h):
    '''
    // returns the cumul. probability distribution function (cdf) for histogram h
		int K = h.length;
		int n = 0;		// sum all histogram values
		for (int i=0; i<K; i++)	{
			n += h[i];
		}
		double[] P = new double[K];
		int c = h[0];
		P[0] = (double) c / n;
	    for (int i=1; i<K; i++) {
		c += h[i];
	        P[i] = (double) c / n;
	    }
	    return P;
    '''
    K = h.size
    n = h.sum()
    P = np.zeros(h.shape)
    c = h[0]
    P[0] = np.double(c / n)
    for i in range(1, K):
        c += h[i]
        P[i] = np.double(c / n)
    return P


# In[207]:


def hist_matching(target_hist, referance_hist):
    '''
    public int[] matchHistograms (int[] hA, int[] hR) {
		int K = hA.length;
		double[] PA = Util.Cdf(hA); // get CDF of histogram hA
		double[] PR = Util.Cdf(hR); // get CDF of histogram hR
		int[] F = new int[K]; // pixel mapping function f()

		// compute pixel mapping function f():
		for (int a = 0; a < K; a++) {
			int j = K - 1;
			do {
				F[a] = j;
				j--;
			} while (j >= 0 && PA[a] <= PR[j]);
		}
		return F;
}
    '''
    PA = get_cdf(np.copy(target_hist))
    PR = get_cdf(np.copy(referance_hist))
    K = target_hist.size
    F = np.zeros(K)
    # print("F is")
    # print(F)
    for a in range(K):
        j = K - 1
        while True:
            F[a] = j
            j -= 1
            if not (j >= 0 and PA[a] <= PR[j]):
                break
    return F


def histogram(x, bins=10):
    # copied from cupy github https://github.com/cupy/cupy/blob/master/cupy/statistics/histogram.py
    """Computes the histogram of a set of data.
    Args:
        x (cupy.ndarray): Input array.
        bins (int or cupy.ndarray): If ``bins`` is an int, it represents the
            number of bins. If ``bins`` is an :class:`~cupy.ndarray`, it
            represents a bin edges.
    Returns:
        tuple: ``(hist, bin_edges)`` where ``hist`` is a :class:`cupy.ndarray`
        storing the values of the histogram, and ``bin_edges`` is a
        :class:`cupy.ndarray` storing the bin edges.
    .. seealso:: :func:`numpy.histogram`
    """

    if x.dtype.kind == 'c':
        # TODO(unno): comparison between complex numbers is not implemented
        raise NotImplementedError('complex number is not supported')

    if isinstance(bins, int):
        if x.size == 0:
            min_value = 0.0
            max_value = 1.0
        else:
            min_value = float(x.min())
            max_value = float(x.max())
        if min_value == max_value:
            min_value -= 0.5
            max_value += 0.5
        bins = cupy.linspace(min_value, max_value, bins + 1)
    elif isinstance(bins, cupy.ndarray):
        if cupy.any(bins[:-1] > bins[1:]):
            raise ValueError('bins must increase monotonically.')
    else:
        raise NotImplementedError('Only int or ndarray are supported for bins')

    # atomicAdd only supports int32
    y = cupy.zeros(bins.size - 1, dtype=cupy.int32)

    # TODO(unno): use searchsorted
    cupy.ElementwiseKernel(
        'S x, raw T bins, int32 n_bins',
        'raw int32 y',
        '''
        if (x < bins[0] or bins[n_bins - 1] < x) {
            return;
        }
        int high = n_bins - 1;
        int low = 0;
        while (high - low > 1) {
            int mid = (high + low) / 2;
            if (bins[mid] <= x) {
                low = mid;
            } else {
                high = mid;
            }
        }
        atomicAdd(&y[low], 1);
        '''
    )(x, bins, bins.size, y)
    return y.astype('l'), bins

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __dir__(self):
        return self.keys()


def imread(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return tifffile.imread(*args, **kwargs)


def imshow(*args, **kwargs):
    return tifffile.imshow(*args, **kwargs)


def imsave(arr, outpath, dx=1, dz=1, dt=1, unit='micron'):
    """sample wrapper for tifffile.imsave imagej=True."""
    # array must be in TZCYX order
    md = {
        'unit': unit,
        'spacing': dz,
        'finterval': dt,
        'hyperstack': 'true',
        'mode': 'composite',
        'loop': 'true',
    }
    bigT = True if arr.nbytes > 3758096384 else False  # > 3.5GB make a bigTiff
    if arr.ndim == 3:
        arr = reorderstack(arr)  # assume that 3 dimension array is ZYX
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tifffile.imsave(outpath, arr, bigtiff=bigT, imagej=True,
                        resolution=(1 / dx, 1 / dx), metadata=md)


def getfoldersize(folder, recurse=False):
    if recurse:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                total_size += os.path.getsize(os.path.join(dirpath, f))
        return total_size
    else:
        return sum(os.path.getsize(os.path.join(folder, f))
                for f in os.listdir(folder))


def format_size(size):
    """Return file size as string from byte size."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB'):
        if size < 1024:
            return "%.f %s" % (size, unit)
        size /= 1024.0


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def which(program):
    """Check if program is exectuable.  Return path to bin if so"""
    if program is None:
        return None

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        try:
            base = sys._MEIPASS
            if is_exe(os.path.join(base, program)):
                return os.path.join(base, program)
            elif is_exe(os.path.join(base, 'bin', program)):
                return os.path.join(base, 'bin', program)
        except AttributeError:
            pass

        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

        # binpaths = ['bin', 'Library/bin', '../../llspylibs/{}/bin'.format(PLAT)]
        binpaths = ('bin', 'Library/bin')
        for path in binpaths:
            path = getAbsoluteResourcePath(path)
            if path:
                path = os.path.abspath(path)
                if os.path.isdir(path):
                    exe_file = os.path.join(path, program)
                    if is_exe(exe_file):
                        return exe_file

    if sys.platform.startswith('win32') and not program.endswith('.exe'):
        return which(program + ".exe")
    return None


def isexecutable(fpath):
    if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
        return 1
    else:
        return 0



def reorderstack(arr, inorder='zyx', outorder='tzcyx'):
    """rearrange order of array, used when resaving a file."""
    inorder = inorder.lower()
    assert arr.ndim == len(inorder), 'The array dimensions must match the inorder dimensions'
    for _ in range(len(outorder) - arr.ndim):
        arr = np.expand_dims(arr, 0)
    for i in outorder:
        if i not in inorder:
            inorder = i + inorder
    arr = np.transpose(arr, [inorder.find(n) for n in outorder])
    return arr


def getAbsoluteResourcePath(relativePath):
    """ Load relative path, in an environment agnostic way"""

    try:
        # PyInstaller stores data files in a tmp folder refered to as _MEIPASS
        basePath = sys._MEIPASS
        # print('1 base path', basePath)
    except Exception:
        # If not running as a PyInstaller created binary, try to find the data file as
        # an installed Python egg
        try:
            basePath = os.path.dirname(sys.modules['llspy'].__file__)
            # print('2 base path', basePath)
            # print('2 debug', sys.modules['llspy'].__file__)
        except Exception:
            basePath = ''

        # If the egg path does not exist, assume we're running as non-packaged
        if not os.path.exists(os.path.join(basePath, relativePath)):
            basePath = 'llspy'

    path = os.path.join(basePath, relativePath)
    # print("basePath", basePath, "relativePath", relativePath, 'path', path)
    # If the path still doesn't exist, this function won't help you
    if not os.path.exists(path):
        return None

    return path


def load_lib(libname):
    """load shared library, searching a number of likely paths
    """
    # first just try to find it on the search path

    searchlist = [os.path.join(os.environ.get('CONDA_PREFIX', '.'), 'Library', 'bin'),
                  os.path.join(os.environ.get('CONDA_PREFIX', '.'), 'lib'),
                  './lib',
                  # '../../llspylibs/{}/lib/'.format(PLAT),
                  # '../llspylibs/{}/lib/'.format(PLAT),
                  '.']

    # print(searchlist)

    ext = {'linux': '.so',
           'win32': '.dll',
           'darwin': '.dylib'}

    if not libname.endswith(('.so', '.dll', '.dylib')):
        libname += ext[PLAT]

    # print("libname - ", libname)
    for f in searchlist:
        try:
            d = getAbsoluteResourcePath(f)
            # print('d - ', d)
            # print('details ', os.path.abspath(os.path.join(d, libname)))
            return ctypes.CDLL(os.path.abspath(os.path.join(d, libname)))
        except Exception:
            continue

    #last resort, chdir into each dir
    curdir = os.path.abspath(os.curdir)
    for f in searchlist:
        try:
            d = os.path.abspath(getAbsoluteResourcePath(f))
            if os.path.isdir(d):
                os.chdir(d)
                lib = ctypes.CDLL(libname)
                os.chdir(curdir)
                return lib
            raise Exception('didn\'t find it')
        except Exception:
            continue


def array_to_tif(
        x,
        filename,
        slices=None,
        channels=None,
        frames=None,
        verbose=False,
        coerce_64bit_to_32bit=True,
        backup_filename=None,
):
    """Save a numpy array as a TIF
    We'll structure our TIF the same way ImageJ does:
    *8-bit header
    *First image file directory (IFD, description of one 2D slice)
    *Image description
    *All image data
    *Remaining IFDs

    First, ensure a three dimensional input:
    """
    if len(x.shape) == 1:
        x = x.reshape((1, 1,) + x.shape)
    if len(x.shape) == 2:
        x = x.reshape((1,) + x.shape)
    assert len(x.shape) == 3
    """
    All our IFDs are very similar; reuse what we can:
    """
    ifd = Simple_IFD()
    ifd.width[0] = x.shape[2]
    ifd.length[0] = x.shape[1]
    ifd.rows_per_strip[0] = x.shape[1]
    if coerce_64bit_to_32bit and x.dtype in (np.float64, np.int64, np.uint64):
        if x.dtype == np.float64:
            dtype = np.dtype('float32')
        elif x.dtype == np.int64:
            dtype = np.dtype('int32')
        elif x.dtype == np.uint64:
            dtype = np.dtype('uint32')
    elif x.dtype == np.bool:  # Coorce boolean arrays to uint8
        dtype = np.dtype('uint8')
    else:
        dtype = x.dtype
    ifd.set_dtype(dtype)
    ifd.strip_byte_counts[0] = (x.shape[1] *
                                x.shape[2] *
                                ifd.bits_per_sample[0] // 8)

    if slices is not None and channels is not None and frames is not None:
        assert slices * channels * frames == x.shape[0]
        image_description = bytes(''.join((
            'ImageJ=1.48e\nimages=%i\nchannels=%i\n' % (x.shape[0], channels),
            'slices=%i\nframes=%i\nhyperstack=true\n' % (slices, frames),
            'mode=grayscale\nloop=false\nmin=%0.3f\nmax=%0.3f\n\x00' % (
                x.min(), x.max()))), encoding='ascii')
    elif slices is not None and channels is not None and frames is None:
        assert slices * channels == x.shape[0]
        image_description = bytes(''.join((
            'ImageJ=1.48e\nimages=%i\nchannels=%i\n' % (x.shape[0], channels),
            'slices=%i\nhyperstack=true\nmode=grayscale\n' % (slices),
            'loop=false\nmin=%0.3f\nmax=%0.3f\n\x00' % (x.min(), x.max()))),
            encoding='ascii')
    else:
        image_description = bytes(''.join((
            'ImageJ=1.48e\nimages=%i\nslices=%i\n' % (x.shape[0], x.shape[0]),
            'loop=false\nmin=%0.3f\nmax=%0.3f\n\x00' % (x.min(), x.max()))),
            encoding='ascii')
    ifd.num_chars_in_image_description[0] = len(image_description)
    ifd.offset_of_image_description[0] = 8 + ifd.bytes.nbytes
    ifd.strip_offsets[0] = 8 + ifd.bytes.nbytes + len(image_description)
    if x.shape[0] == 1:
        ifd.next_ifd_offset[0] = 0
    else:
        ifd.next_ifd_offset[0] = (
                ifd.strip_offsets[0] + x.size * ifd.bits_per_sample[0] // 8)
    """
    We have all our ducks in a row, time to actually write the TIF:
    """
    for fn in (filename, backup_filename):
        try:
            with open(fn, 'wb') as f:
                f.write(b'II*\x00\x08\x00\x00\x00')  # Little tif, turn to page 8
                ifd.bytes.tofile(f)
                f.write(image_description)
                if dtype != x.dtype:  # We have to coerce to a different dtype
                    for z in range(x.shape[0]):  # Convert one at a time (memory)
                        x[z, :, :].astype(dtype).tofile(f)
                else:
                    x.tofile(f)
                for which_header in range(1, x.shape[0]):
                    if which_header == x.shape[0] - 1:
                        ifd.next_ifd_offset[0] = 0
                    else:
                        ifd.next_ifd_offset[0] += ifd.bytes.nbytes
                    ifd.strip_offsets[0] += ifd.strip_byte_counts[0]
                    ifd.bytes.tofile(f)
            break
        except Exception as e:
            print("np_tif.array_to_tif failed to save:")
            print(fn)
            print(" with error:", repr(e))
            if backup_filename is not None and fn != backup_filename:
                continue
            else:
                raise


    return None


class Simple_IFD:
    def __init__(self):
        """
        A very simple TIF IFD with 11 tags (2 + 11*12 + 4 = 138 bytes)
        """
        self.bytes = np.array([
            # Num. entries = 11
            11, 0,
            # NewSubFileType = 0
            254, 0, 4, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # Width = 0
            0, 1, 4, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # Length = 0
            1, 1, 4, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # BitsPerSample = 0
            2, 1, 3, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # PhotometricInterpretation = 1
            6, 1, 3, 0, 1, 0, 0, 0, 1, 0, 0, 0,
            # ImageDescription (num_chars = 0, pointer = 0)
            14, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            # StripOffsets = 0
            17, 1, 4, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # SamplesPerPixel = 1
            21, 1, 3, 0, 1, 0, 0, 0, 1, 0, 0, 0,
            # RowsPerStrip = 0
            22, 1, 3, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # StripByteCounts = 0
            23, 1, 4, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # SampleFormat = 3
            83, 1, 3, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            # Next IFD = 0
            0, 0, 0, 0,
        ], dtype=np.ubyte)
        self.width = self.bytes[22:26].view(dtype=np.uint32)
        self.length = self.bytes[34:38].view(dtype=np.uint32)
        self.bits_per_sample = self.bytes[46:50].view(dtype=np.uint32)
        self.num_chars_in_image_description = self.bytes[66:70].view(np.uint32)
        self.offset_of_image_description = self.bytes[70:74].view(np.uint32)
        self.strip_offsets = self.bytes[82:86].view(np.uint32)
        self.rows_per_strip = self.bytes[106:110].view(np.uint32)
        self.strip_byte_counts = self.bytes[118:122].view(np.uint32)
        self.data_format = self.bytes[130:134].view(np.uint32)
        self.next_ifd_offset = self.bytes[134:138].view(np.uint32)
        return None

    def set_dtype(self, dtype):
        allowed_dtypes = {
            np.dtype('uint8'): (1, 8),
            np.dtype('uint16'): (1, 16),
            np.dtype('uint32'): (1, 32),
            np.dtype('uint64'): (1, 64),
            np.dtype('int8'): (2, 8),
            np.dtype('int16'): (2, 16),
            np.dtype('int32'): (2, 32),
            np.dtype('int64'): (2, 64),
            ##np.dtype('float16'): (3, 16), #Not supported in older numpy?
            np.dtype('float32'): (3, 32),
            np.dtype('float64'): (3, 64),
        }
        try:
            self.data_format[0], self.bits_per_sample[0] = allowed_dtypes[dtype]
        except KeyError:
            warning_string = "Array datatype (%s) not allowed. Allowed types:" % (
                dtype)
            for i in sorted(allowed_dtypes.keys()):
                warning_string += '\n ' + repr(i)
            raise UserWarning(warning_string)
        return None


def get_bytes_from_file(file, offset, num_bytes):
    file.seek(offset)
    return file.read(num_bytes)


def bytes_to_int(x, endian):  # Isn't there a builtin to do this...?
    if endian == 'little':
        return sum(c * 256 ** i for i, c in enumerate(x))
    elif endian == 'big':
        return sum(c * 256 ** (len(x) - 1 - i) for i, c in enumerate(x))
    else:
        raise UserWarning("'endian' must be either big or little")
