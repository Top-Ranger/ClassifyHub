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

import classifier
import configserver
import github
import utility
import shutil
import os

class TestClassifier(unittest.TestCase):
    def setUp(self):
        # setup config
        configserver._CONGIF['maximum_cache_age'] = 366000 # About 1000 years
        configserver._CONGIF['cache_path'] = './tests/cache'
        configserver._CONGIF['model_path'] = './tests/models'

        self.classifier = classifier.get_all_classifiers()
        self.github_list = [github.Github('Top-Ranger', 'kana-keyboard'),
                            github.Github('Top-Ranger', 'CHI2016-SUR-datasets'),
                            github.Github('Top-Ranger', 'SPtP_learningdb'),
                            github.Github('Top-Ranger', 'SUR213'),
                            github.Github('Top-Ranger', 'bakery'),
                            github.Github('Top-Ranger', 'fooling_dnn'),
                            github.Github('Top-Ranger', 'harbour-hiragana'),
                            github.Github('Top-Ranger', 'harbour-katakana'),
                            github.Github('Top-Ranger', 'harbour-reversi'),
                            github.Github('Top-Ranger', 'qnn'),
                            github.Github('Top-Ranger', 'SPtP')]

    def tearDown(self):
        # Remove the models to always start in a clean environment
        if os.path.exists('./tests/models'):
            shutil.rmtree('./tests/models')

    def test_classifier_instance(self):
        for c in self.classifier:
            self.assertIsInstance(c, classifier.Classifier)

    def test_unique_names(self):
        names = set()
        for c in self.classifier:
            names.add(c.name())

        self.assertEqual(len(names), len(self.classifier), 'Some names of classifier are not unique')

    def test_learning(self):
        for c in self.classifier:
            try:
                c.learn([(x, 'DEV') for x in self.github_list]) # correct class does not matter
            except:
                self.fail('{}: Throws exception'.format(c.name()))

    def test_classify(self):
        # First learn the models.
        # The training is covered in an other test case so it should be fine.
        for c in self.classifier:
            c.learn([(x, 'DEV') for x in self.github_list])  # correct class does not matter

            result = c.classify(self.github_list[0])

            # All classes represented
            self.assertEqual(result.keys(), utility.get_zero_class_dict().keys())

            # Result is in range
            for result_class in result:
                self.assertTrue(0.0 <= result[result_class] <= 1.0, 'Class {} of classifier {} is out of range ({})'.format(result_class, c.name(), result[result_class]))