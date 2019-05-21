import os
import unittest

import bs4

import progress


class BaseTestTableWriterRepoLinks(unittest.TestCase):
    def setUp(self):
        self.d = progress.RepoTable()

        self.reponame1 = 'abc'
        self.reponame2 = 'def'

        self.section = 'section_name'

        self.row_title_list = [self.reponame1, self.reponame2]

        self.domain_name = 'github.com'
        self.scheme = 'https://'

        self.repo_dict_list = []
        for repo_name in self.row_title_list:
            self.repo_dict_list.append({
                'name': repo_name,
                'url': f'{self.scheme}{self.domain_name}/{self.section}/{repo_name}'
            })

        self.filename1 = 'iii123.py'
        self.filename2 = 'jjj456.ipynb'

        self.column_title_list = [self.filename1, self.filename2]

        table = {
            self.reponame1: {self.filename1: 11, self.filename2: 12},
            self.reponame2: {self.filename1: 21, self.filename2: 22},
        }

        for repo_name in self.row_title_list:
            for path_name in self.column_title_list:
                self.d.set_row_column(
                    repo_name, path_name, table[repo_name][path_name])

        self.repo_url_lookup = {}

        for repo_info in self.repo_dict_list:
            self.repo_url_lookup[repo_info['name']] = repo_info['url']

    @staticmethod
    def get_expected_url(domain_name, file_name, ref='master'):
        return f"{domain_name}/blob/{ref}/{file_name}"


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
        self.path = os.path.dirname(__file__)

    def get_row_column_item(self, row, column):
        # decide an element for table[row][column]
        return row + column


class TestTextTableWriter(BaseTestTableWriterTable):
    def get_expected_list(self, writer):
        title_row = writer.col_sep.join(
            [''] + self.column_title_list) + writer.row_sep

        expected_list = [title_row]
        for row_title in self.row_title_list:
            row_item_list = [row_title]
            for column_title in self.column_title_list:
                row_item_list.append(
                    self.get_row_column_item(row_title, column_title))
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

        first_row = space_sep_space.join(
            [writer.col_sep+'  '] + self.column_title_list)
        second_row = writer.col_sep.join(
            [''] + [':-----:'] * (len(self.column_title_list)+1) + [''])

        title_row = writer.row_sep.join([first_row, second_row])

        expected_list = [title_row]
        for row_title in self.row_title_list:
            row_item_list = ['', row_title]
            for column_title in self.column_title_list:
                row_item_list.append(
                    self.get_row_column_item(row_title, column_title))
            row_str = space_sep_space.join(row_item_list) + writer.row_sep
            expected_list.append(row_str)

        return expected_list

    def test_gen_rows_body(self):

        writer = progress.MarkdownTableWriter(
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

        writer = progress.MarkdownTableWriter(
            self.d,
            self.section,
            self.row_title_list,
            filename_prefix=self.file_prefix,
            path=self.path,
        )

        expected_list = self.get_expected_list(writer)

        expected_header_row, expected_second_row = expected_list[0].splitlines(
        )

        expected_header_row_split = [
            string.strip() for string in expected_header_row.split(writer.col_sep)]
        expected_second_row_split = expected_second_row.split(writer.col_sep)

        result_header = next(writer.gen_rows())
        result_header_row, result_second_row = result_header.splitlines()

        result_header_row_split = [
            string.strip() for string in result_header_row.split(writer.col_sep)]
        result_second_row_split = result_second_row.split(writer.col_sep)

        self.assertSequenceEqual(
            expected_header_row_split, result_header_row_split)

        # second row
        self.assertEqual(len(expected_second_row_split), len(result_second_row_split), msg='\n'
                         f'expected_str = {repr(expected_second_row)}\n'
                         f'result_str = {repr(result_second_row)}\n'
                         f'expected_str.split() = {repr(expected_second_row_split)}\n'
                         f'result_str.split() = {repr(result_second_row_split)}'
                         )

        for item in result_second_row_split:
            if item:
                self.assertEqual(':', item[0])
                self.assertEqual(':', item[-1])
                self.assertEqual('-', item[1])
                self.assertEqual('-', item[-2])
                self.assertLessEqual(4, len(item))


class TestHtmlTableWriter(BaseTestTableWriterTable):
    def setUp(self):
        super().setUp()

        self.writer = progress.HtmlTableWriter(
            self.d,
            self.section,
            self.row_title_list,
            filename_prefix=self.file_prefix,
            path=self.path,
        )

    def test_gen_rows_bs4(self):

        result_txt = ''.join(list(self.writer.gen_rows()))

        soup = bs4.BeautifulSoup(result_txt, "lxml")

        table_list = soup.find_all('table')

        self.assertEqual(1, len(table_list))

        table = table_list[0]

        rows_list = table.find_all('tr')

        header_row = rows_list[0]
        body_rows_list = rows_list[1:]

        self.assertEqual(len(self.row_title_list), len(body_rows_list),
                         msg="number of body rows different\n"
                         )

        self.check_table_header(header_row)

        self.check_table_body_rows(body_rows_list)

    def check_table_header(self, header_row):

        header_column_list = header_row.find_all('th')
        header_body_list = header_column_list[1:]

        self.assertEqual(len(self.column_title_list), len(header_body_list))

        for expected_header, header_body in zip(self.column_title_list, header_body_list):
            self.assertEqual(expected_header, header_body.get_text().strip())

    def check_table_body_rows(self, body_rows_list):
        for expected_row_header, row in zip(self.row_title_list, body_rows_list):
            columns_list = row.find_all('td')

            row_header = columns_list[0]
            self.assertEqual(expected_row_header,
                             row_header.get_text().strip())

            row_items_list = columns_list[1:]
            self.assertEqual(len(self.column_title_list), len(row_items_list))

            for column_title, table_item in zip(self.column_title_list, row_items_list):
                self.assertEqual(
                    self.d[expected_row_header][column_title],
                    table_item.get_text().strip()
                )


class TestMDlinkTableWriter(BaseTestTableWriterRepoLinks):
    def setUp(self):
        super().setUp()
        self.table_writer = progress.MDlinkTableWriter(self.d, self.row_title_list, 'test_MD_link_table',
                                                       repo_list=self.repo_dict_list,
                                                       )

    def test_get_repo_url(self):
        for repo_name in self.row_title_list:
            result = self.table_writer.get_repo_url(repo_name)
            expected = self.repo_url_lookup[repo_name]
            self.assertEqual(result, expected,
                             f"\ninput = {repo_name}\nresult = {result}")

    def test_start_row(self):
        for repo_name in self.row_title_list:
            # function under test
            result = self.table_writer.start_row(repo_name)

            expected_name = repo_name
            expected_url = self.repo_url_lookup[repo_name]
            expected = f"| [{expected_name}]({expected_url}) "

            self.assertEqual(result, expected,
                             f"\ninput = {repo_name}\nresult = {result}")

    def test_get_file_url(self):
        ref_name = 'commit'
        for repo_name in self.row_title_list:
            for file_path in self.column_title_list:
                # function under test
                result = self.table_writer.get_file_url(
                    repo_name, file_path, ref_name)

                expected_url = self.repo_url_lookup[repo_name]
                expected = self.get_expected_url(
                    expected_url, file_path, ref_name)

                self.assertEqual(expected, result)

    def test_get_cell_text(self):
        ref_name = 'commit'
        for repo_name in self.row_title_list:
            for file_path in self.column_title_list:

                result = self.table_writer.get_cell_text(
                    repo_name, file_path, ref_name=ref_name)

                expected_repo_url = self.repo_url_lookup[repo_name]
                expected_file_url = self.get_expected_url(
                    expected_repo_url, file_path, ref_name)
                expected = f'| [{self.d[repo_name][file_path]}]({expected_file_url}) '

                self.assertEqual(expected, result)


class TestHtmlLinkTableWriter(BaseTestTableWriterRepoLinks):
    def setUp(self):
        super().setUp()
        self.table_writer = progress.HtmlLinkTableWriter(self.d, self.row_title_list, 'test_HTML_link_table',
                                                         repo_list=self.repo_dict_list,
                                                         )

    def test_get_repo_url(self):
        for repo_name in self.row_title_list:
            result = self.table_writer.get_repo_url(repo_name)
            expected = self.repo_url_lookup[repo_name]
            self.assertEqual(result, expected,
                             f"\ninput = {repo_name}\nresult = {result}")

    def test_start_row(self):
        for repo_name in self.row_title_list:
            # function under test
            result = self.table_writer.start_row(repo_name)

            expected_name = repo_name
            expected_url = self.repo_url_lookup[repo_name]
            expected = f'<tr><td> <a href="{expected_url}">{expected_name}</a> '

            self.assertEqual(result, expected,
                             f"\ninput = {repo_name}\nresult = {result}")

    def test_get_file_url(self):
        ref_name = 'commit'
        for repo_name in self.row_title_list:
            for file_path in self.column_title_list:
                # function under test
                result = self.table_writer.get_file_url(
                    repo_name, file_path, ref_name)

                expected_url = self.repo_url_lookup[repo_name]
                expected = self.get_expected_url(
                    expected_url, file_path, ref_name)

                self.assertEqual(expected, result)

    def test_get_cell_text(self):
        ref_name = 'commit'
        for repo_name in self.row_title_list:
            for file_path in self.column_title_list:

                result = self.table_writer.get_cell_text(
                    repo_name, file_path, ref_name=ref_name)

                expected_repo_url = self.repo_url_lookup[repo_name]
                expected_file_url = self.get_expected_url(
                    expected_repo_url, file_path, ref_name)
                expected = f'</td><td> <a href="{expected_file_url}">{self.d[repo_name][file_path]}</a> '

                self.assertEqual(expected, result)


if "__main__" == __name__:
    unittest.main()
