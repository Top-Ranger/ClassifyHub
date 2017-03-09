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

import re
import lockfile
import logging
import random
import configserver
import multiprocessing

##
# \brief Regular expression used for URL validation and developer / repository extraction.
_URL_RE = re.compile('^(http(s)?://)?(www.)?github.com/(?P<dev>[a-zA-Z0-9\-_\.]*)/(?P<repo>[a-zA-Z0-9\-_\.]*)(?!\.git)/?$')


##
# \brief Validates if the given url exists.
#
# \return Returns if the given url exists.
def validate_url(url):
    url = url.strip()
    return _URL_RE.match(url) is not None


##
# \brief Extracts the developer and the repository from the given url.
#
# \return Returns the developer and the repository as tupel of strings ('dev','repo').
def get_dev_and_repo(url):
    url = url.strip()
    match = _URL_RE.match(url)
    if match is None:
        return '', ''
    return match.group('dev'), match.group('repo')


##
# \brief Defines the classes the repositorys are got to be assigned to.
#
# \return Returns a list of strings with all classes.
def get_classes():
    return ['DEV', 'HW', 'EDU', 'DOCS', 'WEB', 'DATA', 'OTHER']


##
# \brief Creates a dict with all classes as keys and zeros as values.
#
# \return Returns a dict with all classes as keys and zeros as values.
def get_zero_class_dict():
    return {'DEV': 0,
            'HW': 0,
            'EDU': 0,
            'DOCS': 0,
            'WEB': 0,
            'DATA': 0,
            'OTHER': 0,
            }


##
# \brief Searches the given dict for the highes value.
#
# \return Returns the highes value as string.
def get_best_class(dict):
    best = -1
    best_class = ''

    for result_class in dict.keys():
        if dict[result_class] > best:
            best = dict[result_class]
            best_class = result_class

    return best_class


##
# \brief Checks for stale lock file and removes it.
#
# A lock file is considered stale if the file is not removed X (default: 20) seconds.
# Since nothing should take longer than 20 seconds (including a single download) this should hopefully be safe.
#
# \param lock_path Path of lockfile to check. Should be the same you give to lockfile.LockFile
# \param time Time to check. The longer the time, the longer are also the waiting times
def check_stale_lock(lock_path, time=20):
    worker = multiprocessing.cpu_count()
    if configserver.get('number_worker') > 0:
        worker = configserver.get('number_worker')

    lock = lockfile.LockFile(lock_path)
    test_lock = lockfile.LockFile(lock_path + '_STALE')
    while not test_lock.i_am_locking():
        try:
            try:
                # Because this is longer then the lock timeout, we are sure that this is stale
                test_lock.acquire(timeout=time + time / 5 * worker + (time / 2) * random.random())
            except lockfile.LockTimeout:
                test_lock.break_lock()
        except Exception as e:
            logging.debug('Error at locking stale test log: {}'.format(e))
            pass

    try:
        lock.acquire(timeout=time)
        lock.release()
    except lockfile.LockTimeout:
        logging.debug('Breaking log {}'.format(lock_path))
        try:
            lock.break_lock()
        except lockfile.NotLocked:
            pass

    try:
        test_lock.release()
    except lockfile.NotLocked:
        # Someone broke it - not bad
        pass


##
# \brief Calculates the 'Levenshtein distance' between two given strings.
#
# \return Returns the distances between the two given strings as int.
def edit_distance(target, source, cost_ins=1, cost_del=1, cost_sub=1):
    # Default is 'Levenshtein distance'
    n = len(target)
    m = len(source)
    matrix = [[0 for __ in range(m + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        matrix[i][0] = matrix[i - 1][0] + cost_ins

    for j in range(1, m + 1):
        matrix[0][j] = matrix[0][j - 1] + cost_del

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            matrix[i][j] = min(matrix[i - 1][j] + cost_ins, matrix[i - 1][j - 1] + (0 if source[j - 1] is target[i - 1] else cost_sub), matrix[i][j - 1] + cost_del)

    return matrix[n][m]
