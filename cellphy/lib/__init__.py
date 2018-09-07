from .version import __version__

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')

import sys
if '--debug' in sys.argv:
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s | %(message)s')
if 'install' in sys.argv:
    logging.getLogger("llspy.libcudawrapper").setLevel(logging.CRITICAL)


# #libcuda functions
# try:
# 	from .libcudawrapper import deskewGPU as deskew
# 	from .libcudawrapper import affineGPU as affine
# 	from .libcudawrapper import quickDecon as decon
# 	from .libcudawrapper import rotateGPU as rotate
# 	from .libcudawrapper import quickCamcor as camcor
# except Exception:
# 	pass
