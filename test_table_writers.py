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


class BaseTestTableWriterTable(unittest.TestCase):
    def setUp(self):
        self.row_title_list = [f'test_row_{i:}' for i in range(3)]
        self.column_title_list = [f'test_column_{i:}' for i in range(3)]

        self.d = progress.RepoTable()
        for row_title in self.row_title_list:
            for column_title in self.column_title_list:
                self.d.set_row_column(row_title, column_title, 
                self.get_row_column_item(row_title, column_title))

        self.section = 'test_section'
        self.file_prefix = 'test_output'
        self.path = os.path.split(__file__)[0]

    def get_row_column_item(self, row, column):
        # decide an element for table[row][column]
        return row + column


class TestTextTableWriter(BaseTestTableWriterTable):
    def get_expected_list(self, writer):
        title_row = writer.col_sep.join([''] + self.column_title_list) + writer.row_sep
        
        expected_list = [title_row]
        for row_title in self.row_title_list:
            row_item_list = [row_title]
            for column_title in self.column_title_list:
                row_item_list.append(self.get_row_column_item(row_title, column_title))
            row_str = writer.col_sep.join(row_item_list) + writer.row_sep
            expected_list.append(row_str)

        return expected_list

    def test_gen_rows(self):
        # TODO : common base class for various table writers possible?

        writer = progress.TextTableWriter(
            self.d,
            self.section,
            self.row_title_list,
            filename_prefix=self.file_prefix,
            path=self.path,
        )

        expected_list = self.get_expected_list(writer)

        for expected_str, result_str in zip(expected_list, writer.gen_rows()):
            self.assertEqual(expected_str, result_str, msg='\n'
            f'expected = {repr(expected_str)}\n'
            f'result = {repr(result_str)}'
            )


class TestMarkdownTableWriter(BaseTestTableWriterTable):
    def get_expected_list(self, writer):

        space_sep_space = f"  {writer.col_sep}  "

        first_row = space_sep_space.join([writer.col_sep+'  '] + self.column_title_list)
        second_row = writer.col_sep.join([''] + [':-----:'] * (len(self.column_title_list)+1) + [''])

        title_row = writer.row_sep.join([first_row, second_row])
        
        expected_list = [title_row]
        for row_title in self.row_title_list:
            row_item_list = ['', row_title]
            for column_title in self.column_title_list:
                row_item_list.append(self.get_row_column_item(row_title, column_title))
            row_str = space_sep_space.join(row_item_list) + writer.row_sep
            expected_list.append(row_str)

        return expected_list

    def test_gen_rows_body(self):

        writer = progress.MarkdownTableWriter (
            self.d,
            self.section,
            self.row_title_list,
            filename_prefix=self.file_prefix,
            path=self.path,
        )

        expected_list = self.get_expected_list(writer)
        result_list = list(writer.gen_rows())

        for expected_str, result_str in zip(expected_list[1:], result_list[1:]):
            expected_split_list = expected_str.split()
            result_split_list = result_str.split()
            self.assertSequenceEqual(expected_split_list, result_split_list,
                '\n'
                f'expected_str = {repr(expected_str)}\n'
                f'result_str = {repr(result_str)}\n'
                f'expected_str.split() = {repr(expected_split_list)}\n'
                f'result_str.split() = {repr(result_split_list)}'
            )

    def test_gen_rows_header(self):

        writer = progress.MarkdownTableWriter (
            self.d,
            self.section,
            self.row_title_list,
            filename_prefix=self.file_prefix,
            path=self.path,
        )

        expected_list = self.get_expected_list(writer)

        expected_header_row, expected_second_row = expected_list[0].splitlines()

        expected_header_row_split = [string.strip() for string in expected_header_row.split(writer.col_sep)]
        expected_second_row_split = expected_second_row.split(writer.col_sep)

        result_header = next(writer.gen_rows())
        result_header_row, result_second_row = result_header.splitlines()

        result_header_row_split = [string.strip() for string in result_header_row.split(writer.col_sep)]
        result_second_row_split = result_second_row.split(writer.col_sep)

        self.assertSequenceEqual(expected_header_row_split, result_header_row_split)

        # second row
        self.assertEqual(len(expected_second_row_split), len(result_second_row_split), msg='\n'
                f'expected_str = {repr(expected_second_row)}\n'
                f'result_str = {repr(result_second_row)}\n'
                f'expected_str.split() = {repr(expected_second_row_split)}\n'
                f'result_str.split() = {repr(result_second_row_split)}'
        )

        for item in result_second_row_split:
            if item:
                self.assertEquals(':', item[0])
                self.assertEquals(':', item[-1])
                self.assertEquals('-', item[1])
                self.assertEquals('-', item[-2])
                self.assertLessEqual(4, len(item))
