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

import processor
import configserver
import github
import filecmp
import os

class TestProcessor(unittest.TestCase):
    def setUp(self):
        configserver._CONGIF['input'] = './tests/data/input.txt'
        configserver._CONGIF['maximum_cache_age'] = 366000  # About 1000 years
        configserver._CONGIF['cache_path'] = './tests/cache'

    def test_file_to_input(self):
        input = processor.file_to_input('./tests/data/input.txt')
        self.assertEqual(input, [github.Github('Top-Ranger', 'kana-keyboard')])

    def test_result_to_file(self):
        result = [(github.Github('Top-Ranger', 'kana-keyboard'), 'DEV')]
        processor.result_to_file(result, './tests/tmp')
        self.assertTrue(filecmp.cmp('./tests/tmp', './tests/data/output.txt'))
        os.remove('./tests/tmp')

    def test_dir_to_learning(self):
        learning_comparison = [
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DATA'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'SUR213'), 'DOCS'),
            (github.Github('Top-Ranger', 'fooling_dnn'), 'EDU'),
            (github.Github('Top-Ranger', 'harbour-reversi'), 'HW'),
            (github.Github('Top-Ranger', 'qnn'), 'OTHER'),
            (github.Github('Top-Ranger', 'kana-keyboard'), 'WEB'),
        ]
        learning = processor.dir_to_learning('./tests/learning/')

        for data in learning:
            self.assertIn(data, learning_comparison)

        self.assertEqual(len(learning_comparison), len(learning))
