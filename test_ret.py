import os
import shutil
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
