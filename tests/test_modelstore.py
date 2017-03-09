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

import unittest

import modelstore
import configserver
import os
import shutil


class TestModelstore(unittest.TestCase):
    def setUp(self):
        configserver._CONGIF['model_path'] = './tests/models'

    def tearDown(self):
        # Remove the models to always start in a clean environment
        if os.path.exists('./tests/models'):
            shutil.rmtree('./tests/models')

    def test_save(self):
        # create some data
        model = modelstore.ModelStore('test')
        model.config['test1'] = 'test1'
        model.config['test2'] = 2
        model.config['3'] = 3
        model.config['test4'] = [1, 2, 3, 'four']
        model.save()

        # try to get data
        model = modelstore.ModelStore('test')
        self.assertEqual(model.config['test1'], 'test1')
        self.assertEqual(model.config['test2'], 2)
        self.assertEqual(model.config['3'], 3)
        self.assertEqual(model.config['test4'], [1, 2, 3, 'four'])


    def test_clear(self):
        # create some data
        model = modelstore.ModelStore('test')
        model.config['test1'] = 'test1'
        model.config['test2'] = 2
        model.config['3'] = 3
        model.config['test4'] = [1, 2, 3, 'four']

        # clear data
        model.clear()
        self.assertEqual(model.config, dict())