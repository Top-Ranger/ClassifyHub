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

import logging
import argparse
import sys


##
# \brief Curent configuration .
#
# Information stored as a python dict.
_CONGIF = {
    'model_path': './models',
    'cache_path': './cache',
    'maximum_cache_age': 7,
    'force_cache_update': False,
    'secret_file': './secret',
    'user_file': './user',
    'number_worker': 0,
    'input': './data/input.txt',
    'output': './data/output.txt',
    'learning_input': './data/learning/',
    'k-fold': 10,
}


##
# \brief Returns the the configuration.
#
# \return Dictionary {KEY:VALUE}, where KEY is a string and VALUE can be of different types. The config is a copy, to
#         change the values globally use the configserver.set() method
def get_config():
    return _CONGIF.copy()


##
# \brief Returns the value for a given configuration key.
#
# \param key Key as a string.
# \return Value of the configuration entry. Can be of arbitrary type.
def get(key):
    if key in _CONGIF:
        return _CONGIF[key]
    else:
        logging.warning('Asking for non-existing key %s' % key)
        return ''


##
# \brief Sets the value for a given configuration key.
#
# \param key Key as a string.
# \param value Value of the configuration entry. Can be of arbitrary type, however it should be of the same type as the
#              original value.
def set(key, value):
    if key not in _CONGIF:
        logging.debug('Adding new config key: {}'.format(key))
    elif type(_CONGIF[key]) is not type(value):
        logging.warning('Assigning new type to {} ({} changed to {}'.format(key, type(_CONGIF[key]), type(value)))
    _CONGIF[key] = value


##
# \brief Parses command line arguments.
#
# Parses command line arguments and stores the result in the global config. Sets up the correct output configuration
# based on the command line arguments.
def parse_args():
    parser = argparse.ArgumentParser(description='ClassifyHub')

    parser.add_argument('-m', '--model-path', dest='model_path', help='Path to the folder containing the trained models. Will be created during the learning process if non existing. Default: {}'.format(_CONGIF['model_path']), type=str)
    parser.add_argument('-c', '--cache-path', dest='cache_path', help='Path to the folder containing the download cache. Will be created if non existing. Default: {}'.format(_CONGIF['cache_path']), type=str)
    parser.add_argument('-a', '--maximum-cache-age', dest='maximum_cache_age', help='Maximum age of cache files. Default: {}'.format(_CONGIF['maximum_cache_age']), type=int)
    parser.add_argument('-f', '--force-cache-update', dest='force_cache_update', help='Force cache update. Default: {}'.format(_CONGIF['force_cache_update']), action='store_true')
    parser.add_argument('-s', '--secret-file', dest='secret_file', help='Path to secret file. The file should only contain the GitHub API key. Default: {}'.format(_CONGIF['secret_file']), type=str)
    parser.add_argument('-u', '--user-file', dest='user_file', help='Path to user file. The file should only contain the GitHub user name used for API interaction. Default: {}'.format(_CONGIF['user_file']), type=str)
    parser.add_argument('-w', '--worker', dest='number_worker', help='Number of worker processes used. If set to 0 it will use a number of processes equal to the number of CPU cores. Default: {}'.format(_CONGIF['number_worker']), type=int)
    parser.add_argument('-i', '--input-file', dest='input', help='Path to input file for batch processing. Must contain multiple lines of single GitHub repository URLs. Default: {}'.format(_CONGIF['input']), type=str)
    parser.add_argument('-o', '--output-file', dest='output', help='Path to output file for batch processing and validation. The file will contain multiple lines of single GitHub repository URLs followed by the computed class. Default: {}'.format(_CONGIF['output']), type=str)
    parser.add_argument('-l', '--learning-dir', dest='learning_input', help='Path to learning directory. The directory must contain one file for each category containing multiple lines of single GitHub repository URLs. Default: {}'.format(_CONGIF['learning_input']), type=str)
    parser.add_argument('-k', '--k-fold', dest='k_fold', help='k parameter for k-fold cross-validation. Default: {}'.format(_CONGIF['k-fold']), type=int)
    parser.add_argument('-d', '--debug', dest='debug', help='Enable debug output. Default: False', action='store_true')

    args = parser.parse_args()

    if args.model_path:
        _CONGIF['model_path'] = args.model_path
    if args.cache_path:
        _CONGIF['cache_path'] = args.cache_path
    if args.maximum_cache_age:
        _CONGIF['maximum_cache_age'] = args.maximum_cache_age
    if args.secret_file:
        _CONGIF['secret_file'] = args.secret_file
    if args.user_file:
        _CONGIF['user_file'] = args.user_file
    if args.number_worker:
        _CONGIF['number_worker'] = args.number_worker
    if args.input:
        _CONGIF['input'] = args.input
    if args.output:
        _CONGIF['output'] = args.output
    if args.learning_input:
        _CONGIF['learning_input'] = args.learning_input
    if args.k_fold:
        _CONGIF['k-fold'] = args.k_fold

    _CONGIF['force_cache_update'] = args.force_cache_update

    _setup_logging(args.debug)


##
# \brief Class to filter log messages.
#
# This class will filter all messages which are in the 'OUTPUT' log level. It is intended to be used with the logging
# module as a filter for a handle.
class _OutputFilter:
    ##
    # \brief Constructor.
    #
    # \param output_only If True only OUTPUT will be logged, if FALSE only OUTPUT will be ignored.
    def __init__(self, output_only=True):
        self._level = output_log_level()
        self._output_only = output_only

    ##
    # \brief Filter method.
    #
    # \param record logging.LogRecord object.
    # \return True if message should be logged (based on constructor argument).
    def filter(self, record):
        return (record.levelno is self._level) == self._output_only


##
# \brief Controls the logging.
#
# This is called automatically during parse_args, so there is no need for manual call.
def _setup_logging(debug=False):
    # logging configuration
    logging.addLevelName(output_log_level(), 'OUTPUT')
    logging.basicConfig(format=str(), level=logging.DEBUG)

    # remove all handlers
    handlers = logging.getLogger().handlers
    for handle in handlers:
        logging.getLogger().removeHandler(handle)

    # basic (error logging) setup
    log_level = logging.WARNING
    if debug:
        log_level = logging.DEBUG

    handle = logging.StreamHandler(stream=sys.stderr)
    handle.setLevel(log_level)
    handle.addFilter(_OutputFilter(False))
    handle.setFormatter(logging.Formatter('%(asctime)s %(levelname)s at %(funcName)s (%(module)s: %(lineno)d): %(message)s'))
    logging.getLogger().addHandler(handle)

    # add output logger
    handle = logging.StreamHandler(stream=sys.stdout)
    handle.setLevel(output_log_level())
    handle.addFilter(_OutputFilter(True))
    handle.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(handle)


##
# \brief Returns the information level for the self defined OUTPUT log level.
#
# \return Gives int according to the logging level.
def output_log_level():
    return logging.INFO + 5
