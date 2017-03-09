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

import configserver
import processor
import logging


##
# \brief Starts the learning.
def main():
    data = processor.dir_to_learning(configserver.get('learning_input'))
    if len(data) == 0:
        logging.error('No learning data - aborting')
        return
    logging.log(configserver.output_log_level(), 'Learning started')
    logging.log(configserver.output_log_level(), 'Depending on your system, the size of learning data and the amount that needs to be downloaded this might take a while. Please wait.')
    processor.learning(data)
    logging.log(configserver.output_log_level(), 'Learning finished')


if __name__ == '__main__':
    configserver.parse_args()
    main()
