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

def _setup_testing():
    # setup function for testing
    from chainsaw import config
    # do not cache trajectory info in user directory (temp traj files)
    config.use_trajectory_lengths_cache = False
    config.show_progress_bars = False

def _monkey_patch_testing_apply_setting():
    """ this monkey patches the init methods of unittest.TestCase and doctest.DocTestFinder,
    in order to apply internal settings. """
    import unittest
    import doctest
    _old_init = unittest.TestCase.__init__
    def _new_init(self, *args, **kwargs):
        _old_init(self, *args, **kwargs)
        _setup_testing()

    unittest.TestCase.__init__ = _new_init

    _old_init_doc_test_finder = doctest.DocTestFinder.__init__

    def _patched_init(self, *args, **kw):
        _setup_testing()
        _old_init_doc_test_finder(self, *args, **kw)

    doctest.DocTestFinder.__init__ = _patched_init


def get_bpti_test_data():
    import pkg_resources
    path = pkg_resources.resource_filename(__name__, 'data') + os.path.sep
    from glob import glob
    xtcfiles = glob(path + '/bpti_0*.xtc')
    pdbfile = os.path.join(path, 'bpti_ca.pdb')
    assert xtcfiles, xtcfiles
    assert pdbfile, pdbfile

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
