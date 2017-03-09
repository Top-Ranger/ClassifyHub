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
import random
import utility


##
# \brief Calculates the precision for a given class.
#
# \param truth The truth data in the form of (GITHUB, CLASS), where GITHUB is the repository as a github.Github class
#              and CLASS is the class label of the repository as a string.
# \param results The truth data in the form of (GITHUB, CLASS), where GITHUB is the repository as a github.Github class
#                and CLASS is the class label of the repository as a string.
# \param target_class The target class for which the precision should be computed as string.
# \return Precision as float.
def calculate_precision(truth, results, target_class):
    count = 0
    tp = 0

    for data in results:
        if data[1] == target_class:
            count += 1
            for t in truth:
                if t[0] == data[0]:
                    if t[1] == target_class:
                        tp += 1
                    break

    if count != 0:
        return tp / count
    else:
        logging.warning('Precision: No tp/fp found (class: %s) - maybe dataset too small?' % target_class)
        return 0.0


##
# \brief Calculates the recall for a given class.
#
# \param truth The truth data in the form of (GITHUB, CLASS), where GITHUB is the repository as a github.Github class
#              and CLASS is the class label of the repository as a string.
# \param results The truth data in the form of (GITHUB, CLASS), where GITHUB is the repository as a github.Github class
#                and CLASS is the class label of the repository as a string.
# \param target_class The target class for which the recall should be computed as string.
# \return Recall as float.
def calculate_recall(truth, results, target_class):
    count = 0
    tp = 0

    for data in truth:
        if data[1] == target_class:
            count += 1
            for r in results:
                if r[0] == data[0]:
                    if r[1] == target_class:
                        tp += 1
                    break

    if count != 0:
        return tp / count
    else:
        logging.warning('Recall: No tp/fn found (class: %s) - maybe dataset too small?' % target_class)
        return 0.0


##
# \brief Starts the validation process.
#
# The validation process runs a k-fold cross-validation and outputs the results in the 'OUTPUT' logger level as well
# as in the output file.
def main():
    # Open Output file
    file = None
    try:
        file = open(configserver.get('output'), 'w')
    except OSError:
        logging.error('Can not save results to {}'.format(configserver.get('output')))

    # Prepare data
    data = processor.dir_to_learning(configserver.get('learning_input'))
    if len(data) == 0:
        logging.error('No learning data - aborting')
        return

    k_fold = configserver.get('k-fold')

    if k_fold < 2:
        logging.error('k-cross must be at least 2 (is: {})'.format(k_fold))
        return

    logging.log(configserver.output_log_level(), 'Starting validation ({}-cross validation)'.format(k_fold))
    logging.log(configserver.output_log_level(), 'Depending on your system, the size of learning/validation data and the amount that needs to be downloaded this might take a while. Please wait.')
    if file is not None:
        file.write('Starting validation ({}-cross validation)\n'.format(k_fold))
        file.flush()

    datasets = [[] for i in range(k_fold)]

    for d in data:
        datasets[random.randint(0, k_fold - 1)] += [d]

    # Run k-fold cross-validation
    precision = utility.get_zero_class_dict()
    recall = utility.get_zero_class_dict()

    for run in range(k_fold):
        logging.log(configserver.output_log_level(), 'Starting validation run {}'.format(run + 1))
        if file is not None:
            file.write('Starting validation run {}\n'.format(run + 1))
            file.flush()

        learn = []
        truth = []

        # Create datasets for run
        for i in range(k_fold):
            if i == run:
                truth = datasets[i]
            else:
                learn += datasets[i]

        # Remove labels
        validate = [x[0] for x in truth]

        # Learn
        processor.learning(learn)

        # Calculate validation data set
        result = processor.batch(validate)

        # Cache results of this run
        for c in utility.get_classes():
            precision_result = calculate_precision(truth, result, c)
            recall_result = calculate_recall(truth, result, c)

            if file is not None:
                file.write('{:6} - precision: {:6.4f}, recall: {:6.4f}\n'.format(c, precision_result, recall_result))

            precision[c] += precision_result
            recall[c] += recall_result

        if file is not None:
            file.write('\n')
            file.flush()

    # Calculate average
    for c in utility.get_classes():
        precision[c] /= k_fold
        recall[c] /= k_fold

    # Print results
    logging.log(configserver.output_log_level(), 'Average results from {}-fold cross-validation:'.format(k_fold))
    precision_avg = 0.0
    recall_avg = 0.0
    if file is not None:
        file.write('Average results from {}-fold cross-validation:\n'.format(k_fold))
    for c in utility.get_classes():
        precision_avg += precision[c]
        recall_avg += recall[c]
        logging.log(configserver.output_log_level(), '{:6} - precision: {:6.4f}, recall: {:6.4f}'.format(c, precision[c], recall[c]))
        if file is not None:
            file.write('{:6} - precision: {:6.4f}, recall: {:6.4f}\n'.format(c, precision[c], recall[c]))

    precision_avg /= len(utility.get_classes())
    recall_avg /= len(utility.get_classes())
    logging.log(configserver.output_log_level(), '{:6} - precision: {:6.4f}, recall: {:6.4f}'.format('ALL', precision_avg, recall_avg))

    # Close file if open
    if file is not None:
        file.write('{:6} - precision: {:6.4f}, recall: {:6.4f}\n'.format('ALL', precision_avg, recall_avg))
        file.write('\n')
        file.close()


if __name__ == '__main__':
    configserver.parse_args()
    main()
