import re
import subprocess
import unittest

import git


class TestGit(unittest.TestCase):
    def test_git(self):
        msg = git.git("", bVerbose=False)
        expected = "git help"
        # https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
        self.assertIn(expected, msg, msg='"%s" not in "%s"' % (expected, msg))

    def test_git_config(self):
        msg = git.git("config", bVerbose=False)
        expected = "usage: git config"
        self.assertIn(expected, msg, msg='"%s" not in "%s"' % (expected, msg))

    def test_git_log(self):
        """
        test git log command
        >>> git log --follow git.py
        check "Author:", "Date:", "commit" strings are all included in the message
        """
        msg = git.git("log --follow git.py", bVerbose=False)
        # print "\ntest_git_log() msg ="
        # print msg
        try:
            self.assertIn("Author:", msg, msg='"%s" not in "%s"' % ("Author:", msg))
            self.assertIn("Date:", msg, msg='"%s" not in "%s"' % ("Date:", msg))
            self.assertIn("commit", msg, msg='"%s" not in "%s"' % ("commit", msg))
        except UnicodeDecodeError:
            self.assertIn("Author:", msg, msg='"%s" not in "%s"' % ("Author:", msg))
            self.assertIn("Date:", msg, msg='"%s" not in "%s"' % ("Date:", msg))
            self.assertIn("commit", msg, msg='"%s" not in "%s"' % ("commit", msg))

    def test_git_log_oneline(self):
        """
        test git log command
        >>> git log --follow --oneline git.py
        check first two commits included in the message
        """
        msg = git.git("log --follow --oneline git.py", bVerbose=False)

        expected0_str = '7dbdb92 Initial commit'
        # print "\ntest_git_log_oneline() msg ="
        # print msg

        print(f'test_git_log_oneline() : msg={msg}')

        try:
            self.assertIn(expected0_str, msg)
        except UnicodeDecodeError:
            self.assertIn(expected0_str, msg)

    def test_get_last_sha(self):

        # function under test
        result = git.get_last_sha()

        # get git log of the last commit
        p = subprocess.Popen(('git', 'log', '-1'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msgo, msge = str(p.stdout.read(),encoding='utf-8'), str(p.stderr.read(),encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        if msgo:
            self.assertTrue(result in msgo, msg='\nresult = {result}\nlog = {log}'.format(
                result=result,
                log=msgo,
            ))
        else:
            raise IOError('Unable to obtain git log\nmsgo = {log!r}\nmsge = {err!r}'.format(log=msgo, err=msge))

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
            ['git', 'log', '--pretty="{t1}%H{t1}{t2}%d{t2}"'.format(t1=token1, t2=token2)], 
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

        result_in_expected = [result_sha in expected_dict for result_sha in result_dict]
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


if "__main__" == __name__:
    unittest.main()
