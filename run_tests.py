#!/usr/bin/env python3

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


##
# \brief Starts the unit tests.
def main():
    # Build test suite
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().discover("./tests/"))

    # Run tests
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
