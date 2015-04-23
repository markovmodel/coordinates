
# Copyright (c) 2015, 2014 Computational Molecular Biology Group, Free University
# Berlin, 14195 Berlin, Germany.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
Created on 26.01.2015

@author: marscher
'''
import itertools
import unittest

from pyemma.coordinates.clustering.regspace import RegularSpaceClustering
from pyemma.coordinates.data.data_in_memory import DataInMemory
from pyemma.coordinates.api import cluster_regspace

import numpy as np
import pyemma.util.types as types


class RandomDataSource(DataInMemory):

    def __init__(self, a=None, b=None, chunksize=1000, n_samples=5, dim=3):
        """
        creates random values in interval [a,b]
        """
        data = np.random.random((n_samples, dim))
        if a is not None and b is not None:
            data *= (b - a)
            data += a
        super(RandomDataSource, self).__init__(data, chunksize=chunksize)


class TestRegSpaceClustering(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegSpaceClustering, cls).setUpClass()
        np.random.seed(0)

    def setUp(self):
        self.dmin = 0.3
        self.clustering = RegularSpaceClustering(dmin=self.dmin)
        self.clustering.data_producer = RandomDataSource()

    def test_algorithm(self):
        self.clustering.parametrize()

        # correct type of dtrajs
        assert types.is_int_array(self.clustering.dtrajs[0])

        # assert distance for each centroid is at least dmin
        for c in itertools.combinations(self.clustering.clustercenters, 2):
            if np.allclose(c[0], c[1]):  # skip equal pairs
                continue

            dist = np.linalg.norm(c[0] - c[1], 2)

            self.assertGreaterEqual(dist, self.dmin,
                                    "centroid pair\n%s\n%s\n has smaller"
                                    " distance than dmin(%f): %f"
                                    % (c[0], c[1], self.dmin, dist))

    def test_assignment(self):
        self.clustering.parametrize()

        assert len(self.clustering.clustercenters) > 1

        # num states == num _clustercenters?
        self.assertEqual(len(np.unique(self.clustering.dtrajs)),  len(
            self.clustering.clustercenters), "number of unique states in dtrajs"
            " should be equal.")

        data_to_cluster = np.random.random((1000, 3))

        self.clustering.assign(data_to_cluster, stride=1)

    def test_spread_data(self):
        self.clustering.data_producer = RandomDataSource(a=-2, b=2)
        self.clustering.dmin = 2
        self.clustering.parametrize()

    def test1d_data(self):
        data = np.random.random(100)
        cluster_regspace(data, dmin=0.3)

    def test_non_existent_metric(self):
        self.clustering.data_producer = RandomDataSource(a=-2, b=2)
        self.clustering.dmin = 2
        self.clustering.metric = "non_existent_metric"
        with self.assertRaises(ValueError):
            self.clustering.parametrize()

if __name__ == "__main__":
    unittest.main()