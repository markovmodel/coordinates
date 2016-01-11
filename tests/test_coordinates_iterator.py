import unittest
import numpy as np

from pyemma.coordinates.data import DataInMemory


class TestCoordinatesIterator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = [np.random.random((100, 3)) for _ in range(3)]

    def test_current_trajindex(self):
        r = DataInMemory(self.d)
        expected_itraj = 0
        for itraj, X in r.iterator(chunk=0):
            assert itraj == expected_itraj
            expected_itraj += 1

        expected_itraj = -1
        it = r.iterator(chunk=16)
        for itraj, X in it:
            if it.pos == 0:
                expected_itraj += 1
            assert itraj == expected_itraj == it.current_trajindex

    def test_skip(self):
        r = DataInMemory(self.d)
        lagged_it = r.iterator(lag=5)
        assert lagged_it._it.skip == 0
        assert lagged_it._it_lagged.skip == 5

        it = r.iterator()
        for itraj, X in it:
            if itraj == 0:
                it.skip = 5
            if itraj == 1:
                assert it.skip == 5

    def test_chunksize(self):
        r = DataInMemory(self.d)
        cs = np.arange(1, 17)
        i = 0
        it = r.iterator(chunk=cs[i])
        for itraj, X in it:
            if not it.last_chunk_in_traj:
                assert len(X) == it.chunksize
            else:
                assert len(X) <= it.chunksize
            i += 1
            i %= len(cs)
            it.chunksize = cs[i]
            assert it.chunksize == cs[i]

    def test_last_chunk(self):
        r = DataInMemory(self.d)
        it = r.iterator(chunk=0)
        for itraj, X in it:
            assert it.last_chunk_in_traj
            if itraj == 2:
                assert it.last_chunk

    def test_stride(self):
        r = DataInMemory(self.d)
        stride = np.arange(1, 17)
        i = 0
        it = r.iterator(stride=stride[i], chunk=1)
        for _ in it:
            i += 1
            i %= len(stride)
            it.stride = stride[i]
            assert it.stride == stride[i]

    def test_return_trajindex(self):
        r = DataInMemory(self.d)
        it = r.iterator(chunk=0)
        it.return_traj_index = True
        assert it.return_traj_index is True
        for tup in it:
            assert len(tup) == 2
        it.reset()
        it.return_traj_index = False
        assert it.return_traj_index is False
        itraj = 0
        for tup in it:
            np.testing.assert_equal(tup, self.d[itraj])
            itraj += 1

        for tup in r.iterator(return_trajindex=True):
            assert len(tup) == 2
        itraj = 0
        for tup in r.iterator(return_trajindex=False):
            np.testing.assert_equal(tup, self.d[itraj])
            itraj += 1

    def test_pos(self):
        r = DataInMemory(self.d)
        r.chunksize = 17
        it = r.iterator()
        t = 0
        for itraj, X in it:
            assert t == it.pos
            t += len(X)
            if it.last_chunk_in_traj:
                t = 0