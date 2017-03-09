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

import utility
import lockfile
import shutil
import os
import multiprocessing


class TestUtility(unittest.TestCase):
    def setUp(self):
        pass

    def test_validate_url_positive(self):
        self.assertTrue(utility.validate_url('https://github.com/ericfischer/housing-inventory'))
        self.assertTrue(utility.validate_url('https://github.com/rubymonstas-zurich/rubymonstas-zurich.github.io'))
        self.assertTrue(utility.validate_url(' https://github.com/rubymonstas-zurich/rubymonstas-zurich.github.io \n'))
        self.assertTrue(utility.validate_url('https://github.com/datasciencelabs/2016/'))

    def test_validate_url_negative(self):
        self.assertFalse(utility.validate_url('https://bitbucket.org/mgorny/eclean-kernel'))
        self.assertFalse(utility.validate_url('https://github.com/ericfischer/housing-inventory/tree/master/R-scripts'))
        self.assertFalse(utility.validate_url('https://github.com/rubymonstas-zurich/rubymonstas-zurich github io'))

    def test_get_dev_and_repo(self):
        # Positive
        self.assertEqual(utility.get_dev_and_repo('https://github.com/ericfischer/housing-inventory'), ('ericfischer', 'housing-inventory'))
        self.assertEqual(utility.get_dev_and_repo('https://github.com/rubymonstas-zurich/rubymonstas-zurich.github.io'), ('rubymonstas-zurich', 'rubymonstas-zurich.github.io'))
        self.assertEqual(utility.get_dev_and_repo(' https://github.com/rubymonstas-zurich/rubymonstas-zurich.github.io \n'), ('rubymonstas-zurich', 'rubymonstas-zurich.github.io'))

        # Negative
        self.assertEqual(utility.get_dev_and_repo('https://bitbucket.org/mgorny/eclean-kernel'), ('', ''))

    def test_get_classes(self):
        classes = utility.get_classes()
        self.assertTrue(len(classes) is 7, 'Wrong number of classes')
        self.assertTrue('DEV' in classes)
        self.assertTrue('EDU' in classes)
        self.assertTrue('DOCS' in classes)
        self.assertTrue('HW' in classes)
        self.assertTrue('OTHER' in classes)
        self.assertTrue('DATA' in classes)
        self.assertTrue('WEB' in classes)

    def test_get_zero_class_dict(self):
        classes = utility.get_classes()
        zero_dict = utility.get_zero_class_dict()

        compare = dict()
        for c in classes:
            compare[c] = 0.0

        self.assertEqual(zero_dict, compare)

    def test_get_best_class(self):
        class_dict = utility.get_zero_class_dict()
        class_dict['DEV'] = 0.1
        # Simple test
        self.assertEqual(utility.get_best_class(class_dict), 'DEV')

        # Test negative numbers
        class_dict['HW'] = -0.5
        self.assertEqual(utility.get_best_class(class_dict), 'DEV')

        # Test huge numbers
        class_dict['OTHER'] = 9999999999
        self.assertEqual(utility.get_best_class(class_dict), 'OTHER')

    def test_edit_distance(self):
        long_string = ''
        long_string_iterations = 151
        for _ in range(long_string_iterations):
            long_string += 'aaaaa0'

        # Equal
        self.assertEqual(utility.edit_distance('test', 'test'), 0)
        self.assertEqual(utility.edit_distance('', ''), 0)
        self.assertEqual(utility.edit_distance('ClassifyHub', 'ClassifyHub'), 0)
        self.assertEqual(utility.edit_distance(long_string, long_string), 0)

        # Delete / Insert
        self.assertEqual(utility.edit_distance('ClassifyHub', 'Classify'), 3)
        self.assertEqual(utility.edit_distance('Hub', 'ClassifyHub'), 8)
        self.assertEqual(utility.edit_distance('', long_string), len(long_string))
        self.assertEqual(utility.edit_distance(long_string, ''), len(long_string))

        # Replace
        self.assertEqual(utility.edit_distance('Classifyhub', 'ClassifyHub'), 1)
        self.assertEqual(utility.edit_distance('ClassifyHub', 'Classifyhub'), 1)
        self.assertEqual(utility.edit_distance('classifyHub', 'Classifyhub'), 2)
        self.assertEqual(utility.edit_distance(long_string, long_string.replace('0', '1')), long_string_iterations)

    def test_check_stale_lock(self):
        # Stale lock has to be created in an other process - otherwise no error on failure will be raised
        def create_stale_lock():
            stale_lock = lockfile.LockFile('./tests/lock_test/TEST_LOCK')
            stale_lock.acquire(timeout=1)
            del stale_lock

        if os.path.exists('./tests/lock_test/'):
            shutil.rmtree('./tests/lock_test/')
        os.mkdir('./tests/lock_test/')

        target_lock = lockfile.LockFile('./tests/lock_test/TEST_LOCK')
        # No prior lock
        utility.check_stale_lock('./tests/lock_test/TEST_LOCK', 2)
        target_lock.acquire(timeout=1)
        target_lock.release()

        # With stale lock
        process = multiprocessing.Process(target=create_stale_lock)
        process.start()
        process.join()

        utility.check_stale_lock('./tests/lock_test/TEST_LOCK', 2)
        target_lock.acquire(timeout=1)
        target_lock.release()

        shutil.rmtree('./tests/lock_test/')
