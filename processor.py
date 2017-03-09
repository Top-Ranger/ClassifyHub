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

import multiprocessing
import logging
import os
import utility
import github
import configserver
import queue
import sys
import classifier


##
# \brief Batch worker for parallel processing.
#
# \param queue_input multiprocessing.Queue containing github.Github objects for classification.
# \param queue_output multiprocessing.Queue where output is pushed into as (LABEL, GITHUB, COMBINED_DICT, DETAILED_DICT)
#                     tupel, where LABEL is a string containing the label, GITHUB is the classified repository as a
#                     github.Github object, COMBINED_DICT is a dict containing the combined prediction of all
#                     classifier as a dict {CLASS: PROBABILITY} and DETAILED_DICT contains the output of the single
#                     classifiers as a dict {NAME: {CLASS: PROBABILITY}}.
def _batch_worker(queue_input, queue_output):
    classifiers = classifier.get_all_classifiers()
    try:
        while True:
            data = queue_input.get(True, 1)
            sum_results = utility.get_zero_class_dict()
            classifier_results = dict()
            for c in classifiers:
                result = c.classify(data)
                classifier_results[c.name()] = result
                for key in sum_results.keys():
                    if key in result:
                        sum_results[key] += result[key] / len(classifiers)
            queue_output.put((data, utility.get_best_class(sum_results), sum_results, classifier_results))
    except queue.Empty:
        sys.exit(0)


##
# \brief Learning worker for parallel processing.
#
# \param input List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
#              CLASS is the class label of the repository as a string.
# \param queue_classifier multiprocessing.Queue containing classifier objects for learning.
def _learning_worker(input, queue_classifier):
    try:
        while True:
            c = queue_classifier.get(True, 1)
            c.learn(input)
    except queue.Empty:
        sys.exit(0)


##
# \brief Parses a file and returns an array which can be used for batch processing.
#
# \param path Path of the file to parse.
# \return List containing github.Github objects corresponding to the input file.
def file_to_input(path):
    if not os.path.exists(path):
        logging.warning('Can not convert {}: file not existing'.format(path))
        return []

    data = []
    try:
        with open(path, 'r') as file:
            for line in file:
                line = line.strip()
                if line == '':
                    continue
                elif not utility.validate_url(line):
                    logging.warning('Line "{}" is not a valid url - skipping'.format(line))
                else:
                    url_data = utility.get_dev_and_repo(line)
                    data += [github.Github(url_data[0], url_data[1])]
    except:
        logging.error('Error while converting file {}'.format(path))

    return data


##
# Saves the processing results to a file.
#
# \param result List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
#               CLASS is the class label of the repository as a string.
# \param filename Target file path.
def result_to_file(result, filename):
    try:
        with open(filename, 'w') as file:
            for r in result:
                file.write('{} {}\n'.format(r[0].get_repo_url(), r[1]))
    except:
        logging.error('Can not save results to {}'.format(filename))


##
# \brief Parsed the files in a directory and returns input for learning.
#
# The directory has to contain one file with the name of each class ('DEV', 'HW', 'EDU', 'DOCS', 'WEB', 'DATA', 'OTHER')
# containing lines with repositories of that class.
#
# \param path Path to directory.
# \return List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
#         CLASS is the class label of the repository as a string.
def dir_to_learning(path):
    if not os.path.isdir(path):
        logging.warning('Can not convert {}: not a directory'.format(path))
        return []

    classes = utility.get_classes()

    for file in classes:
        if not os.path.exists(path + '/' + file):
            logging.warning('Can not convert {}: file {} not existing'.format(path, path + '/' + file))
            return []

    input = []

    for file in classes:
        dataset = file_to_input(path + '/' + file)
        for data in dataset:
            input += [(data, file)]

    return input


##
# \brief Runs the batch processing.
#
# Before running the batch processing (as well as after a scikit-learn upgrade) you first must run the learning function
# (not necessary in the same program).
#
# The batch processing is done in parallel.
# The parameters for the processing are taking from the global configuration.
#
# \param input List containing github.Github objects for classification.
# \return List containing Tupel (LABEL, GITHUB, COMBINED_DICT), where LABEL is the computed label
#              and GITHUB is the repository as a github.Github class, COMBINED_DICT is a dict containing the
#              combined prediction of all classifier as a dict {CLASS: PROBABILITY} and DETAILED_DICT contains the
#              output of the single classifiers as a dict {NAME: {CLASS: PROBABILITY}}.
def batch(input):
    if len(input) == 0:
        return []

    worker = multiprocessing.cpu_count()
    if configserver.get('number_worker') > 0:
        worker = configserver.get('number_worker')

    queue_input = multiprocessing.Queue()
    queue_output = multiprocessing.Queue()

    for data in input:
        queue_input.put_nowait(data)

    processes = []
    failed = []

    for i in range(worker):
        processes += [multiprocessing.Process(target=_batch_worker, args=(queue_input, queue_output))]

    for process in processes:
        process.start()

    result = []
    alive = True

    # We have to pull all elements out of the queue or else the process might not terminate
    # See https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
    while alive:
        try:
            while True:
                result += [queue_output.get(True, 1)]
        except queue.Empty:
            pass

        alive = False
        for process in processes:
            if process.is_alive():
                alive = True
                break

    for process in processes:
        process.join()
        if not process.exitcode == 0:
            failed += [process]

    if len(failed) > 0:
        logging.error('{} processes have failed - result might not be complete'.format(len(failed)))

    # Try again just in case we missed some elements
    try:
        while True:
            result += [queue_output.get(True, 1)]
    except queue.Empty:
        pass

    if len(result) != len(input):
        logging.error('Expected {} results, got {} - some results are missing'.format(len(input), len(result)))

    return result


##
# \brief Runs the learning process.
#
# The results are stored to permanent memory and can be used later.
#
# \param input List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
#              CLASS is the class label of the repository as a string.
def learning(input):
    worker = multiprocessing.cpu_count()
    if configserver.get('number_worker') > 0:
        worker = configserver.get('number_worker')

    queue_classifier = multiprocessing.Queue()

    for c in classifier.get_all_classifiers():
        queue_classifier.put_nowait(c)

    processes = []
    failed = []

    for i in range(worker):
        processes += [multiprocessing.Process(target=_learning_worker, args=(input, queue_classifier))]

    for process in processes:
        process.start()

    for process in processes:
        process.join()
        if not process.exitcode == 0:
            failed += [process]

    if len(failed) > 0:
        logging.error('{} processes have failed - result might not be complete'.format(len(failed)))
