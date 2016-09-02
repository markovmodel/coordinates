
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

from __future__ import absolute_import, print_function

from chainsaw._ext.sklearn_base import BaseEstimator as _BaseEstimator
from chainsaw.base.loggable import Loggable as _Loggable

__author__ = 'noe, marscher'


class Estimator(_BaseEstimator, _Loggable):
    """ Base class for Chainsaws estimators """
    # flag indicating if estimator's estimate method has been called
    _estimated = False

    def estimate(self, X, **params):
        """ Estimates the model given the data X

        Parameters
        ----------
        X : object
            A reference to the data from which the model will be estimated
        params : dict
            New estimation parameter values. The parameters must that have been
            announced in the __init__ method of this estimator. The present
            settings will overwrite the settings of parameters given in the
            __init__ method, i.e. the parameter values after this call will be
            those that have been used for this estimation. Use this option if
            only one or a few parameters change with respect to
            the __init__ settings for this run, and if you don't need to
            remember the original settings of these changed parameters.

        Returns
        -------
        estimator : object
            The estimated estimator with the model being available.

        """
        # set params
        if params:
            self.set_params(**params)
        self._model = self._estimate(X)
        self._estimated = True
        return self

    def _estimate(self, X):
        raise NotImplementedError(
            'You need to overload the _estimate() method in your Estimator implementation!')

    def fit(self, X):
        """Estimates parameters - for compatibility with sklearn.

        Parameters
        ----------
        X : object
            A reference to the data from which the model will be estimated

        Returns
        -------
        estimator : object
            The estimator (self) with estimated model.

        """
        self.estimate(X)
        return self

    @property
    def model(self):
        """The model estimated by this Estimator"""
        try:
            return self._model
        except AttributeError:
            raise AttributeError(
                'Model has not yet been estimated. Call estimate(X) or fit(X) first')
