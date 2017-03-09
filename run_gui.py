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

import sys
import os
import threading
import traceback
import requests
import random

from PyQt5.QtCore import QObject, QUrl, QSettings, QVariant
from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal
from PyQt5.QtQml import qmlRegisterType, QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog

import github
import utility
import processor
import classifier
import configserver


##
# \brief Holds whether learning is neaded
_learning_needed = False


##
# \brief Tests if user/secret file is setup correctly.
#
# If not an error message will be shown.
def check_user_and_secret():
    github_secret = github.GithubSecret()

    if not github_secret.secret_available:
        QMessageBox.warning(None, 'No authentification possible',
                            'Authentificated requests are not possible - this will limit you to only a few GitHub requests per hour. '
                            'Please ensure that the user file ({}) and the secret file ({}) exist in your setup. '
                            'The file names must match exactly, including the file extension, which is not visible on all systems.'.format(
                                configserver.get('user_file'), configserver.get('secret_file')))


##
# \brief Class for communication between UI and algorithm.
#
# This class is responsible for the communication between the algorithm and the UI (written in QML).
# All classes decleared as Qt slots are callable from QML. Only one instance of the class should be used.
class UIProxy(QObject):
    ##
    # \brief Signal emitted when new results are ready.
    resultReady = pyqtSignal()

    ##
    # \brief Signal emitted when the availability of saving changes.
    saveReadyChanged = pyqtSignal(bool)

    ##
    # \brief Signal emitted when computation is running.
    runningChanged = pyqtSignal(bool)

    ##
    # \brief Signal emitted when the learning process is running.
    learningRunningChanged = pyqtSignal(bool, arguments=['value'])

    ##
    # \brief Signal emitted when new rate limit arrives
    rateLimit = pyqtSignal(int, arguments=['limit'])

    ##
    # \brief Constructor.
    #
    # \param parent QObject parent.
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._thread = None
        self._save_ready = False
        self._cache = None
        self._running = False
        self._learning_running = False
        self._classifier_names = [c.name() for c in classifier.get_all_classifiers()]

    ##
    # \brief Sets the cache to the provided entry.
    #
    # If the entry is not found, the result will be set zu None.
    #
    # \param github github.Github class representing the target repository.
    def _update_cache(self, github):
        if self._cache is not None and github == self._cache[0]:
            return

        for result in self._results:
            if result[0] == github:
                self._cache = result
                return

        self._cache = None

    ##
    # \brief Starts the computation process.
    #
    # Computation will run in a background thread to have a responsive UI.
    # Ones computation has finished 'resultReady' will be emitted.
    #
    # \param data String containing repositories to classify (divided by new lines).
    @pyqtSlot(str)
    def start_computation(self, data):
        if self._running:
            return

        if not self.test_valid_input(data):
            self._results = []
            self.resultReady()
            return
        self._running = True
        self.runningChanged.emit(True)
        self._save_ready = False
        self.saveReadyChanged.emit(False)
        self._thread = threading.Thread(target=self._computation_handle, args=(data,))
        self._thread.start()

    ###
    # \brief Starts the learning process.
    #
    # Computation will run in a background thread to have a responsive UI.
    @pyqtSlot()
    def start_learning(self):
        self._running = True
        self.runningChanged.emit(True)
        self._learning_running = True
        self.learningRunningChanged.emit(True)
        self._thread = threading.Thread(target=self._learning_handle)
        self._thread.start()

    ##
    # \brief Tests if the input is valid.
    #
    # An input is valid if each line is a link to a repository.
    #
    # \param data Input data to validate as string.
    # \return True if data is valid.
    @pyqtSlot(str, result=bool)
    def test_valid_input(self, data):
        for line in data.split('\n'):
            if line == '':
                continue
            if not utility.validate_url(line):
                return False
        return True

    ##
    # \brief Helper function to handle actual computation.
    #
    # This function is intended to be used in a thread to make the GUI responsive.
    # This signal will emit resultReady when the computation has finished.
    #
    # \param input Input data as string.
    def _computation_handle(self, data):
        computation_input = []

        for line in data.split('\n'):
            if line == '':
                continue
            if utility.validate_url(line):
                dev, repo = utility.get_dev_and_repo(line)
                computation_input += [github.Github(dev, repo)]

        self._results = processor.batch(computation_input)
        self.saveReadyChanged.emit(True)
        self._save_ready = True
        self._running = False

        self.runningChanged.emit(False)
        self.resultReady.emit()

    ##
    # \brief Helper function to handle actual computation.
    #
    # This function is intended to be used in a thread to make the GUI responsive.
    def _learning_handle(self):
        learning_data = processor.dir_to_learning(configserver.get('learning_input'))
        if len(learning_data) == 0:
            QMessageBox.critical(None, 'No learning data', 'Learning data not found ({}), the application will not work. Please rerun the learning once the configuration was fixed.'.format(configserver.get('learning_input')))
        processor.learning(learning_data)

        self._running = False
        self.runningChanged.emit(False)
        self._learning_running = False
        self.learningRunningChanged.emit(False)

    ##
    # \brief Returns a list of all repositories for which results were calculated.
    #
    # \return List containing strings in 'DEV/REPO' format, where DEV is the developer and REPO the repository.
    @pyqtSlot(result=QVariant)
    def get_result_list(self):
        list = []
        for result in self._results:
            dev, repo = result[0].get_dev_repo()
            list += ['{}/{}'.format(dev, repo)]
        return QVariant(list)

    ##
    # \brief Gets the class of a repository.
    #
    # \param dev Developer as string.
    # \param repo Repository as string.
    # \return String containing computed class.
    @pyqtSlot(str, str, result=str)
    def get_class(self, dev, repo):
        test_github = github.Github(dev, repo)
        self._update_cache(test_github)
        if self._cache is not None:
            return self._cache[1]
        return 'NOT FOUND'

    ##
    # \brief returns the combined probability of a class.
    #
    # \param dev Developer as string.
    # \param repo Repository as string.
    # \param target_class Class as string.
    # \return Combined probability of the class.
    @pyqtSlot(str, str, str, result=float)
    def get_prob(self, dev, repo, target_class):
        test_github = github.Github(dev, repo)
        self._update_cache(test_github)
        if self._cache is not None:
            if target_class in self._cache[2]:
                return self._cache[2][target_class]
            else:
                return 0.0
        return 0.0

    ##
    # \brief returns the name of all classifier.
    #
    # \return List containing names of classifiers as string.
    @pyqtSlot(result=QVariant)
    def get_classifier_names(self):
        return QVariant(self._classifier_names)

    ##
    # \brief returns the probability of a class for a given classifier.
    #
    # \param dev Developer as string.
    # \param repo Repository as string.
    # \param target_class Class as string.
    # \param classifier Classifier as string.
    # \return Probability of the class for the given classifier.
    @pyqtSlot(str, str, str, str, result=float)
    def get_classifier_prob(self, dev, repo, target_class, classifier):
        test_github = github.Github(dev, repo)
        self._update_cache(test_github)
        if self._cache is not None:
            if classifier in self._cache[3] and target_class in self._cache[3][classifier]:
                return self._cache[3][classifier][target_class]
            else:
                return 0.0
        return 0.0

    ##
    # \brief Returns the URL of a repository.
    #
    # \param dev Developer as string.
    # \param repo Repository as string.
    # \return URL of repository as string.
    @pyqtSlot(str, str, result=str)
    def get_url(self, dev, repo):
        test_github = github.Github(dev, repo)
        self._update_cache(test_github)
        if self._cache is not None:
            return self._cache[0].get_repo_url()

        return ''

    ##
    # \brief Saves the results to a file.
    #
    # This function does nothing if saveReadyChanged has not been emitted or has been emitted with False.
    @pyqtSlot()
    def save_results(self):
        if not self._save_ready:
            return

        target = QFileDialog.getSaveFileName(None, 'Save results', './', 'Text (*.txt);All files')[0]
        if target != '':
            processor.result_to_file(self._results, target)

    ##
    # \brief Returns the path of an existing directory
    #
    # If no directory is chosen by the user an empty string will be returned
    #
    # \param title Title of the selection window
    # \return String containing directory or empty string if no directory is chosen
    @pyqtSlot(str, result=str)
    def get_dir_path(self, title):
        return QFileDialog.getExistingDirectory(None, title)

    ##
    # \brief Returns the path of an existing file
    #
    # If no file is chosen by the user an empty string will be returned
    #
    # \param title Title of the selection window
    # \return String containing file path or empty string if no file is chosen
    @pyqtSlot(str, result=str)
    def get_file_path(self, title):
        return QFileDialog.getOpenFileName(None, title)[0]

    ##
    # \brief Qt slot for check_user_and_secret().
    #
    # Tests if user/secret file is setup correctly and shows error message if not.
    @pyqtSlot()
    def check_authentification(self):
        check_user_and_secret()

    ##
    # \brief Checks whether learning is needed.
    #
    # After calling this once (globally) the result will always be False.
    #
    # \return Bool if learning is needed.
    @pyqtSlot(result=bool)
    def check_learning_needed(self):
        global _learning_needed
        learning_needed = _learning_needed
        _learning_needed = False
        return learning_needed

    ##
    # \brief Reads a file and returns the file content.
    #
    # \return File content as string
    @pyqtSlot(result=str)
    def get_file_content(self):
        filename = QFileDialog.getOpenFileName(None, 'Open file')[0]
        if filename is '':
            return ''
        try:
            with open(filename, 'r') as file:
                try:
                    return str(file.read())
                except Exception as e:
                    QMessageBox.warning(None, 'Can not open file', 'Can not open file {}:\n{}'.format(filename, e))
                    return ''
        except IOError:
            return ''

    ##
    # \brief Returns the remaining rate limit
    #
    # Returns -1 if an error occurred. This request do not xount against the rate limit.
    #
    # \return Rate limit or -1 if error occurred
    @pyqtSlot()
    def get_remaining_rate_limit(self):
        thread = threading.Thread(target=self._rate_limit_handle)
        thread.start()

    ##
    # \brief Internal handle for getting rate limit
    #
    # This should make the UI more responsive. Emits rateLimit.
    def _rate_limit_handle(self):
        try:
            github_secret = github.GithubSecret()
            if github_secret.secret_available:
                r = requests.get('https://api.github.com/rate_limit', auth=(github_secret.user, github_secret.secret))
            else:
                r = requests.get('https://api.github.com/rate_limit')

            if r.status_code != 200:
                self.rateLimit.emit(-1)

            data = r.json()
            self.rateLimit.emit(int(data['rate']['remaining']))
        except Exception:
            self.rateLimit.emit(-1)

    ##
    # \brief Returns 5 random repositories.
    #
    # This uses one GitHub API request.
    #
    # \return String containing random repositories.
    @pyqtSlot(result=str)
    def get_random_repositories(self):
        try:
            github_secret = github.GithubSecret()
            get_url = "https://api.github.com/repositories?since={}".format(random.randint(1, 58000000))  # Should be save and huge enough

            if github_secret.secret_available:
                r = requests.get(get_url, auth=(github_secret.user, github_secret.secret))
            else:
                r = requests.get(get_url)

            if r.status_code != 200:
                error = 'Bad status code %i returned while fetching random repositories.'.format(r.status_code)
                data = r.json()
                if 'message' in data:
                    error += '\nError: {}'.format(r.json()['message'])
                QMessageBox.warning(None, 'Error while fetching random repositories', error)
                return ''

            data = r.json()
            repositories = ''
            for i in range(10):
                repositories += data[i]['html_url']
                repositories += '\n'
            return repositories

        except Exception as e:
            QMessageBox.warning(None, 'Error while fetching random repositories', 'An unknown error occurred during fetching random repositories:\n{}'.format(e))
            return ''

    ##
    # \brief Shows the 'About Qt' window.
    @pyqtSlot()
    def show_about_qt(self):
        QApplication.aboutQt()

    ##
    # \brief Shows the 'About PyQt5' window.
    @pyqtSlot()
    def show_about_pyqt(self):
        QMessageBox.about(None, 'About PyQt5', 'PyQt5 provides Python bindings for the Qt framework. PyQt5 is developed by Riverbank Computing Limited and available under the GPL version 3 as well as under a commercial license.')

    ##
    # \brief Shows the 'About ClassifyHub' window.
    @pyqtSlot()
    def show_about_classifyhub(self):
        QMessageBox.about(None, 'About ClassifyHub', 'Copyright (C) 2016,2017 Marcus Soll\nCopyright (C) 2016,2017 Malte Vosgerau\nClassifyHub is an algorithm to tackle the \'GitHub Classification Problem\'. The goal is to classify GitHub (https://github.com/) repositories into different categories.\nClassifyHub is licensed under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.')

    ##
    # \brief Returns if saving is available.
    #
    # \return True if saving is available.
    @pyqtSlot(result=bool)
    def getSaveReady(self):
        return self._save_ready

    ##
    # \brief Returns if computation is running.
    #
    # This includes both learning and batch processing.
    #
    # \return True if computation is running..
    @pyqtSlot(result=bool)
    def getRunning(self):
        return self._running

    ##
    # \brief Returns if computation is running.
    #
    # This includes both learning and batch processing.
    #
    # \return True if computation is running..
    @pyqtSlot(result=bool)
    def getLearningRunning(self):
        return self._learning_running

    ##
    # \brief QProperty holding if saving is available.
    saveReady = pyqtProperty(bool, fget=getSaveReady, notify=saveReadyChanged)

    ##
    # \brief QProperty holding if computation is running.
    running = pyqtProperty(bool, fget=getRunning, notify=runningChanged)

    ##
    # \brief QProperty holding if the learning process is running.
    learningRunning = pyqtProperty(bool, fget=getLearningRunning, notify=learningRunningChanged)


##
# \brief The SettingsProxy saves various information (e.g. from UI) to permanent memory.
#
# Internally a QSettings object is used which saves the data platform dependent. Ones a value is set, it will
# automatically be saved without the need to call a special 'flush' function.
class SettingsProxy(QObject):
    ##
    # \brief Signal emitted when x has changed.
    xChanged = pyqtSignal()

    ##
    # \brief Signal emitted when y has changed.
    yChanged = pyqtSignal()

    ##
    # \brief Signal emitted when width has changed.
    widthChanged = pyqtSignal()

    ##
    # \brief Signal emitted when height has changed.
    heightChanged = pyqtSignal()

    ##
    # \brief Constructor.
    #
    # \param parent QObject parent.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()

    ##
    # \brief Gets the x value of the window.
    #
    # \return x as int.
    def getX(self):
        return int(self.settings.value('window/x', 0))

    ##
    # \brief Stores the x value of the window.
    #
    # Change signal will be emitted when this function is called.
    #
    # \param i x value as int.
    def setX(self, i):
        self.settings.setValue('window/x', i)
        self.xChanged.emit()

    ##
    # \brief Gets the y value of the window.
    #
    # \return y as int.
    def getY(self):
        return int(self.settings.value('window/y', 0))

    ##
    # \brief Stores the y value of the window.
    #
    # Change signal will be emitted when this function is called.
    #
    # \param i y value as int.
    def setY(self, i):
        self.settings.setValue('window/y', i)
        self.yChanged.emit()

    ##
    # \brief Gets the width of the window
    #
    # \return width as int
    def getWidth(self):
        return int(self.settings.value('window/width', 800))

    ##
    # \brief Stores the width of the window.
    #
    # Change signal will be emitted when this function is called
    #
    # \param i width as int
    def setWidth(self, i):
        self.settings.setValue('window/width', i)
        self.widthChanged.emit()

    ##
    # \brief Gets the height of the window
    #
    # \return height as int
    def getHeight(self):
        return int(self.settings.value('window/height', 600))

    ##
    # \brief Stores the height of the window
    #
    # Change signal will be emitted when this function is called
    #
    # \param i height as int
    def setHeight(self, i):
        self.settings.setValue('window/height', i)
        self.heightChanged.emit()

    ##
    # \brief Gets the ClassifyHub configuration as a string.
    #
    # The configuration will be searched first at the local settings, then in the configserver.
    #
    # \param key Configuration key as string.
    # \return Value as string.
    @pyqtSlot(str, result=str)
    def getStringConfig(self, key):
        return str(self.settings.value('classifyhub/{}'.format(key), configserver.get(key)))

    ##
    # \brief Gets the ClassifyHub configuration as an int.
    #
    # The configuration will be searched first at the local settings, then in the configserver.
    #
    # \param key Configuration key as string.
    # \return Value as int.
    @pyqtSlot(str, result=int)
    def getIntConfig(self, key):
        return int(self.settings.value('classifyhub/{}'.format(key), configserver.get(key)))

    ##
    # \brief Gets the ClassifyHub configuration as a bool.
    #
    # The configuration will be searched first at the local settings, then in the configserver.
    #
    # \param key Configuration key as string
    # \return Value as bool.
    @pyqtSlot(str, result=bool)
    def getBoolConfig(self, key):
        return bool(int(self.settings.value('classifyhub/{}'.format(key), configserver.get(key))))

    ##
    # \brief Sets the ClassifyHub configuration as a string.
    #
    # The setting is both set globally and in the local settings.
    #
    # \param key Configuration key as string.
    # \param value Value as string.
    @pyqtSlot(str, str)
    def setStringConfig(self, key, value):
        self.settings.setValue('classifyhub/{}'.format(key), value)
        configserver.set(key, value)

    ##
    # \brief Sets the ClassifyHub configuration as an int.
    #
    # The setting is both set globally and in the local settings.
    #
    # \param key Configuration key as string.
    # \param value Value as int.
    @pyqtSlot(str, int)
    def setIntConfig(self, key, value):
        self.settings.setValue('classifyhub/{}'.format(key), value)
        configserver.set(key, value)

    ##
    # \brief Sets the ClassifyHub configuration as a bool.
    #
    # The setting is both set globally and in the local settings.
    #
    # \param key Configuration key as string.
    # \param value Value as bool.
    @pyqtSlot(str, bool)
    def setBoolConfig(self, key, value):
        self.settings.setValue('classifyhub/{}'.format(key), int(value))
        configserver.set(key, value)

    ##
    # \brief QProperty holding x value of window
    x = pyqtProperty(int, fget=getX, fset=setX, notify=xChanged)

    ##
    # \brief QProperty holding y value of window
    y = pyqtProperty(int, fget=getY, fset=setY, notify=yChanged)

    ##
    # \brief QProperty holding width of window
    width = pyqtProperty(int, fget=getWidth, fset=setWidth, notify=widthChanged)

    ##
    # \brief QProperty holding height of value
    height = pyqtProperty(int, fget=getHeight, fset=setHeight, notify=heightChanged)


##
# \brief Loads the configuration for the GUI.
#
# This will first parse the cmd arguments and then overwrite the unchanged ones with the ones set by the GUI.
def load_classifyhub_settings():
    settings = QSettings()
    old_config = configserver.get_config()
    configserver.parse_args()

    for key in old_config.keys():
        if configserver.get(key) == old_config[key]:
            # This key wasn't changed by cmd arguments - so try to load it from config
            data = configserver.get(key)
            if isinstance(data, bool):
                configserver.set(key, bool(int(settings.value('classifyhub/{}'.format(key), old_config[key]))))
            elif isinstance(data, int):
                configserver.set(key, int(settings.value('classifyhub/{}'.format(key), old_config[key])))
            elif isinstance(data, str):
                configserver.set(key, str(settings.value('classifyhub/{}'.format(key), old_config[key])))
        else:
            # Save cmd options so no confusion will occur for user
            settings.setValue('classifyhub/{}'.format(key), configserver.get(key))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    QApplication.setApplicationName('ClassifyHub')
    QApplication.setOrganizationName('Top-Ranger')

    load_classifyhub_settings()

    qmlRegisterType(UIProxy, 'UIProxy', 1, 0, 'UIProxy')
    qmlRegisterType(SettingsProxy, 'SettingsProxy', 1, 0, 'SettingsProxy')

    # Catch any python error to give an error message
    try:

        # test for secret
        check_user_and_secret()

        # Test if we need to learn
        need_to_learn = True
        if os.path.exists(configserver.get('model_path')):
            for file in os.listdir(configserver.get('model_path')):
                if os.path.isfile(configserver.get('model_path') + '/' + file) and file.endswith('.model'):
                    need_to_learn = False
                    break

        if need_to_learn:
            QMessageBox.information(None, 'No models', 'It seems that no models are present on your system ({}), this means that the learning process has not been run yet.\n'
                                                       'The learning process will be started now. This might take some time.'.format(configserver.get('model_path')))
            _learning_needed = True

        view = QQmlApplicationEngine()
        view.load(QUrl('./qml/application.qml'))
        view.rootObjects()[0].show()

        sys.exit(app.exec())
    except KeyboardInterrupt:
        # Do not print a stack trace
        print('')
        sys.exit(0)
    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        QMessageBox.critical(None, 'Unknown error', 'Received unknown error:\n\n'
                                                    '{}\n\n'
                                                    'Terminating application'.format(e))
        sys.exit(2)
