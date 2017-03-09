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
# \brief Starts the batch processing.
def main():
    data = processor.file_to_input(configserver.get('input'))
    if len(data) == 0:
        logging.error('No learning data - aborting')
        return
    logging.log(configserver.output_log_level(), 'Batch processing started')
    result = processor.batch(data)
    processor.result_to_file(result, configserver.get('output'))
    logging.log(configserver.output_log_level(), 'Batch processing finished')


if __name__ == '__main__':
    configserver.parse_args()
    main()
