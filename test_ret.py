import os
import shutil
import subprocess
import unittest

import regex_test as ret


def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``

    # https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied
    # https://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows

    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise IOError


class TestFetchAndReset(unittest.TestCase):
    def setUp(self):
        # test repositories
        self.first_repository = 'https://github.com/kangwonlee/test-reposetman-fetch-and-reset-00'
        self.second_repository = 'https://github.com/kangwonlee/test-reposetman-fetch-and-reset-conflict'

        self.cwd = os.getcwd()
        self.clone_destination_folder = os.path.abspath('temp_test_fetch_and_reset')

        if os.path.exists(self.clone_destination_folder):
            self.reset_to_first()
        else:
            # clone the first test repository
            os.system(f'git clone {self.first_repository} {self.clone_destination_folder}')

            # change default remote repository to another
            os.chdir(self.clone_destination_folder)
            os.system(f'git remote set-url origin {self.second_repository}')
            os.system(f'git remote add test00 {self.first_repository}')
            os.system(f'git remote add conflict {self.second_repository}')

            # now `git pull` would cause a ** merge conflict **

            os.chdir(self.cwd)

    def reset_to_first(self):
        os.chdir(self.clone_destination_folder)
        os.system(f'git remote set-url origin {self.first_repository}')
        os.system(f'git fetch origin')
        os.system(f"git reset --hard origin/master")

    def show_remotes(self, caller='show_remotes'):
        os.chdir(self.clone_destination_folder)
        print(f'TestFetchAndReset.{caller}() '.ljust(60, '='))
        os.system(f'git remote -v')
        print(f'TestFetchAndReset.{caller}() '.ljust(60, '='))
        os.chdir(self.cwd)

    def tearDown(self):
        self.reset_to_first()

    def test_fetch_and_reset(self):
        ret.fetch_and_reset(self.clone_destination_folder)

        os.chdir(self.clone_destination_folder)

        os.system('git log --all --graph --oneline')
