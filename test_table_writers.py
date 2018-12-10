import os
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


class TestTextTableWriter(unittest.TestCase):
    def setUp(self):
        self.row_title_list = [f'test_row_{i:}' for i in range(3)]
        column_title_list = [f'test_column_{i:}' for i in range(3)]

        self.d = progress.RepoTable()
        for row_title in self.row_title_list:
            for column_title in column_title_list:
                self.d.set_row_column(row_title, column_title, row_title+column_title)

        self.section = 'test_section'
        self.file_prefix = 'test_output'
        self.path = os.path.split(__file__)[0]

    def test_gen_rows(self):
        writer = progress.TextTableWriter(
            self.d,
            self.section,
            self.row_title_list,
            filename_prefix=self.file_prefix,
            path=self.path,
        )

        expected_list = [
            '\ttest_column_0\ttest_column_1\ttest_column_2\n',
            'test_row_0\ttest_row_0test_column_0\ttest_row_0test_column_1\ttest_row_0test_column_2\n',
            'test_row_1\ttest_row_1test_column_0\ttest_row_1test_column_1\ttest_row_1test_column_2\n',
            'test_row_2\ttest_row_2test_column_0\ttest_row_2test_column_1\ttest_row_2test_column_2\n',
            ]

        for expected_str, result_str in zip(expected_list, writer.gen_rows()):
            self.assertEqual(expected_str, result_str)
