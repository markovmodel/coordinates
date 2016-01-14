# This file is part of PyEMMA.
#
# Copyright (c) 2015, 2014 Computational Molecular Biology Group, Freie Universitaet Berlin (GER)
#
# PyEMMA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
import os
import tempfile
import unittest
from unittest import TestCase
import numpy as np
import pyemma.coordinates.api as coor
import pkg_resources
import mdtraj
from six.moves import range

from pyemma.coordinates.data import DataInMemory
from pyemma.coordinates.data._base.datasource import IteratorState
from pyemma.coordinates.data.fragmented_trajectory_reader import FragmentedTrajectoryReader


class TestRandomAccessStride(TestCase):
    def setUp(self):
        self.dim = 5
        self.data = [np.random.random((100, self.dim)),
                     np.random.random((20, self.dim)),
                     np.random.random((20, self.dim))]
        self.stride = np.asarray([
            [0, 1], [0, 3], [0, 3], [0, 5], [0, 6], [0, 7],
            [2, 1], [2, 1]
        ])
        self.stride2 = np.asarray([[2, 0]])

    def test_is_random_accessible(self):
        dim = DataInMemory(self.data)
        frag = FragmentedTrajectoryReader([[self.data]])
        assert dim.is_random_accessible is True
        assert frag.is_random_accessible is False

    def test_slice_random_access(self):
        dim = DataInMemory(self.data)

        all_data = dim.ra_itraj_cuboid[:, :, :]
        # the remaining 80 frames of the first trajectory should be truncated
        np.testing.assert_equal(all_data.shape, (3, 20, self.dim))
        # should coincide with original data
        np.testing.assert_equal(all_data, np.array((self.data[0][:20], self.data[1], self.data[2])))
        # we should be able to select the 1st trajectory
        np.testing.assert_equal(dim.ra_itraj_cuboid[0], np.array([self.data[0]]))
        # select only dimensions 1:3 of 2nd trajectory with every 2nd frame
        np.testing.assert_equal(dim.ra_itraj_cuboid[1, ::2, 1:3], np.array([self.data[1][::2, 1:3]]))
        # select only last dimension of 1st trajectory every 17th frame
        np.testing.assert_equal(dim.ra_itraj_cuboid[0, ::17, -1], np.array([np.array([self.data[0][::17, -1]]).T]))

    def test_slice_random_access_linear(self):
        dim = DataInMemory(self.data)

        all_data = dim.ra_linear[:, :]
        # all data should be all data concatenated
        np.testing.assert_equal(all_data, np.concatenate(self.data))
        # select first 5 frames
        np.testing.assert_equal(dim.ra_linear[:5], self.data[0][:5])
        # select only dimensions 1:3 of every 2nd frame
        np.testing.assert_equal(dim.ra_linear[::2, 1:3], np.concatenate(self.data)[::2, 1:3])

    def test_slice_random_access_linear_itraj(self):
        dim = DataInMemory(self.data)

        all_data = dim.ra_itraj_linear[:, :, :]
        # all data should be all data concatenated
        np.testing.assert_equal(all_data, np.concatenate(self.data))

        # if requested 130 frames, this should yield the first two trajectories and half of the third
        np.testing.assert_equal(dim.ra_itraj_linear[:, :130], np.concatenate(self.data)[:130])
        # now request first 30 frames of the last two trajectories
        np.testing.assert_equal(dim.ra_itraj_linear[[1, 2], :30], np.concatenate((self.data[1], self.data[2]))[:30])

    def test_slice_random_access_jagged(self):
        dim = DataInMemory(self.data)

        all_data = dim.ra_itraj_jagged[:, :, :]
        for idx in range(3):
            np.testing.assert_equal(all_data[idx], self.data[idx])

        jagged = dim.ra_itraj_jagged[:, :30]
        for idx in range(3):
            np.testing.assert_equal(jagged[idx], self.data[idx][:30])

        jagged_last_dim = dim.ra_itraj_jagged[:, :, -1]
        for idx in range(3):
            np.testing.assert_equal(jagged_last_dim[idx], self.data[idx][:, -1])

    def test_iterator_context(self):
        dim = DataInMemory(np.array([1]))

        ctx = dim.iterator(stride=1).state
        assert ctx.stride == 1
        assert ctx.uniform_stride
        assert ctx.is_stride_sorted()
        assert ctx.traj_keys is None

        ctx = dim.iterator(stride=np.asarray([[0, 0], [0, 1], [0, 2], [1, 1], [1, 2], [1, 3]])).state
        assert not ctx.uniform_stride
        assert ctx.is_stride_sorted()
        np.testing.assert_array_equal(ctx.traj_keys, np.array([0, 1]))

        # require sorted random access
        dim._needs_sorted_random_access_stride = True

        # sorted within trajectory, not sorted by trajectory key
        with self.assertRaises(ValueError):
            dim.iterator(stride=np.asarray([[1, 1], [1, 2], [1, 3], [0, 0], [0, 1], [0, 2]]))

        # sorted by trajectory key, not within trajectory
        with self.assertRaises(ValueError):
            dim.iterator(stride=np.asarray([[0, 0], [0, 1], [0, 2], [1, 1], [1, 5], [1, 3]]))

        np.testing.assert_array_equal(ctx.ra_indices_for_traj(0), np.array([0, 1, 2]))
        np.testing.assert_array_equal(ctx.ra_indices_for_traj(1), np.array([1, 2, 3]))

    def test_data_in_memory_random_access(self):
        # access with a chunk_size that is larger than the largest index list of stride
        data_in_memory = coor.source(self.data, chunk_size=10)
        out1 = data_in_memory.get_output(stride=self.stride)

        # access with a chunk_size that is smaller than the largest index list of stride
        data_in_memory = coor.source(self.data, chunk_size=1)
        out2 = data_in_memory.get_output(stride=self.stride)

        # access in full trajectory mode
        data_in_memory = coor.source(self.data, chunk_size=0)
        out3 = data_in_memory.get_output(stride=self.stride)

        for idx in np.unique(self.stride[:, 0]):
            np.testing.assert_array_almost_equal(self.data[idx][self.stride[self.stride[:, 0] == idx][:, 1]], out1[idx])
            np.testing.assert_array_almost_equal(out1[idx], out2[idx])
            np.testing.assert_array_almost_equal(out2[idx], out3[idx])

    def test_data_in_memory_without_first_two_trajs(self):
        data_in_memory = coor.source(self.data, chunk_size=10)
        out = data_in_memory.get_output(stride=self.stride2)
        np.testing.assert_array_almost_equal(out[2], [self.data[2][0]])

    def test_csv_filereader_random_access(self):
        tmpfiles = [tempfile.mktemp(suffix='.dat') for _ in range(0, len(self.data))]
        try:
            for idx, tmp in enumerate(tmpfiles):
                np.savetxt(tmp, self.data[idx])

            # large enough chunksize
            csv_fr = coor.source(tmpfiles, chunk_size=10)
            out1 = csv_fr.get_output(stride=self.stride)

            # small chunk size
            np_fr = coor.source(tmpfiles, chunk_size=1)
            out2 = np_fr.get_output(stride=self.stride)

            for idx in np.unique(self.stride[:, 0]):
                np.testing.assert_array_almost_equal(self.data[idx][self.stride[self.stride[:, 0] == idx][:, 1]],
                                                     out1[idx])
                np.testing.assert_array_almost_equal(out1[idx], out2[idx])
        finally:
            for tmp in tmpfiles:
                try:
                    os.unlink(tmp)
                except EnvironmentError:
                    pass

    def test_numpy_filereader_random_access(self):
        tmpfiles = [tempfile.mktemp(suffix='.npy') for _ in range(0, len(self.data))]
        try:
            for idx, tmp in enumerate(tmpfiles):
                np.save(tmp, self.data[idx])
            # large enough chunk size
            np_fr = coor.source(tmpfiles, chunk_size=10)
            out1 = np_fr.get_output(stride=self.stride)

            # small chunk size
            np_fr = coor.source(tmpfiles, chunk_size=1)
            out2 = np_fr.get_output(stride=self.stride)

            # full traj mode
            np_fr = coor.source(tmpfiles, chunk_size=0)
            out3 = np_fr.get_output(stride=self.stride)

            for idx in np.unique(self.stride[:, 0]):
                np.testing.assert_array_almost_equal(self.data[idx][self.stride[self.stride[:, 0] == idx][:, 1]],
                                                     out1[idx])
                np.testing.assert_array_almost_equal(out1[idx], out2[idx])
                np.testing.assert_array_almost_equal(out2[idx], out3[idx])

        finally:
            for tmp in tmpfiles:
                try:
                    os.unlink(tmp)
                except EnvironmentError:
                    pass

    def test_transformer_iterator_random_access(self):
        kmeans = coor.cluster_kmeans(self.data, k=2)
        kmeans.in_memory = True

        for cs in range(0, 5):
            kmeans.chunksize = cs
            ref_stride = {0: 0, 1: 0, 2: 0}
            it = kmeans.iterator(stride=self.stride)
            for x in it:
                ref_stride[x[0]] += len(x[1])
            for key in list(ref_stride.keys()):
                expected = len(it.ra_indices_for_traj(key))
                assert ref_stride[key] == expected, \
                    "Expected to get exactly %s elements of trajectory %s, but got %s for chunksize=%s" \
                    % (expected, key, ref_stride[key], cs)

    def test_feature_reader_random_access(self):
        from pyemma.coordinates.tests.test_featurereader import create_traj

        topfile = pkg_resources.resource_filename(__name__, 'data/test.pdb')
        trajfiles = []
        for _ in range(3):
            f, _, _ = create_traj(topfile)
            trajfiles.append(f)
        try:
            source = coor.source(trajfiles, top=topfile)
            source.chunksize = 2

            out = source.get_output(stride=self.stride)
            keys = np.unique(self.stride[:, 0])
            for i, coords in enumerate(out):
                if i in keys:
                    traj = mdtraj.load(trajfiles[i], top=topfile)
                    np.testing.assert_equal(coords,
                                            traj.xyz[
                                                np.array(self.stride[self.stride[:, 0] == i][:, 1])
                                            ].reshape(-1, 9))
        finally:
            for t in trajfiles:
                try:
                    os.unlink(t)
                except EnvironmentError:
                    pass


if __name__ == '__main__':
    unittest.main()
