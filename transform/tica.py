'''
Created on 19.01.2015

@author: marscher
'''
from .transformer import Transformer
from pyemma.util.linalg import eig_corr
from pyemma.util.log import getLogger
import numpy as np

log = getLogger('TICA')
__all__ = ['TICA']


class TICA(Transformer):

    r"""
    Time-lagged independent component analysis (TICA)

    Given a sequence of multivariate data X_t, computes the mean-free
    covariance and time-lagged covariance matrix:

    .. math::

        C_0 =   (X_t - \mu)^T (X_t - \mu) \
        C_{\tau} = (X_t - \mu)^T (X_t+\tau - \mu)
    and solves the eigenvalue problem

    .. math:: C_{tau} r_i = C_0 \lambda_i r_i

    where :math:`r_i` are the independent components and :math:`\lambda_i` are
    their respective normalized time-autocorrelations. The eigenvalues are
    related to the relaxation timescale by

    .. math:: t_i = -\tau / ln |\lambda_i|

    When used as a dimension reduction method, the input data is projected
    onto the dominant independent components.

    Parameters
    ----------
    lag : int
        lag time
    output_dim : int
        how many significant TICS to use to reduce dimension of input data
    epsilon : float
        eigenvalue norm cutoff. Eigenvalues of C0 with norms <= epsilon will be
        cut off. The remaining number of Eigenvalues define the size
        of the output.

    """

    def __init__(self, lag, output_dimension, epsilon=1e-6):
        super(TICA, self).__init__()

        self.lag = lag
        self.output_dim = output_dimension
        self.epsilon = epsilon

        # covariances
        self.cov = None
        self.cov_tau = None
        # mean
        self.mu = None
        self.N = 0
        self.eigenvalues = None
        self.eigenvectors = None

    def describe(self):
        return "[TICA, lag = %i; output dimension = %i]" \
            % (self.lag, self.output_dimension())

    def dimension(self):
        """
        Returns the number of output dimensions

        :return:
        """
        return self.output_dim

    def output_dimension(self):
        return self.output_dim

    def get_constant_memory(self):
        # TODO: change me
        dim = self.data_producer.dimension()
        return ((2 * dim ** 2) + dim) * 8

    def param_init(self):
        """
        Initializes the parametrization.

        :return:
        """
        self.N = 0
        # create mean array and covariance matrices
        self.mu = np.zeros(self.data_producer.dimension())
        dim = self.data_producer.dimension()
        assert dim > 0, "zero dimension from data producer"
        self.cov = np.zeros((dim, dim))
        self.cov_tau = np.zeros_like(self.cov)

        log.info("Running TICA lag=%i; shape cov=(%i, %i)" % (self.lag, dim, dim))

    def param_add_data(self, X, itraj, t, first_chunk, last_chunk_in_traj, last_chunk, ipass, Y=None):
        """
        Chunk-based parameterization of TICA. Iterates through all data twice. In the first pass, the
        data means are estimated, in the second pass the covariance and time-lagged covariance
        matrices are estimated. Finally, the generalized eigenvalue problem is solved to determine
        the independent components.

        :param X:
            coordinates. axis 0: time, axes 1-..: coordinates
        :param itraj:
            index of the current trajectory
        :param t:
            time index of first frame within trajectory
        :param first_chunk:
            boolean. True if this is the first chunk globally.
        :param last_chunk_in_traj:
            boolean. True if this is the last chunk within the trajectory.
        :param last_chunk:
            boolean. True if this is the last chunk globally.
        :param ipass:
            number of pass through data
        :param Y:
            time-lagged data (if available)
        :return:
        """
        if ipass == 0:
            # TODO: maybe use stable sum here, since small chunksizes accumulate more errors
            self.mu += np.sum(X, axis=0)
            self.N += np.shape(X)[0]

            if last_chunk:
                log.debug("mean before norming:\n%s" % self.mu)
                log.debug("norming mean by %i" % self.N)
                self.mu /= self.N
                log.info("calculated mean:\n%s" % self.mu)

        if ipass == 1:
            X_meanfree = X - self.mu
            Y_meanfree = Y - self.mu
            self.cov += np.dot(X_meanfree.T, X_meanfree)
            self.cov_tau += np.dot(X_meanfree.T, Y_meanfree)

            if last_chunk:
                return True  # finished!

        return False  # not finished yet.

    def param_finish(self):
        """ Finalizes the parametrization.
        """
        # norm
        self.cov /= self.N - 1
        self.cov_tau /= self.N - self.lag - 1

        # symmetrize covariance matrices
        self.cov = self.cov + self.cov.T
        self.cov /= 2.0

        self.cov_tau = self.cov_tau + self.cov_tau.T
        self.cov_tau /= 2.0

        self.eigenvalues, self.eigenvectors = \
            eig_corr(self.cov, self.cov_tau, self.epsilon)

    def map(self, X):
        """Projects the data onto the dominant independent components.

        :param X: the input data
        :return: the projected data
        """
        X_meanfree = X - self.mu
        Y = np.dot(X_meanfree, self.eigenvectors[:, 0:self.output_dim])
        return Y