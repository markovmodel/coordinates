
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
import warnings

from chainsaw.util.reflection import getargspec_no_self

__author__ = 'noe'


class Model(object):
    """ Base class for Chainsaws models

    This class is inspired by sklearn's BaseEstimator class. However, we define parameter names not by the
    current class' __init__ but have to announce them. This allows us to also remember the parameters of model
    superclasses. This class can be mixed with Chainsaw and sklearn Estimators.

    """

    def _get_model_param_names(self):
        r"""Get parameter names for the model"""
        # fetch model parameters
        if hasattr(self, 'set_model_params'):
            set_model_param_method = getattr(self, 'set_model_params')
            # introspect the constructor arguments to find the model parameters
            # to represent
            args, varargs, kw, default = getargspec_no_self(set_model_param_method)
            if varargs is not None:
                raise RuntimeError("Models should always specify their parameters in the signature"
                                   " of their set_model_params (no varargs). %s doesn't follow this convention."
                                   % (self, ))
            # Remove 'self'
            # XXX: This is going to fail if the init is a staticmethod, but
            # who would do this?
            args.pop(0)
            args.sort()
            return args
        else:
            # No parameters known
            return []

    def update_model_params(self, **params):
        r"""Update given model parameter if they are set to specific values"""
        for key, value in list(params.items()):
            if not hasattr(self, key):
                setattr(self, key, value)  # set parameter for the first time.
            elif getattr(self, key) is None:
                setattr(self, key, value)  # update because this parameter is still None.
            elif value is not None:
                setattr(self, key, value)  # only overwrite if set to a specific value (None does not overwrite).

    def get_model_params(self, deep=True):
        r"""Get parameters for this model.

        Parameters
        ----------
        deep: boolean, optional
            If True, will return the parameters for this estimator and
            contained subobjects that are estimators.
        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.
        """
        out = dict()
        for key in self._get_model_param_names():
            # We need deprecation warnings to always be on in order to
            # catch deprecated param values.
            # This is set in utils/__init__.py but it gets overwritten
            # when running under python3 somehow.
            warnings.simplefilter("always", DeprecationWarning)
            try:
                with warnings.catch_warnings(record=True) as w:
                    value = getattr(self, key, None)
                if len(w) and w[0].category == DeprecationWarning:
                    # if the parameter is deprecated, don't show it
                    continue
            finally:
                warnings.filters.pop(0)

            # XXX: should we rather test if instance of estimator?
            if deep and hasattr(value, 'get_params'):
                deep_items = list(value.get_params().items())
                out.update((key + '__' + k, val) for k, val in deep_items)
            out[key] = value
        return out
