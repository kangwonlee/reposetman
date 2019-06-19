import git
import os
import re
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


class TestGit(unittest.TestCase):
    def test_git(self):
        msg = git.git("", bVerbose=False)
        expected = "git help"

        # https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
        self.assertIn(expected, msg, msg='"%s" not in "%s"' % (expected, msg))

    def test_git_config(self):
        msg = git.git(["config"], bVerbose=False)
        expected = "usage: git config"
        self.assertIn(expected, msg, msg='"%s" not in "%s"' % (expected, msg))

    def test_git_log(self):
        """
        test git log command
        >>> git log test_git.py
        check "Author:", "Date:", "commit" strings are all included in the message
        """
        msg = git.git(("log", __file__), bVerbose=False)

        try:
            for token in ("Author:", "Date:", "commit"):
                self.assertIn(token, msg, msg=f'"{token}" not in "{msg}"')
        except UnicodeDecodeError:
            for token in ("Author:", "Date:", "commit"):
                self.assertIn(token, msg, msg=f'"{token}" not in "{msg}"')

    def test_git_log_oneline(self):
        """
        test git log command
        >>> git log --oneline git.py
        check first two commits included in the message
        """
        msg = git.git(("log", "--oneline", __file__), bVerbose=False)

        assert_message = f"git message = {msg}"

        try:
            self.assertTrue(msg, msg=assert_message)
        except UnicodeDecodeError:
            self.assertTrue(msg, msg=assert_message)

    def test_get_last_sha(self):

        # function under test
        result = git.get_last_sha()

        # get git log of the last commit
        p = subprocess.Popen(('git', 'log', '-1'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msgo, msge = str(
            p.stdout.read(), encoding='utf-8'), str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        if msgo:
            self.assertTrue(result in msgo, msg='\nresult = {result}\nlog = {log}'.format(
                result=result,
                log=msgo,
            ))
        else:
            raise IOError('Unable to obtain git log\nmsgo = {log!r}\nmsge = {err!r}'.format(
                log=msgo, err=msge))

    def test_git_last_sha_file(self):
        filepath = os.path.abspath(__file__)

        result = git.get_last_sha(path=filepath)

        # get git log of the last commit
        p = subprocess.Popen(('git', 'log', '-1', filepath),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msgo, msge = str(
            p.stdout.read(), encoding='utf-8'), str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        if msgo:
            self.assertTrue(result in msgo, msg='\nresult = {result}\nlog = {log}'.format(
                result=result,
                log=msgo,
            ))
        else:
            raise IOError('Unable to obtain git log\nmsgo = {log!r}\nmsge = {err!r}'.format(
                log=msgo, err=msge))

    def test_get_refs_tag_deref(self):
        # function under test
        result = git.get_refs_tag_deref()

        # The result should be True
        self.assertTrue(result)

        # convert result into a dictioany
        # SHA as key
        # list of tags as value
        result_dict = {}
        for result_tuple in result:
            tag, sha = result_tuple
            result_dict[sha] = result_dict.get(sha, [])
            result_dict[sha].append(tag)

        # start preparing for the expected dictionary
        token1 = '@@@'
        token2 = '###'

        # run command
        p = subprocess.Popen(
            ['git', 'log',
                '--pretty="{t1}%H{t1}{t2}%d{t2}"'.format(t1=token1, t2=token2)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # result of the command
        msgo = str(p.stdout.read(), encoding='utf-8')
        msge = str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        self.assertFalse(msge)

        # from the result, prepare expected dictionary
        expected_dict = {}

        for match in re.finditer(r'{t1}(?P<sha>.+?){t1}{t2}\s+\((?P<ref>.+?)\){t2}'.format(t1=token1, t2=token2), msgo, re.M):
            d = match.groupdict()
            if 'tag:' in d['ref']:
                tag_list = d['ref'].replace('tag: ', '').split(', ')

                expected_dict[d['sha']] = tag_list

        result_in_expected = [
            result_sha in expected_dict for result_sha in result_dict]
        self.assertTrue(any(result_in_expected))

    def test_ls_remote_tag(self):
        # function under test
        result_sha_tag_list = git.ls_remote_tag()

        result_set = set(result_sha_tag_list)

        # prepare for the expected set
        # run command
        p = subprocess.Popen(
            ['git', 'show-ref', '--tags', '--dereference'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # result of the command
        msgo = str(p.stdout.read(), encoding='utf-8')
        msge = str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        self.assertFalse(msge)

        expected_set = set()

        for line in msgo.splitlines():
            if line.endswith('^{}'):
                sha, ref = line.split()
                tag = ref.replace('^{}', '').replace('refs/tags/', '')
                expected_set.add((sha, tag))

        self.assertTrue(expected_set.intersection, result_set)

    def test_has_a_tag(self):

        # prepare for the expected set
        # run command
        p = subprocess.Popen(
            ['git', 'show-ref', '--tags', '--dereference'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # result of the command
        msgo = str(p.stdout.read(), encoding='utf-8')
        msge = str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        self.assertFalse(msge)

        expected_set = set()

        for line in msgo.splitlines():
            if line.endswith('^{}'):
                sha, ref = line.split()
                _ = ref.replace('^{}', '').replace('refs/tags/', '')
                expected_set.add(sha)

        # function under test
        for sha in expected_set:
            self.assertTrue(git.has_a_tag(sha))

    def test_get_remote_branch_list(self):
        result = git.get_remote_branch_list()

        # is sequence?
        self.assertLessEqual(0, len(result))

        self.assertTrue(all(
            [' -> ' for branch in result]
        ))

    def test_which_git(self):
        result = git.which_git()
        self.assertTrue(os.path.exists(result), msg=f"Cannot find {result}")


class TestRet(unittest.TestCase):
    def test_set_id_to_url_00(self):
        input_url = 'https://github.com/abc/def.git'
        result = git.set_id_to_url(input_url, 'xyz')
        expected = 'https://xyz@github.com/abc/def.git'

        self.assertEqual(expected, result)

    def test_set_id_to_url_01(self):
        input_url = 'https://def@github.com/abc/def.git'
        result = git.set_id_to_url(input_url, 'xyz')
        expected = 'https://xyz@github.com/abc/def.git'

        self.assertEqual(expected, result)


class TestGitCheckout(unittest.TestCase):
    def setUp(self):
        self.temp_folder = tempfile.TemporaryDirectory()
        subprocess.run(['git', 'init'], cwd=self.temp_folder.name)
        subprocess.run(['git', 'config', 'user.name', 'temp'],
                       cwd=self.temp_folder.name)
        subprocess.run(['git', 'config', 'user.email',
                        'temp@temp.net'], cwd=self.temp_folder.name)

        tempfile_full_path = os.path.join(self.temp_folder.name, 'temp')

        with open(tempfile_full_path, 'w') as f:
            f.write('tempfile\n')

        subprocess.run(['git', 'add', tempfile_full_path],
                       cwd=self.temp_folder.name)
        subprocess.run(['git', 'commit', '-m', 'first commit'],
                       cwd=self.temp_folder.name)

        self.branch_name = 'branch'

        subprocess.run(['git', 'checkout', '-b', self.branch_name],
                       cwd=self.temp_folder.name)

        with open(tempfile_full_path, 'a') as f:
            f.write('modified\n')

        subprocess.run(['git', 'add', tempfile_full_path],
                       cwd=self.temp_folder.name)
        subprocess.run(['git', 'commit', '-m', 'second commit'],
                       cwd=self.temp_folder.name)

        self.current_branch_name = 'master'

        subprocess.run(
            ['git', 'checkout', self.current_branch_name], cwd=self.temp_folder.name)

        self.cwd = os.getcwd()

        os.chdir(self.temp_folder.name)

    def tearDown(self):
        os.chdir(self.cwd)
        del self.temp_folder

    def test_starts_with_already_on(self):
        _, stderr = git.checkout(self.current_branch_name)

        self.assertTrue(git.starts_with_already_on(
            stderr), msg=f'\nstderr = \n{stderr}')

    def detach_head(self):
        r = subprocess.run(["git", "show", "--summary", "--oneline"],
                           cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        last_rev_sha = r.stdout.strip().split()[0]

        r2 = subprocess.run(["git", "checkout", last_rev_sha],
                            cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        return [r, r2], last_rev_sha

    def test_is_head_detached(self):
        r_list, _ = self.detach_head()

        self.assertTrue(git.is_head_detached(r_list[-1].stderr), msg=(
            f"\nstderr :\n{r_list[-1].stderr}\n"
            "git show:\n"
            f"{r_list[0].stdout}"
        )
        )

    def switch_to_the_branch(self):
        r = subprocess.run(["git", "checkout", self.branch_name],
                           cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        return [r], self.branch_name

    def test_switched_to_intended_branch(self):
        r_list, commit = self.switch_to_the_branch()

        self.assertTrue(git.switched_to_intended_branch(commit, r_list[-1].stderr), msg=(
            f"\nstderr :\n{r_list[-1].stderr}\n"
            "stdout :\n"
            f"{r_list[-1].stdout}"
        )
        )

    def checkout_sha_sha(self):
        r0 = subprocess.run(["git", "show", "--summary", "--oneline"],
                            cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        rev_sha_0 = r0.stdout.strip().split()[0]

        r1 = subprocess.run(["git", "show", self.branch_name, "--summary", "--oneline"],
                            cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        rev_sha_1 = r1.stdout.strip().split()[0]

        r2 = subprocess.run(["git", "checkout", rev_sha_0],
                            cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')
        r3 = subprocess.run(["git", "checkout", rev_sha_1],
                            cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        return [r0, r1, r2, r3], rev_sha_1

    def test_is_prev_now(self):
        r_list, _ = self.checkout_sha_sha()

        self.assertTrue(git.is_prev_now(r_list[-1].stderr), msg=(
            f"\nstderr :\n{r_list[-1].stderr}\n"
            "stdout :\n"
            f"{r_list[-1].stdout}"
        )
        )

    def test_show_stderr_prev_now(self):
        r_list, commit = self.checkout_sha_sha()

        self.assertFalse(git.show_stderr(r_list[-1].stderr, commit), msg=(
            f"\nstderr :\n{r_list[-1].stderr}\n"
            "stdout:\n"
            f"{r_list[-1].stdout}"
        )
        )

    def test_show_stderr_switch_to_the_branch(self):
        r_list, commit = self.switch_to_the_branch()

        self.assertFalse(git.show_stderr(r_list[-1].stderr, commit), msg=(
            f"\nstderr :\n{r_list[-1].stderr}\n"
            "stdout:\n"
            f"{r_list[-1].stdout}"
        )
        )

    def test_show_stderr_detach_head(self):
        r_list, commit = self.detach_head()

        self.assertFalse(git.show_stderr(r_list[-1].stderr, commit), msg=(
            f"\nstderr :\n{r_list[-1].stderr}\n"
            "git show:\n"
            f"{r_list[0].stdout}"
        )
        )

    def test_show_stderr_already_on(self):
        stdout, stderr = git.checkout(self.current_branch_name)

        self.assertFalse(git.show_stderr(stderr, self.current_branch_name), msg=(
            f"\nstderr :\n{stderr}\n"
            "stdout :\n"
            f"{stdout}"
        )
        )


class TestGitCheckoutDate(unittest.TestCase):
    def setUp(self):
        self.temp_folder = tempfile.TemporaryDirectory()
        subprocess.run(['git', 'init'], cwd=self.temp_folder.name)
        subprocess.run(['git', 'config', 'user.name', 'temp'],
                       cwd=self.temp_folder.name)
        subprocess.run(['git', 'config', 'user.email',
                        'temp@temp.net'], cwd=self.temp_folder.name)

        tempfile_full_path = os.path.join(self.temp_folder.name, 'temp')

        with open(tempfile_full_path, 'w') as f:
            f.write('tempfile\n')

        self.date_0 = '2008-01-01 12:00:00'

        subprocess.run(['git', 'add', tempfile_full_path],
                       cwd=self.temp_folder.name)
        subprocess.run(['git', 'commit', '-m', 'first commit',
                        '--date', self.date_0], cwd=self.temp_folder.name)

        self.branch_name = 'branch'

        subprocess.run(['git', 'checkout', '-b', self.branch_name],
                       cwd=self.temp_folder.name)

        with open(tempfile_full_path, 'a') as f:
            f.write('modified\n')

        subprocess.run(['git', 'add', tempfile_full_path],
                       cwd=self.temp_folder.name)
        subprocess.run(['git', 'commit', '-m', 'second commit'],
                       cwd=self.temp_folder.name)

        self.current_branch_name = 'master'

        subprocess.run(
            ['git', 'checkout', self.current_branch_name], cwd=self.temp_folder.name)

    def tearDown(self):
        del self.temp_folder

    def test_checkout_date(self):
        stdout, stderr = git.checkout_date(
            self.date_0, repo_path=self.temp_folder.name)

        r = subprocess.run(["git", "log", "-1", '''--format=medium''', '--date=iso'],
                           cwd=self.temp_folder.name, capture_output=True, encoding='utf-8')

        result = ' '.join(r.stdout.splitlines()[2].split()[1:3])

        self.assertEqual(result, self.date_0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")


if "__main__" == __name__:
    unittest.main()
