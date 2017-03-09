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

import run_validate
import github
import configserver


class TestRunValidate(unittest.TestCase):
    def setUp(self):
        configserver._CONGIF['maximum_cache_age'] = 366000  # About 1000 years
        configserver._CONGIF['cache_path'] = './tests/cache'

    def test_calculate_precision(self):
        truth = [
            (github.Github('Top-Ranger', 'qnn'), 'DEV'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DATA')
        ]

        data1 = [
            (github.Github('Top-Ranger', 'qnn'), 'DATA'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DATA')
        ]

        data2 = [
            (github.Github('Top-Ranger', 'qnn'), 'DEV'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DEV')
        ]

        self.assertEqual(run_validate.calculate_precision(truth, truth, 'DEV'), 1.0)
        self.assertEqual(run_validate.calculate_precision(truth, data1, 'DEV'), 1.0)
        self.assertEqual(run_validate.calculate_precision(truth, data2, 'DEV'), 2/3)

    def test_calculate_recall(self):
        truth = [
            (github.Github('Top-Ranger', 'qnn'), 'DEV'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DATA')
        ]

        data1 = [
            (github.Github('Top-Ranger', 'qnn'), 'DATA'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DATA')
        ]

        data2 = [
            (github.Github('Top-Ranger', 'qnn'), 'DEV'),
            (github.Github('Top-Ranger', 'bakery'), 'DEV'),
            (github.Github('Top-Ranger', 'CHI2016-SUR-datasets'), 'DEV')
        ]

        self.assertEqual(run_validate.calculate_recall(truth, truth, 'DEV'), 1.0)
        self.assertEqual(run_validate.calculate_recall(truth, data1, 'DEV'), 0.5)
        self.assertEqual(run_validate.calculate_recall(truth, data2, 'DEV'), 1.0)