__author__ = 'noe'

import psutil
import numpy as np

from io.feature_reader import FeatureReader
from transform.transformer import Transformer
from pyemma.util.log import getLogger


logger = getLogger('Discretizer')
__all__ = ['Discretizer']


class Discretizer(object):

    """
    A Discretizer gets a FeatureReader, which defines the features (distances,
    angles etc.) of given trajectory data and passes this data in a memory
    efficient way through the given pipeline of a Transformer and a clustering.
    The clustering object is responsible for assigning the data to discrete
    states.

    Currently the constructor will calculate everything instantly.


    Parameters
    ----------
    reader : a FeatureReader object
        reads trajectory data and selects features.
    transform : a Transformer object (optional)
        the Transformer will be used to e.g reduce dimensionality of inputs.
    cluster : a clustering object
        used to assign input data to discrete states/ discrete trajectories.
    """

    def __init__(self, reader, transform=None, cluster=None):

        # check input
        assert isinstance(reader, FeatureReader), \
            'reader is not of the correct type'
        if (transform is not None):
            assert isinstance(transform, Transformer), \
                'transform is not of the correct type'
        if cluster is None:
            raise ValueError('Must specify a clustering algorithm!')
        else:
            assert isinstance(cluster, Transformer), \
                'cluster is not of the correct type'

        # ------------------------------------------------------------------------------------------
        # PIPELINE CONSTRUCTION

        self.transformers = []

        # add reader first
        self.transformers.append(reader)
        last = reader

        # add transform if any
        if transform is not None:
            self.transformers.append(transform)
            transform.data_producer = last
            last = transform

        # add clustering
        self.transformers.append(cluster)
        cluster.data_producer = last

        # ------------------------------------------------------------------------------------------
        # MEMORY MANAGEMENT

        M = psutil.virtual_memory()[1]  # available RAM
        logger.info("available RAM: %i" % M)
        const_mem = long(0)
        mem_per_frame = long(0)
        for trans in self.transformers:
            mem_per_frame += trans.get_memory_per_frame()
            const_mem += trans.get_constant_memory()
        logger.info("per-frame memory requirements: %i" % mem_per_frame)
        # maximum allowed chunk size
        logger.info("const mem: %i" % const_mem)
        chunksize = (M - const_mem) / mem_per_frame
        if chunksize < 0:
            raise MemoryError(
                'Not enough memory for desired transformation chain!')

        # is this chunksize sufficient to store full trajectories?
        # TODO: ensure chunksize does not leave a last single frame at the end
        # to avoid trouble
        chunksize = min(chunksize, np.max(reader.trajectory_lengths()))
        logger.info("resulting chunk size: %i" % chunksize)
        # set chunksize
        for trans in self.transformers:
            trans.chunksize = chunksize

        # any memory unused? if yes, we can store results
        Mfree = M - const_mem - chunksize * mem_per_frame
        logger.info("free memory: %i" % Mfree)

        # starting from the back of the pipeline, store outputs if possible
        for trans in reversed(self.transformers):
            mem_req_trans = trans.n_frames_total() * \
                trans.get_memory_per_frame()
            if Mfree > mem_req_trans:
                Mfree -= mem_req_trans
                # TODO: before we are allowed to call this method, we have to ensure all memory requirements are correct!
                #trans.operate_in_memory()
                logger.info("spending %i bytes to operate in main memory: %s "
                            % (mem_req_trans,  trans.describe()))

        # ------------------------------------------------------------------------------------------
        # PARAMETRIZE PIPELINE
        for trans in self.transformers:
            trans.parametrize()