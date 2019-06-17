import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )
    )
)

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

        self.temp_folder_name = tempfile.mkdtemp()

        # test repositories
        self.first_repository = 'https://github.com/kangwonlee/test-reposetman-fetch-and-reset-00'
        self.second_repository = 'https://github.com/kangwonlee/test-reposetman-fetch-and-reset-conflict'

        self.cwd = os.getcwd()
        self.clone_destination_folder = os.path.join(
            self.temp_folder_name,
            'temp_test_fetch_and_reset'
        )

        if os.path.exists(self.clone_destination_folder):
            self.reset_existing_repo()
        else:
            # clone the first test repository
            os.system(
                f'git clone {self.first_repository} {self.clone_destination_folder}')

            assert os.path.exists(self.clone_destination_folder)

            # change default remote repository to another
            os.chdir(self.clone_destination_folder)
            os.system(f'git remote set-url origin {self.second_repository}')
            os.system(f'git remote add test00 {self.first_repository}')
            os.system(f'git remote add conflict {self.second_repository}')

            # now `git pull` would cause a ** merge conflict **

        self.show_remotes('setUp')

    def tearDown(self):
        shutil.rmtree(self.temp_folder_name)

    def reset_existing_repo(self):
        os.chdir(self.clone_destination_folder)
        try:
            os.system(f'git remote set-url origin {self.first_repository}')
            os.system(f'git fetch origin')
            os.system(f"git reset --hard origin/master")
            os.system(f'git remote set-url origin {self.second_repository}')
            os.chdir(self.cwd)
        except BaseException as e:
            os.chdir(self.cwd)

            raise e

        self.show_remotes('reset_existing_repo')

    def show_remotes(self, caller='show_remotes'):
        os.chdir(self.clone_destination_folder)
        print(f'TestFetchAndReset.{caller}() '.ljust(60, '='))
        os.system(f'git remote -v')
        print(f'TestFetchAndReset.{caller}() '.ljust(60, '='))
        os.chdir(self.cwd)

    def test_fetch_and_reset(self):
        ret.fetch_and_reset(self.clone_destination_folder, b_verbose=True)

        # check the SHA of the last commit
        os.chdir(self.clone_destination_folder)
        r = subprocess.check_output(['git', 'log', '-1'])
        os.chdir(self.cwd)

        result_sha = r.decode().splitlines()[0].split()[-1]

        expected_sha = '2a3ac03f077d739b6cc115788703431bb5beefc8'

        self.assertEqual(expected_sha, result_sha)


if "__main__" == __name__:
    unittest.main()
