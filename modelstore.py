# Copyright (C) 2016,2017 Marcus Soll
# Copyright (C) 2016,2017 Malte Vosgerau
#
# This file is part of ClassifyHub.
#
# ClassifyHub is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ClassifyHub is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ClassifyHub. If not, see <http://www.gnu.org/licenses/>.

import json
import os
import configserver
import logging
import lockfile
import utility


##
# \brief Saves the model of a classifier. The model can be everything the classifier needs to work.
#
# The model can be saved to Modelstore.config as anything that is serialisable as a json.
# Per default (for new Modelstore or after Modelstore.clear()) Modelstore.config is a python dict.
class ModelStore:
    ##
    # \fn __init__(self, name)
    # \brief Constructor.
    #
    # The constructor loads the model if it has been saved in a previous session.
    #
    # \param name String containing the target name of the model. Usually the classifier name.
    #
    def __init__(self, name):
        ##
        # \var config
        # \brief Holds the configuration.
        #
        # As default the conf variable holds an empty dict which can be used, however it is possible to replace
        # it with anything that can be serialised as an JSON (e.g. list).

        self.config = dict()

        if name is '':
            logging.warning('Empty name')
            name = 'UNKNOWN'

        self._dir = configserver.get('model_path')
        self._path = self._dir + '/' + name + '.model'

        if os.path.isdir(self._dir) and os.path.exists(self._path):
            utility.check_stale_lock(self._path + '_LOCK')
            lock = lockfile.LockFile(self._path + '_LOCK')
            with lock:
                with open(self._path, 'r') as file:
                    try:
                        self.config = json.load(file)
                    except:
                        logging.error('Can not load model {}'.format(self._path))

    ##
    # \brief Clears the config by assigning an empty dict.
    #
    # This will not save the cleared model to permanent memory. For this the save method has to be called manually.
    def clear(self):
        self.config = dict()

    ##
    # \brief Saves the model to permanent memory.
    def save(self):
        if not os.path.isdir(self._dir):
            try:
                os.makedirs(self._dir)
            except OSError:
                logging.error('Can not create models directory')
                return

        lock = lockfile.LockFile(self._path + '_LOCK')
        with lock:
            try:
                with open(self._path, 'w') as file:
                    json.dump(self.config, file)
            except:
                logging.error('Can not write model {}' .format(self._path))
