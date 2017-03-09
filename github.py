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
import os
import logging
import json
import datetime
import requests
import requests.exceptions
import lockfile
import base64
import utility


##
# \brief Error which is raised when an GitHub request fails.
class GithubError(IOError):
    pass


##
# \brief Error is raised when no connection to GitHub is possible.
class GithubConnectionError(GithubError):
    pass


##
# \brief Handles communication with GitHub via GitHub API.
#
# All requests are cached to the permanent memory for later usage.
# All methods of this class can be used on different processes simultaneously - the class uses internal locking (through
# lock files) to assure consistency and avoid multiple calls to the same API.
#
# The number of GitHub requests is limited, especially when unauthentificated
# (see https://developer.github.com/v3/rate_limit/). It is therefore adviced to provide a username / access token
# through the user file / secret file.
class Github:
    ##
    # \brief Constructor.
    #
    # \param dev String containing the name of the developer.
    # \param repo String containing the name of the repository.
    def __init__(self, dev, repo):
        self._dev = dev
        self._repo = repo
        self._path = configserver.get('cache_path') + '/' + self._dev + '/' + self._repo + '/'
        self._cache_time = dict()
        self._github_secret = GithubSecret()

        if not os.path.isdir(self._path):
            try:
                os.makedirs(self._path)
            except OSError:
                logging.error('Can not create cache directory {}'.format(self._path))

    ##
    # \brief Equality operator.
    #
    # Two objects are compared. They are considered as equal if they have the same developer and repository.
    #
    # \param other github.Github object.
    #
    # \return True if objects are equal.
    def __eq__(self, other):
        if not isinstance(other, Github):
            return False
        return self._dev == other._dev and self._repo == other._repo

    ##
    # \brief Reads metadata cache from permanent memory.
    #
    # Reads cache metadata from the "METADATA" file in the cache directory .
    def _read_metadata(self):
        lock = lockfile.LockFile(self._path + 'METADATA_LOCK')
        with lock:
            if os.path.exists(self._path + 'METADATA'):
                with open(self._path + 'METADATA', 'r') as file:
                    try:
                        self._cache_time = json.load(file)
                    except:
                        logging.error('Can not load metadata of {} / {}'.format(self._dev, self._repo))
                        self._cache_time = dict()

    ##
    # \brief Saves metadata cache to permanent memory.
    #
    # Saves cache metadata to the "METADATA" file in the cache directory.
    def _save_metadata(self):
        lock = lockfile.LockFile(self._path + 'METADATA_LOCK')
        with lock:
            with open(self._path + 'METADATA', 'w') as file:
                try:
                    json.dump(self._cache_time, file)
                except:
                    logging.error('Can not save metadata of {} / {}'.format(self._dev, self._repo))

    ##
    # \brief Tests if cache data is valid or has to be updated.
    #
    # Data has to be updated if:
    # * data is outdated
    # * data does not exists
    # * data update is forced
    #
    # \return True if data is valid. False if data needs to be updated.
    def _test_cache_valid(self, data_key):
        self._read_metadata()
        age = abs(datetime.date.today().toordinal() - self._cache_time[data_key]) if data_key in self._cache_time else configserver.get('maximum_cache_age') + 1
        returnvalue = (
            (os.path.exists(self._path + data_key) or os.path.exists(self._path + data_key + '_ERROR_GITHUB'))
            and not configserver.get('force_cache_update')
            and age < configserver.get('maximum_cache_age')
        )
        return returnvalue

    ##
    # \brief Gets the API data.
    #
    # The data is read from the API cache if the cache is still valid, otherwise it will be fetched from GitHub.
    # Raises an error if the GitHub requests fails. GitHub API errors are cached like normal data.
    #
    # \param data_key String containing the cache key.
    # \param get_url String containing the url for the API request.
    #
    # \exception github.GithubError raised if requests fails.
    #
    # \return API data
    def _get_data(self, data_key, get_url):
        # Check metadata lock here once - no need to check it somewhere else
        utility.check_stale_lock(self._path + 'METADATA_LOCK')
        utility.check_stale_lock(self._path + data_key + '_GET_DATA_LOCK')

        metadata_lock = lockfile.LockFile(self._path + 'METADATA_LOCK')
        dl_lock = lockfile.LockFile(self._path + data_key + '_GET_DATA_LOCK')
        with dl_lock:
            if self._test_cache_valid(data_key):
                # Test for cached error
                if os.path.exists(self._path + data_key + '_ERROR_GITHUB'):
                    logging.debug('Cached github error at {} / {}'.format(self._dev, self._repo))
                    raise GithubError

                # Load data
                try:
                    with open(self._path + data_key, 'r') as file:
                        data = json.load(file)
                        return data
                except:
                    logging.warning('Can not load data "{}" from {} / {} - downloading it'.format(data_key, self._dev, self._repo))

            # Update cache
            if os.path.exists(self._path + data_key + '_ERROR_GITHUB'):
                try:
                    os.remove(self._path + data_key + '_ERROR_GITHUB')
                except IOError:
                    logging.debug('Error removing {}'.format(self._path + data_key + '_ERROR_GITHUB'))

            try:
                if self._github_secret.secret_available:
                    r = requests.get(get_url, auth=(self._github_secret.user, self._github_secret.secret))
                else:
                    logging.warning('Using unuthenticated request - this will limit you to only few requests per hour. Please consider using Authenticated requests.')
                    r = requests.get(get_url)
            except Exception as e:
                logging.error('Can not connect to GitHub API. Please check your internet connection.\n Following error occurred: {}'.format(e))
                raise GithubError

            if r.status_code != 200:
                logging.debug('Bad status code {} returned ({} / {})'.format(r.status_code, self._dev, self._repo))
                logging.debug('Request: "{}" - Key: "{}"'.format(get_url, data_key))
                data = r.json()
                if 'message' in data:
                    logging.debug('Message: {}'.format(r.json()['message']))
                    if 'API rate limit exceeded' in data['message']:
                        logging.error('API rate limit exceeded - no further requests are currently possible. Please see https://developer.github.com/v3/#rate-limiting')
                        raise GithubError
                with metadata_lock:
                    with open(self._path + data_key + '_ERROR_GITHUB', 'w'):
                        pass
                self._cache_time[data_key] = datetime.date.today().toordinal()
                self._save_metadata()
                raise GithubError

            data = r.json()

            try:
                with metadata_lock:
                    with open(self._path + data_key, 'w') as file:
                        json.dump(data, file)
                        self._cache_time[data_key] = datetime.date.today().toordinal()
                self._save_metadata()
            except:
                logging.warning('Can not save data "{}" of {} / {} to cache'.format(data_key, self._dev, self._repo))

            return data

    ##
    # \brief Gets the repository metadata.
    #
    # \return Repository metadata of this repository as deserialised JSON.
    def get_repository_data(self):
        url = 'https://api.github.com/repos/' + self._dev + '/' + self._repo
        return self._get_data('repository_data', url)

    ##
    # \brief Tests if repository exists.
    #
    # \return Returns if the tested repository exists.
    def repository_exists(self):
        try:
            data = self.get_repository_data()
            return not ('message' in data and data['message'] == 'Not Found')
        except GithubError:
            return False

    ##
    # \brief Gets the content of the repository.
    #
    # \param path String containing target path.
    #
    # \return Repository content as deserialised JSON.
    def get_repository_content(self, path=''):
        url = 'https://api.github.com/repos/' + self._dev + '/' + self._repo + '/contents/' + path
        data_key = 'repository_content_' + path
        data_key = data_key.replace('/', '__dir__')
        return self._get_data(data_key, url)

    ##
    # \brief Gets the git tree of the repository.
    #
    # \param branch String containing target branch. If empty the default branch of the repository will be used.
    #
    # \return Returns git tree of the repository as deserialised JSON.
    def get_tree(self, branch=''):
        if branch == '':
            branch = self.get_repository_data()['default_branch']
        url = 'https://api.github.com/repos/{}/{}/git/trees/{}?recursive=1'.format(self._dev, self._repo, branch)
        data_key = 'tree_' + branch
        data_key = data_key.replace('/', '_SLASH_')
        return self._get_data(data_key, url)

    ##
    # \brief Gets all files in the git tree.
    #
    # \return Returns all files in the git tree as list.
    def get_all_files(self):
        tree = self.get_tree()
        files = []
        for element in tree['tree']:
            if element['type'] == 'tree' or element['type'] == 'commit':
                continue
            elif element['type'] == 'blob':
                files += [element['path'].split('/')[-1]]
            else:
                logging.warning('Unknown tree element {} found for {} / {} - "{}"'.format(element['type'], self._dev, self._repo, element['path']))
        return files

    ##
    # \brief Produces the url of the repository with the name of the developer and the name of the repository.
    #
    # \return Returns the url of the repository as string.
    def get_repo_url(self):
        return 'https://github.com/{}/{}'.format(self._dev, self._repo)

    ##
    # \brief Gets the readme of a repository.
    #
    # \return If there is no readme available an empty string will be returned. Otherwise the readme will be returned.
    def get_readme(self):
        url = 'https://api.github.com/repos/{}/{}/readme'.format(self._dev, self._repo)
        data_key = 'readme'
        data = self._get_data(data_key, url)
        if 'message' in data and data['message'] == 'Not Found':
            logging.debug('Repository {} / {} does not seem to have a readme'.format(self._dev, self._repo))
            return ''
        content = data['content']
        if data['encoding'] == 'base64':
            return base64.b64decode(content)
        else:
            logging.debug('Unknown encoding of readme at {} / {}: {}'.format(self._dev, self._repo, data['encoding']))

    ##
    # \brief Gets a specific file from the repository.
    #
    # \param file String containing path to target file.
    #
    # \return If the specific file is not a file an empty string will be returned otherwise the file will be returned.
    def get_file(self, file):
        data = self.get_repository_content(file)
        if isinstance(data, list):
            logging.debug('{} ({} / {}) is not a file'.format(file, self._dev, self._repo))
            return ''
        if 'message' in data and data['message'] == 'Not Found':
            logging.debug('Repository {} / {} does not seem to have a readme'.format(self._dev, self._repo))
            return ''
        if data['type'] != 'file':
            logging.debug('{} ({} / {}) is not a file'.format(file, self._dev, self._repo))
            return ''
        content = data['content']
        if data['encoding'] == 'base64':
            return base64.b64decode(content)
        else:
            logging.debug('Unknown encoding of file "{}" at {} / {}: {}'.format(file, self._dev, self._repo, data['encoding']))

    ##
    # \brief Gets the programming language.
    #
    # Returns the distribution of programming languages as reported by GitHub.
    #
    # \return Returns the language of the repository as deserialised JSON.
    def get_languages(self):
        url = 'https://api.github.com/repos/{}/{}/languages'.format(self._dev, self._repo)
        data_key = 'languages'
        return self._get_data(data_key, url)

    ##
    # \brief Gets all commits in the repository.
    #
    # \return Returns all commits with their comments of the repository as deserialised JSON.
    def get_commits(self):
        url = 'https://api.github.com/repos/{}/{}/commits'.format(self._dev, self._repo)
        data_key = 'commits'
        return self._get_data(data_key, url)

    ##
    # \brief Returns the developer and repository of the object.
    #
    # \return Tupel (DEV, REPO), where DEV/REPO are the developer / repository as strings.
    def get_dev_repo(self):
        return self._dev, self._repo


##
# \brief Holds the user credentials to access GitHub through authentificated access.
#
# This is needed e.g. to get a higher rate limit. You can access the user name / access token through the
# GithubSecret.user / GithubSecret.secret attribute if GithubSecret.secret_available is True.
class GithubSecret:
    ##
    # \fn __init__(self)
    # \brief Constructor.
    #
    # Reads the secret and user file if existing and sets all member variables accordingly.
    def __init__(self):
        ##
        # \var secret_available
        # \brief Set to true if authentification data is available.
        self.secret_available = False

        ##
        # \var secret
        # \brief Authentification token.
        self.secret = ''

        ##
        # \var user
        # \brief User name for authentification.
        self.user = ''

        if os.path.exists(configserver.get('user_file')) and os.path.exists(configserver.get('secret_file')):
            try:
                with open(configserver.get('user_file'), 'r') as file:
                    self.user = file.read().strip()
                with open(configserver.get('secret_file'), 'r') as file:
                    self.secret = file.read().strip()
                self.secret_available = self.user != '' and self.secret != ''
            except:
                logging.warning('Can not read user/secret file - running in anonymous modus')
