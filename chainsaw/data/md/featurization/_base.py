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
'''
Created on 15.02.2016

@author: marscher
'''
from chainsaw.util.annotators import deprecated


class Feature(object):

    @property
    def dimension(self):
        return self._dim

    @dimension.setter
    def dimension(self, val):
        assert isinstance(val, int)
        self._dim = val

    @deprecated('use transform(traj)')
    def map(self, traj):
        return self.transform(traj)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
