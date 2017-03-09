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

import modelstore
import utility
import github
import logging
import pickle
import base64

import sklearn.tree
import sklearn.neighbors


##
# \brief Returns all implemented classifiers.
#
# \return List of classifiers.
def get_all_classifiers():
    return [FileClassifier(),
            ReadmeClassifier(),
            MetadataClassifier(),
            LanguageClassifier(),
            LanguageDetailsClassifier(),
            NameClassifier(),
            CommitMessageClassifier(),
            RepositoryStructureClassifier(),
            ]


##
# \brief Base class for all classifier.
#
# The classifier class is the base class for all weak classifier.
# A weak classifier is an algorithm which solves the 'GitHub Classification Problem' better than random guessing.
#
# All weak classifier have to implement all methods of Classifier to be considered as a valid classifier.
class Classifier:
    ##
    # \brief Constructor.
    def __init__(self):
        pass

    ##
    # \brief Returns the name of the classifier.
    #
    # The name should be unique as it may be used to identify the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        raise NotImplementedError('The method "name" of Classifier is not implemented')

    ##
    # \brief Classifies the given repository.
    #
    # It is necessary to first train the classifier using the Classifier.learn method, otherwise this method might
    # not work.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        # Data: Single github class
        raise NotImplementedError('The method "classify" of Classifier is not implemented')

    ##
    # \brief Trains the classifier on the given data set.
    #
    # After training the resulting model is saved to permanent memory and the Classifier.classify method might be
    # invoked.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        # learn, test: Array of github classes
        raise NotImplementedError('The method "learn" of Classifier is not implemented')


##
# \brief The FileClassifier rates the repositories based on the file type.
#
# The file type is determined from the file extension.
class FileClassifier(Classifier):
    ##
    # \brief Constructor.
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('FileClassifier')

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'FileClassifier'

    ##
    # \brief Classifies the repo based on the type of the files contained in the repository.
    #
    # The probability for each class given a file type is determined at the learning.
    # The classifier averages the probability over all files it found in the repository.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        result = utility.get_zero_class_dict()

        try:
            all_files = data.get_all_files()
        except github.GithubError:
            return result

        if len(all_files) == 0:
            return result

        for file in all_files:
            file = file.split('/')[-1]
            file = file.split('.')[-1]
            file = file.lower()
            if file in self._model.config:
                for c in self._model.config[file]:
                    result[c] += self._model.config[file][c]

        for key in result.keys():
            result[key] /= len(all_files)

        return result

    ##
    # \brief Learns the probability of a class given the file type.
    #
    # This is achieved by looking through all provided learning repositories and calculating the probability as
    # \f$P(Class | File) = \frac{N_{Files\ from\ class}}{N_{Files\ from\ all\ classes}}\f$.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()

        for data in learn:
            try:
                file_list = data[0].get_all_files()
            except github.GithubError:
                continue

            for file in file_list:
                file = file.split('/')[-1]
                file = file.split('.')[-1]
                file = file.lower()
                if file not in self._model.config:
                    self._model.config[file] = utility.get_zero_class_dict()
                self._model.config[file][data[1]] += 1

        for file in self._model.config:
            count = 0
            for c in self._model.config[file]:
                count += self._model.config[file][c]
            if count <= 1:
                continue
            for c in self._model.config[file]:
                self._model.config[file][c] /= count

        self._model.save()


##
# \brief The ReadmeClassifier calculates the probability of classes from the content of README files.
#
# For this the classifier puts the readme into a <em>Bag-of-words</em> and comparing that to all READMEs encountered
# at learning time using <em>k-Nearest Neighbors</em>.
class ReadmeClassifier(Classifier):
    ##
    # \brief Constructor.
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('ReadmeClassifier')
        self._knn = None

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'ReadmeClassifier'

    ##
    # \brief Classifies the repositories based on the README.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        if 'version' not in self._model.config:
            logging.error('Trying to use ReadmeClassifier without learning first')
            return utility.get_zero_class_dict()

        if self._model.config['version'] != sklearn.__version__:
            logging.error('Using ReadmeClassifier with different scikit learn version (trained on: {}, used: {}) - relearn classifier first'.format(self._model.config['version'], sklearn.__version__))
            return utility.get_zero_class_dict()

        try:
            readme = data.get_readme()
        except github.GithubError:
            return utility.get_zero_class_dict()

        if self._knn is None:
            self._knn = pickle.loads(base64.b64decode(self._model.config['knn']))

        bow = [False for _ in self._model.config['bow']]
        for word in readme.split():
            i = self._find_position(word.decode('utf-8').lower())
            if i != -1:
                bow[i] = True

        probability = self._knn.predict_proba([bow])
        result = utility.get_zero_class_dict()

        for i in range(len(self._knn.classes_)):
            result[self._knn.classes_[i]] = probability[0][i]
        return result

    ##
    # \brief Finds the position of word in the <em>Bag-of-words</em>.
    #
    # This needs the 'lookup' attribute in the model which is created at learning.
    #
    # \param word Word for which the position should be found.
    # \return Position or -1 if not in <em>Bag-of-words</em>.
    def _find_position(self, word):
        if word not in self._model.config['lookup']:
            return -1
        return self._model.config['lookup'][word]

    ##
    # \brief Learns the <em>Bag-of-words</em> and the model from all provided repositories.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()
        self._model.config['version'] = sklearn.__version__
        self._knn = None

        word_dict = dict()

        # Find common words
        for data in learn:
            try:
                readme = data[0].get_readme()
            except github.GithubError:
                continue

            word_set = set(readme.decode('utf-8').lower().split())

            for word in word_set:
                if word in word_dict:
                    word_dict[word] += 1
                else:
                    word_dict[word] = 1

        bow = []
        for word in word_dict:
            if word_dict[word] >= 2:
                bow += [word]

        # Save guard
        if len(bow) == 0:
            bow = list(word_dict)

        self._model.config['bow'] = bow

        # Create lookup
        lookup = dict()
        for i in range(len(bow)):
            lookup[bow[i]] = i

        self._model.config['lookup'] = lookup

        # Build KNN
        dataset = []
        labels = []
        for data in learn:
            try:
                readme = data[0].get_readme()
            except github.GithubError:
                continue

            bow_data = [False for _ in bow]

            for word in readme.split():
                i = self._find_position(word.decode('utf-8'))
                if i != -1:
                    bow_data[i] = True

            dataset += [bow_data]
            labels += [data[1]]

        # Check for empty data set
        if len(dataset) == 0 or len(labels) == 0:
            logging.error('Trying to learn ReadmeClassifier with an empty data set. This is not possible.\n'
                          'Possible errors:\n'
                          ' * Your learning folder is not set up correctly\n'
                          ' * Your rate limit is exhausted\n'
                          ' * There is an error with your internet connection\n'
                          ' * There  is an error while connecting to GitHub\n')
            self._model.clear()
            self._model.save()
            return

        knn = sklearn.neighbors.KNeighborsClassifier(n_neighbors=10, metric='jaccard')
        knn.fit(dataset, labels)

        # Save results
        self._knn = knn
        self._model.config['knn'] = base64.b64encode(pickle.dumps(knn)).decode()
        self._model.save()


##
# \brief The MetadataClassifier ates the repositories based on the metadata.
#
# A <em>Decision Tree</em> is used for the classification. The following metadata is used;
#  - Is the repository a fork?
#  - Has the repository a website?
#  - Size of repository
#  - Number of stargazers
#  - Number of watchers
#  - Has the project a wiki?
#  - Has the project 'Pages'?
#  - Number of forks
#  - Number of issues
#  - Number of subscribers
class MetadataClassifier(Classifier):
    ##
    # \brief Constructor.
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('MetadataClassifier')
        self._tree = None

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'MetadataClassifier'

    ##
    # \brief Creates the input array out of the repository.
    #
    # \param github_object github.Github object representing the repository.
    # \return Array of metadata.
    def _get_input(self, github_object):
        try:
            metadata = github_object.get_repository_data()
            input = [
                metadata['fork'],
                True if metadata['homepage'] is not None else False,
                metadata['size'],
                metadata['stargazers_count'],
                metadata['watchers_count'],
                metadata['has_wiki'],
                metadata['has_pages'],
                metadata['forks_count'],
                metadata['open_issues_count'],
                metadata['subscribers_count']
            ]
            return input
        except github.GithubError:
            return [0.0 for _ in range(10)]

    ##
    # \brief Classifies the repository based on the learned <em>Decision Tree</em>.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        if 'version' not in self._model.config:
            logging.error('Trying to use MetadataClassifier without learning first')
            return utility.get_zero_class_dict()

        if self._model.config['version'] != sklearn.__version__:
            logging.error('Using MetadataClassifier with different scikit learn version (trained on: {}, used: {}) - relearn classifier first'.format(self._model.config['version'], sklearn.__version__))
            return utility.get_zero_class_dict()

        if self._tree is None:
            self._tree = pickle.loads(base64.b64decode(self._model.config['tree']))

        probability = self._tree.predict_proba([self._get_input(data)])
        result = utility.get_zero_class_dict()
        for i in range(len(self._tree.classes_)):
            result[self._tree.classes_[i]] = probability[0][i]
        return result

    ##
    # \brief Trains a <em>Decision Tree</em> based on the provided repositories.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()
        self._model.config['version'] = sklearn.__version__
        self._tree = None

        input = []
        classes = []
        for data in learn:
            try:
                input += [self._get_input(data[0])]
                classes += [data[1]]
            except github.GithubError:
                continue

        # Check for empty data set
        if len(input) == 0 or len(classes) == 0:
            logging.error('Trying to learn MetadataClassifier with an empty data set. This is not possible.\n'
                          'Possible errors:\n'
                          ' * Your learning folder is not set up correctly\n'
                          ' * Your rate limit is exhausted\n'
                          ' * There is an error with your internet connection\n'
                          ' * There  is an error while connecting to GitHub\n')
            self._model.clear()
            self._model.save()
            return

        tree = sklearn.tree.DecisionTreeClassifier(min_samples_leaf=3)
        tree.fit(input, classes)

        self._tree = tree
        self._model.config['tree'] = base64.b64encode(pickle.dumps(tree)).decode()
        self._model.save()


##
# \brief The LanguageClassifier classifies the repositories based on the main language (as reported by GitHub).
#
# The probability of a class given the language is calculated from the learning data as following:
# \f$P(Class | Language) = \frac{N_{Repositories\ from\ class\ with\ language}}{N_{Repositories\ with\ language}}\f$.
class LanguageClassifier(Classifier):
    ##
    # \brief Constructor
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('LanguageClassifier')

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'LanguageClassifier'

    ##
    # \brief Classifies the repositories based on the main language.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        try:
            language = data.get_repository_data()['language']
        except github.GithubError:
            return utility.get_zero_class_dict()

        if language is None:
            language = '_None_'

        if language in self._model.config:
            return self._model.config[language].copy()
        else:
            return utility.get_zero_class_dict()

    ##
    # \brief Learns the distribution of the languages based on the provided repositories.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()

        for data in learn:
            try:
                language = data[0].get_repository_data()['language']
            except github.GithubError:
                continue

            if language is None:
                language = '_None_'

            if language not in self._model.config:
                self._model.config[language] = utility.get_zero_class_dict()
            self._model.config[language][data[1]] += 1

        for language in self._model.config:
            count = 0
            for c in self._model.config[language]:
                count += self._model.config[language][c]

            # Saveguard - should never be true
            if count == 0:
                logging.error('LanguageClassifier has zero count for {}'.format(language))
                continue

            for c in self._model.config[language]:
                self._model.config[language][c] /= count

        self._model.save()


##
# \brief The LanguageDetailsClassifier classifies the repositories based on the language distribution.
#
# The language distribution of a repository is measured in the combined size of the files containing the language, as
# reported by GitHub. The classification is done based on a <em>Decision Tree</em> trained on the language distribution.
class LanguageDetailsClassifier(Classifier):
    ##
    # \brief Constructor
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('LanguageDetailsClassifier')
        self._tree = None

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'LanguageDetailsClassifier'

    ##
    # \brief Returns the distribution of languages based on known languages.
    #
    # \param languages Set {LANGUAGE: SIZE} containing the size of files with a given language.
    # \param known_languages List of known languages.
    # \return List containing the distribution of languages.
    def _get_entry(self, languages, known_languages):
        entry = []
        for language in known_languages:
            if language in languages:
                entry += [languages[language]]
            else:
                entry += [0]
        sum_entry = sum(entry)
        if sum_entry != 0:
            entry = [x / sum_entry for x in entry]
        return entry

    ##
    # \brief Classifies the reoisitory based on the learned <em>Decision Tree</em>.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        if 'version' not in self._model.config:
            logging.error('Trying to use LanguageDetailsClassifier without learning first')
            return utility.get_zero_class_dict()

        if self._model.config['version'] != sklearn.__version__:
            logging.error('Using LanguageDetailsClassifier with different scikit learn version (trained on: {}, used: {}) - relearn classifier first'.format(self._model.config['version'], sklearn.__version__))
            return utility.get_zero_class_dict()

        if self._tree is None:
            self._tree = pickle.loads(base64.b64decode(self._model.config['tree']))

        try:
            languages = data.get_languages()
        except github.GithubError:
            return utility.get_zero_class_dict()

        probability = self._tree.predict_proba([self._get_entry(languages, self._model.config['known_languages'])])
        result = utility.get_zero_class_dict()
        for i in range(len(self._tree.classes_)):
            result[self._tree.classes_[i]] = probability[0][i]
        return result

    ##
    # \brief Learns the <em>Decision Tree</em> based on the language distribution.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()
        self._model.config['version'] = sklearn.__version__
        self._tree = None

        known_languages = set()
        for data in learn:
            try:
                languages = data[0].get_languages()
            except github.GithubError:
                continue

            for language in languages:
                known_languages.add(language)

        known_languages = list(known_languages)

        dataset = []
        labels = []

        for data in learn:
            try:
                languages = data[0].get_languages()
            except github.GithubError:
                continue

            entry = self._get_entry(languages, known_languages)

            dataset += [entry]
            labels += [data[1]]

        # Check for empty data set
        if len(dataset) == 0 or len(labels) == 0:
            logging.error('Trying to learn LanguageDetailsClassifier with an empty data set. This is not possible.\n'
                          'Possible errors:\n'
                          ' * Your learning folder is not set up correctly\n'
                          ' * Your rate limit is exhausted\n'
                          ' * There is an error with your internet connection\n'
                          ' * There  is an error while connecting to GitHub\n')
            self._model.clear()
            self._model.save()
            return

        tree = sklearn.tree.DecisionTreeClassifier(min_samples_leaf=3)
        tree.fit(dataset, labels)

        self._tree = tree
        self._model.config['tree'] = base64.b64encode(pickle.dumps(tree)).decode()
        self._model.config['known_languages'] = known_languages
        self._model.save()


##
# \brief The NameClassifier classifies the repositories based on the name similarity.
#
# The similarity is determined by using the Levenshtein distance. The classification is done using the
# <em>k-Nearest Neighbors</em> algorithm.
class NameClassifier(Classifier):
    ##
    # \brief Constructor
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('NameClassifier')

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'NameClassifier'

    ##
    # \brief Classifies a repository based on its name.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        if len(self._model.config) is 0:
            logging.error('Trying to use NameClassifier without learning first')
            return utility.get_zero_class_dict()

        try:
            repo_name = data.get_repository_data()['name']
        except github.GithubError:
            return utility.get_zero_class_dict()

        distances = []
        for target in self._model.config:
            distances += [(target, utility.edit_distance(repo_name, target))]

        distances.sort(key=lambda x: x[1])

        result = utility.get_zero_class_dict()

        nn = 1

        for c in utility.get_classes():
            result[c] += self._model.config[distances[0][0]][c]

        while nn < len(distances) and distances[nn - 1][1] == distances[nn][1]:
            for c in utility.get_classes():
                result[c] += self._model.config[distances[nn][0]][c]
            nn += 1

        for c in utility.get_classes():
            result[c] /= nn

        return result

    ##
    # \brief Builds the <em>k-Nearest Neighbors</em> classifier based on the provided repositories.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()

        for data in learn:
            try:
                repo_name = data[0].get_repository_data()['name']
            except github.GithubError:
                continue

            if repo_name not in self._model.config:
                self._model.config[repo_name] = utility.get_zero_class_dict()
            self._model.config[repo_name][data[1]] += 1

        for repo_name in self._model.config:
            count = 0
            for c in self._model.config[repo_name]:
                count += self._model.config[repo_name][c]

            # Saveguard - should never be true
            if count == 0:
                logging.error('NameClassifier has zero count for {}'.format(repo_name))
                continue

            for c in self._model.config[repo_name]:
                self._model.config[repo_name][c] /= count

        self._model.save()


##
# \brief The CommitMessageClassifier calculates the probability of classes from the content of the commits.
#
# For this the classifier puts the commit messages into a <em>Bag-of-words</em> and comparing that to all
# commit messages of projects encountered at learning time using <em>k-Nearest Neighbors</em>.
class CommitMessageClassifier(Classifier):
    ##
    # \brief Constructor
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('CommitMessageClassifier')
        self._knn = None

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'CommitMessageClassifier'

    ##
    # \brief Classifies the repositories based on the commit messages.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        if 'version' not in self._model.config:
            logging.error('Trying to use CommitMessageClassifier without learning first')
            return utility.get_zero_class_dict()

        if self._model.config['version'] != sklearn.__version__:
            logging.error('Using CommitMessageClassifier with different scikit learn version (trained on: {}, used: {}) - relearn classifier first'.format(self._model.config['version'], sklearn.__version__))
            return utility.get_zero_class_dict()

        try:
            commits = data.get_commits()
        except github.GithubError:
            return utility.get_zero_class_dict()

        if self._knn is None:
            self._knn = pickle.loads(base64.b64decode(self._model.config['knn']))

        bow = [False for _ in self._model.config['bow']]
        for commit in commits:
            for word in commit['commit']['message'].split():
                i = self._find_position(word.lower())
                if i != -1:
                    bow[i] = True

        probability = self._knn.predict_proba([bow])
        result = utility.get_zero_class_dict()

        for i in range(len(self._knn.classes_)):
            result[self._knn.classes_[i]] = probability[0][i]
        return result

    ##
    # \brief Finds the position of word in the <em>Bag-of-words</em>.
    #
    # This needs the 'lookup' attribute in the model which is created at learning.
    #
    # \param word Word for which the position should be found.
    # \return Position or -1 if not in <em>Bag-of-words</em>.
    def _find_position(self, word):
        if word not in self._model.config['lookup']:
            return -1
        return self._model.config['lookup'][word]

    ##
    # \brief Learns the <em>Bag-of-words</em> and the model from all provided repositories.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()
        self._model.config['version'] = sklearn.__version__
        self._knn = None

        word_dict = dict()

        # Find common words
        for data in learn:
            try:
                commits = data[0].get_commits()
            except github.GithubError:
                continue

            word_set = set()
            for commit in commits:
                word_set.update(set(commit['commit']['message'].lower().split()))

            for word in word_set:
                if word in word_dict:
                    word_dict[word] += 1
                else:
                    word_dict[word] = 1

        bow = []
        for word in word_dict:
            if word_dict[word] >= 2:
                bow += [word]

        # Save guard
        if len(bow) == 0:
            bow = list(word_dict)

        self._model.config['bow'] = bow

        # Create lookup
        lookup = dict()
        for i in range(len(bow)):
            lookup[bow[i]] = i

        self._model.config['lookup'] = lookup

        # Build KNN
        dataset = []
        labels = []
        for data in learn:
            try:
                commits = data[0].get_commits()
            except github.GithubError:
                continue

            bow_data = [False for _ in bow]

            for commit in commits:
                for word in commit['commit']['message'].split():
                    i = self._find_position(word)
                    if i != -1:
                        bow_data[i] = True

            dataset += [bow_data]
            labels += [data[1]]

        # Check for empty data set
        if len(dataset) == 0 or len(labels) == 0:
            logging.error('Trying to learn CommitMessageClassifier with an empty data set. This is not possible.\n'
                          'Possible errors:\n'
                          ' * Your learning folder is not set up correctly\n'
                          ' * Your rate limit is exhausted\n'
                          ' * There is an error with your internet connection\n'
                          ' * There  is an error while connecting to GitHub\n')
            self._model.clear()
            self._model.save()
            return

        knn = sklearn.neighbors.KNeighborsClassifier(n_neighbors=10, metric='jaccard')
        knn.fit(dataset, labels)

        # Save results
        self._knn = knn
        self._model.config['knn'] = base64.b64encode(pickle.dumps(knn)).decode()
        self._model.save()


##
# \brief The RepositoryStructureClassifier calculates the probability of the classes by comparing the structure of a repository.
#
# For this the classifier puts the objects in the git tree into a <em>Bag-of-words</em> and compares that to all
# git trees of projects encountered at learning time using <em>k-Nearest Neighbors</em>.
#
# For improved results all appearence of the repo name are replaced by a placeholder. This should generalize more e.g. if the
# repository name is used as a folder name.
class RepositoryStructureClassifier(Classifier):
    ##
    # \brief Constructor.
    def __init__(self):
        super().__init__()
        self._model = modelstore.ModelStore('RepositoryStructureClassifier')
        self._knn = None

    ##
    # \brief Returns the name of the classifier.
    #
    # \return Name of the classifier as string.
    def name(self):
        return 'RepositoryStructureClassifier'

    ##
    # \brief Classifies the repositories based on the commit messages.
    #
    # \param data GitHub repository as github.Github object.
    # \return Dictionary {CLASS: PROBABILITY}, where CLASS is a string containing the class label and
    #         PROBABILITY is a float in [0.0, 1.0] containing the probability that the repository belongs to the class.
    def classify(self, data):
        if 'version' not in self._model.config:
            logging.error('Trying to use RepositoryStructureClassifier without learning first')
            return utility.get_zero_class_dict()

        if self._model.config['version'] != sklearn.__version__:
            logging.error('Using RepositoryStructureClassifier with different scikit learn version (trained on: {}, used: {}) - relearn classifier first'.format(self._model.config['version'], sklearn.__version__))
            return utility.get_zero_class_dict()

        try:
            tree = data.get_tree()
        except github.GithubError:
            return utility.get_zero_class_dict()

        name = data.get_dev_repo()[1].lower()

        if self._knn is None:
            self._knn = pickle.loads(base64.b64decode(self._model.config['knn']))

        bow = [False for _ in self._model.config['bow']]
        for object in tree['tree']:
            i = self._find_position(object['path'].lower().replace(name, '$REPO'))
            if i != -1:
                bow[i] = True

        probability = self._knn.predict_proba([bow])
        result = utility.get_zero_class_dict()

        for i in range(len(self._knn.classes_)):
            result[self._knn.classes_[i]] = probability[0][i]
        return result

    ##
    # \brief Finds the position of word in the <em>Bag-of-words</em>.
    #
    # This needs the 'lookup' attribute in the model which is created at learning.
    #
    # \param word Word for which the position should be found.
    # \return Position or -1 if not in <em>Bag-of-words</em>.
    def _find_position(self, word):
        if word not in self._model.config['lookup']:
            return -1
        return self._model.config['lookup'][word]

    ##
    # \brief Learns the <em>Bag-of-words</em> and the model from all provided repositories.
    #
    # \param learn List containing Tupel (GITHUB, CLASS), where GITHUB is the repository as a github.Github class and
    #              CLASS is the class label of the repository as a string.
    def learn(self, learn):
        self._model.clear()
        self._model.config['version'] = sklearn.__version__
        self._knn = None

        object_dict = dict()

        # Find common structure
        for data in learn:
            try:
                tree = data[0].get_tree()
            except github.GithubError:
                continue

            name = data[0].get_dev_repo()[1].lower()
            object_set = set()
            for object in tree['tree']:
                object_set.update({object['path'].lower().replace(name, '$REPO')})

            for word in object_set:
                if word in object_dict:
                    object_dict[word] += 1
                else:
                    object_dict[word] = 1

        bow = []
        for word in object_dict:
            if object_dict[word] >= 2:
                bow += [word]

        # Save guard
        if len(bow) == 0:
            bow = list(object_dict)

        self._model.config['bow'] = bow

        # Create lookup
        lookup = dict()
        for i in range(len(bow)):
            lookup[bow[i]] = i

        self._model.config['lookup'] = lookup

        # Build KNN
        dataset = []
        labels = []
        for data in learn:
            try:
                tree = data[0].get_tree()
            except github.GithubError:
                continue

            name = data[0].get_dev_repo()[1].lower()
            bow_data = [False for _ in bow]

            for object in tree['tree']:
                i = self._find_position(object['path'].lower().replace(name, '$REPO'))
                if i != -1:
                    bow_data[i] = True

            dataset += [bow_data]
            labels += [data[1]]

        # Check for empty data set
        if len(dataset) == 0 or len(labels) == 0:
            logging.error('Trying to learn RepositoryStructureClassifier with an empty data set. This is not possible.\n'
                          'Possible errors:\n'
                          ' * Your learning folder is not set up correctly\n'
                          ' * Your rate limit is exhausted\n'
                          ' * There is an error with your internet connection\n'
                          ' * There  is an error while connecting to GitHub\n')
            self._model.clear()
            self._model.save()
            return

        knn = sklearn.neighbors.KNeighborsClassifier(n_neighbors=10, metric='jaccard')
        knn.fit(dataset, labels)

        # Save results
        self._knn = knn
        self._model.config['knn'] = base64.b64encode(pickle.dumps(knn)).decode()
        self._model.save()
