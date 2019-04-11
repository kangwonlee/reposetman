import os
import shutil
import unittest

import regex_test as ret


class TestFetchAndReset(unittest.TestCase):
    def setUp(self):

        # test repositories
        first_repository = 'https://github.com/kangwonlee/test-reposetman-fetch-and-reset-00'
        second_repository = 'https://github.com/kangwonlee/test-reposetman-fetch-and-reset-conflict'

        # clone the first test repository
        self.clone_destination_folder = 'temp_test_fetch_and_reset'
        os.system(f'git clone {first_repository} {self.clone_destination_folder}')

        # change default remote repository to another
        self.cwd = os.getcwd()
        os.chdir(self.clone_destination_folder)
        os.system(f'git remote set-url origin {second_repository}')

        # now `git pull` would cause a ** merge conflict **

        os.chdir(self.cwd)

    def tearDown(self):
        shutil.rmtree(self.clone_destination_folder)

    def test_fetch_and_reset(self):
        pass
