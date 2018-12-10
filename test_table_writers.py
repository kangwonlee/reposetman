import unittest

import progress


class TestMarkdownTableWriterRepoLinks(unittest.TestCase):
    def setUp(self):
        d = progress.RepoTable()
        self.reponame1 = 'abc'
        self.reponame2 = 'def'

        repo_list = [self.reponame1, self.reponame2]

        self.filename1 = 'iii123.py'
        self.filename2 = 'jjj456.ipynb'

        table = {
            self.reponame1 : {self.filename1:11, self.filename2:12},
            self.reponame2 : {self.filename1:21, self.filename2:22},
        }

        for repo_name in repo_list:
            d.add_row(row=repo_name, column=self.filename1, value=table[repo_name][self.filename1])

        self.section = 'section_name'

        self.m = progress.MarkdownTableWriterRepoLinks(d=d, section=self.section, repo_list=repo_list)

    def test_start_row(self):
        # check header column string
        expected = rf'| [abc](https://github.com/{self.section}/{self.reponame1}) '
        result = self.m.start_row(self.reponame1)
        self.assertEqual(expected, result)
