import tempfile
import numpy as np
import mdtraj
import pkg_resources
import os
import logging


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }

def get_bpti_test_data():
    import pkg_resources
    path = pkg_resources.resource_filename(__name__, 'data') + os.path.sep
    from glob import glob
    xtcfiles = glob(path + '/bpti_0*.xtc')
    pdbfile = os.path.join(path, 'bpti_ca.pdb')

    return xtcfiles, pdbfile


def get_top():
    return pkg_resources.resource_filename(__name__, 'data/test.pdb')


def create_traj(top=None, format='.xtc', dir=None, length=1000, start=0):
    trajfile = tempfile.mktemp(suffix=format, dir=dir)
    xyz = np.arange(start*3*3, (start+length) * 3 * 3)
    xyz = xyz.reshape((-1, 3, 3))
    if top is None:
        top = get_top()

    t = mdtraj.load(top)
    t.xyz = xyz
    t.unitcell_vectors = np.array(length * [[0, 0, 1], [0, 1, 0], [1, 0, 0]]).reshape(length, 3, 3)
    t.time = np.arange(length)
    t.save(trajfile)

    return trajfile, xyz, length
