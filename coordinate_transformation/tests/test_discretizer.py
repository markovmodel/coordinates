'''
Created on 19.01.2015

@author: marscher
'''
import unittest

from pyemma.coordinates.coordinate_transformation.clustering.uniform_time_clustering import UniformTimeClustering
from pyemma.coordinates.coordinate_transformation.discretizer import Discretizer
from pyemma.coordinates.coordinate_transformation.io.feature_reader import FeatureReader
from pyemma.coordinates.coordinate_transformation.io.featurizer import MDFeaturizer
from pyemma.coordinates.coordinate_transformation.transform.tica import TICA
from pyemma.coordinates.transform.tica_amuse import Amuse
import numpy as np


#@unittest.skip('changed interface')
class TestDiscretizer(unittest.TestCase):

    def setUp(self):
        """ recreate Discretizer for each test case"""
        # TODO: fix test data
        trajfiles = ['/home/marscher/kchan/traj01_sliced.xtc']
        topfile = '/home/marscher/kchan/Traj_Structure.pdb'

        # create featurizer
        featurizer = MDFeaturizer(topfile)
        sel = np.array([(0, 20), (200, 320), (1300, 1500)])
        featurizer.distances(sel)
        # feature reader
        reader = FeatureReader(trajfiles, topfile)

        self.tica = TICA(lag=10, output_dimension=2)
        self.tica.dataproducer = reader

        clustering = UniformTimeClustering(k=2)

        self.D = Discretizer(reader, transform=self.tica, cluster=clustering)

    def testChunksizeResultsTica(self):
        chunk = 31
        eps = 1e-3

        self.D.run()

        # store mean and cov
        tica = self.D.transformers[-1]
        assert isinstance(tica, TICA)
        cov = tica.cov.copy()
        mean = tica.mu.copy()
        # ------- run again -------
        # reset norming factor
        tica.N = 0

        self.D.chunksize = chunk
        for t in self.D.transformers:
            t.parameterized = False

        self.D.run()

        np.testing.assert_allclose(tica.mu, mean, atol=eps)
        np.testing.assert_allclose(tica.cov, cov, atol=eps)

    @unittest.skip("not impled")
    def compareWithAmuse(self):
        # TODO: compare
        amuse = Amuse.compute(self.files, lag=10)
        print amuse.mean

if __name__ == "__main__":
    unittest.main()
