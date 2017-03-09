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

import github
import configserver

class TestGithub(unittest.TestCase):
    def setUp(self):
        # setup config
        configserver._CONGIF['maximum_cache_age'] = 366000  # About 1000 years
        configserver._CONGIF['cache_path'] = './tests/cache'

        self.github = github.Github('Top-Ranger', 'kana-keyboard')

    def test___eq__(self):
        self.assertEqual(self.github, github.Github('Top-Ranger', 'kana-keyboard'))
        self.assertNotEqual(self.github, github.Github('TopRanger', 'kana-keyboard'))
        self.assertNotEqual(self.github, github.Github('Top-Ranger', 'kanakeyboard'))
        self.assertNotEqual(self.github, github.Github('TopRanger', 'kanakeyboard'))
        self.assertNotEqual(self.github, 'https://github.com/Top-Ranger/kana-keyboard')

    def test_github_error(self):
        with self.assertRaises(github.GithubError):
            self.github._get_data('error_test', 'https://api.github.com/repos/Top-Ranger/kana-keyboard')

    def test_get_repository_data(self):
        data = self.github.get_repository_data()
        # Test some values
        self.assertEqual(data['name'], 'kana-keyboard')
        self.assertEqual(data['owner']['login'], 'Top-Ranger')
        self.assertEqual(data['size'], 11)
        self.assertEqual(data['language'], 'QML')
        self.assertEqual(data['fork'], False)

    def test_repository_exists(self):
        self.assertTrue(self.github.repository_exists())
        unexisting = github.Github('aaa', 'aaa')
        self.assertFalse(unexisting.repository_exists())

    def test_get_repository_content(self):
        data = self.github.get_repository_content()
        # Test some values
        self.assertEqual(data[0]['path'], '.gitignore')
        self.assertEqual(data[0]['download_url'], 'https://raw.githubusercontent.com/Top-Ranger/kana-keyboard/master/.gitignore')
        self.assertEqual(data[0]['_links']['self'], 'https://api.github.com/repos/Top-Ranger/kana-keyboard/contents/.gitignore?ref=master')
        self.assertEqual(data[1]['path'], 'LICENSE')
        self.assertEqual(data[1]['download_url'], 'https://raw.githubusercontent.com/Top-Ranger/kana-keyboard/master/LICENSE')
        self.assertEqual(data[1]['_links']['self'], 'https://api.github.com/repos/Top-Ranger/kana-keyboard/contents/LICENSE?ref=master')

    def test_get_tree(self):
        data = self.github.get_tree()
        # Test some values
        self.assertEqual(data['sha'], '5f0d0543dd2bf16bcd8061b3ef58325a595fac28')
        self.assertEqual(data['tree'][0]['path'], '.gitignore')
        self.assertEqual(data['tree'][0]['size'], 19)
        self.assertEqual(data['tree'][-1]['path'], 'rpm/kana-keyboard.spec')
        self.assertEqual(data['tree'][-1]['size'], 802)

    def test_get_all_files(self):
        data = self.github.get_all_files()
        self.assertEqual(data, ['.gitignore', 'LICENSE', 'README.md', 'kana-keyboard.pro', 'kana_keyboard.conf', 'kana_keyboard.qml', 'kana-keyboard.spec'])

    def test_get_repo_url(self):
        self.assertEqual(self.github.get_repo_url(), 'https://github.com/Top-Ranger/kana-keyboard')

    def test_get_readme(self):
        self.assertEqual(self.github.get_readme(), b'A simple hiragana / katakana keyboard for SailfishOS \n\nAfter installation you have to manually activate the new keyboard under "Settings -> System -> Text input -> Keyboards". A restart may be required.\n')

    def test_get_file(self):
        self.assertEqual(self.github.get_file('layout/kana_keyboard.conf'), b'[kana_keyboard.qml]\nname=\xe4\xbb\xae\xe5\x90\x8d\nlanguageCode=\xe4\xbb\xae\xe5\x90\x8d\nhandler=Xt9InputHandler.qml \n')
        self.assertEqual(self.github.get_file('README.md'), b'A simple hiragana / katakana keyboard for SailfishOS \n\nAfter installation you have to manually activate the new keyboard under "Settings -> System -> Text input -> Keyboards". A restart may be required.\n')
        with self.assertRaises(github.GithubError):
            self.github.get_file('non_existing')

    def test_get_languages(self):
        self.assertEqual(self.github.get_languages(), {'QMake': 320, 'QML': 7447})

    def test_get_commits(self):
        data = self.github.get_commits()
        # Test some values
        self.assertEqual(data[0]['sha'], '5f0d0543dd2bf16bcd8061b3ef58325a595fac28')
        self.assertEqual(data[0]['commit']['message'], 'Updated version')
        self.assertEqual(data[-1]['sha'], 'f75ae8f6a00860a547281736355df0da029f79ef')
        self.assertEqual(data[-1]['commit']['message'], 'Initial release')

    def test_get_dev_repo(self):
        self.assertEqual(self.github.get_dev_repo(), ('Top-Ranger','kana-keyboard'))


class TestGithubSecret(unittest.TestCase):
    def test_existing(self):
        configserver._CONGIF['secret_file'] = './tests/secret/secret'
        configserver._CONGIF['user_file'] = './tests/secret/user'
        secret = github.GithubSecret()

        self.assertTrue(secret.secret_available)
        self.assertEqual(secret.secret, 'secret')
        self.assertEqual(secret.user, 'user')

    def test_user_non_existing(self):
        configserver._CONGIF['secret_file'] = './tests/secret/secret'
        configserver._CONGIF['user_file'] = './tests/user'
        secret = github.GithubSecret()

        self.assertFalse(secret.secret_available)

    def test_secret_non_existing(self):
        configserver._CONGIF['secret_file'] = './tests/secret_file'
        configserver._CONGIF['user_file'] = './tests/secret/user'
        secret = github.GithubSecret()

        self.assertFalse(secret.secret_available)

    def test_non_existing(self):
        configserver._CONGIF['secret_file'] = './tests/secret'
        configserver._CONGIF['user_file'] = './tests/user'
        secret = github.GithubSecret()

        self.assertFalse(secret.secret_available)
