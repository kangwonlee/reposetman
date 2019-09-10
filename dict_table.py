import os

import unique_list


class RepoTable(object):
    def __init__(self):
        # header row
        self.column = unique_list.unique_list()
        # table body
        self.index = {}

    def __getitem__(self, item):
        return self.index[item]

    def __iter__(self):
        for key in self.index:
            yield key

    def set_row_column(self, row, column, value):
        """

        :param row: row index
        :param column: column index
        :param value: to store in the self.index
        :return:
        """

        # for self.index header
        self.column.add(column)

        # if new row
        # TODO : consider using setdefault() of the dictionary
        if row not in self.index:
            self.add_row(row, column, value)
        else:
            # if new column
            if column not in self.index[row]:
                self.set_column_new(row, column, value)
            else:
                self.set_column_duplicate(row, column, value)

    def add_row(self, row, column, value):
        """

        :param row: row index
        :param column: column index
        :param value: to store in the self.index
        :return:
        """
        self.index[row] = {column: value}

    def set_column_new(self, row, column, value):
        """

        :param row: row index
        :param column: column index
        :param value: to store in the self.index
        :return:
        """
        self.index[row][column] = value

    def set_column_duplicate(self, row, column, value):
        """

        :param row: row index
        :param column: column index
        :param value: to store in the self.index
        :return:
        """
        msg = 'Overwrite attempt at [{row}][{column}]. current value = {current} new_value = {new}'.format(
            row=row, column=column, current=self.index[row][column], new=value)
        if self.index[row][column] != value:
            raise ValueError(msg)
        else:
            print(msg)

    def update(self, other):
        """
        Integrate other RepoTable

        :param RepoTable other:
        :return:
        """
        self.column.update(other.column)
        self.index.update(other.index)

    def get_sorted_row(self, column=' table'):
        """
        Get list of rows sorted in the order of column in argument
        """

        def key(row):
            # if point same, sort by repository name
            return (-self.index[row].get(column), row)

        rows = list(self.index.keys())
        rows.sort(key=key)

        return rows

    def is_backslash_in_header(self):
        return any(['\\' in column_title for column_title in self.column])


class TextTableWriter(object):
    # class variables
    ext = 'txt'
    col_sep = '\t'
    row_sep = '\n'

    # for each cell
    # to reuse get_cell_text() code
    cell_formatter = '{sep}{value}'

    def __init__(self, d, section, sorted_row=None,
                 filename_prefix='progress', path=os.curdir
                 ):
        """

        :param RepoTable d:
        :param str section: 'a' by default
        :param list(dict) repo_list: list of repository information dictionaries
        :param str filename_prefix: 'progress' by default
        :param str path: output path os.curdir by default
        :param str column_separator: between each column
        :param str row_separator: at the end of each row
        :return:
        """
        self.d = d
        self.section = section
        self.filename_prefix = filename_prefix
        self.path = path
        self.sorted_row = sorted_row

        # for header
        self.field_list = self.get_field_list()

    def write(self):
        """
        Top level method
        Constructor and then call this method
        """

        self.write_table(
            self.gen_rows()
        )
        return True

    def gen_rows(self):
        # header
        yield self.get_header_row()

        # row loop
        for repo_name in self.sorted_row:
            yield self.get_each_row(repo_name)

    def get_filename(self):
        # different file names for each section
        return os.path.join(
            self.path,
            "{prefix}_{section}.{ext}".format(
                prefix=self.filename_prefix,
                section=self.section,
                ext=self.ext,
            )
        )

    def write_table(self, table):

        # write table
        with open(self.get_filename(), 'w') as f:
            f.writelines(table)

    def get_field_list(self):
        field_list = list(self.d.column)
        field_list.sort()
        return field_list

    def get_header_row(self):
        # column title row
        first_line = ''

        for field in self.field_list:
            first_line += "%c%s" % (self.col_sep, field)

        first_line += self.row_sep

        return first_line

    def get_each_row(self, repo_name,):
        # title column
        this_line = self.start_row(repo_name)

        # column loop
        for field in self.field_list:
            this_line += self.get_cell_text(repo_name, field)
        # end of each row
        this_line += self.row_sep

        return this_line

    def start_row(self, repo_name):
        return '%s' % repo_name

    def get_cell_text(self, row_key, column_key):
        # This part may depend on the format : Plain text, MD, HTML, ...
        # for example
        # [tab]a[tab]b...

        return self.cell_formatter.format(
            sep=self.col_sep,
            value=str(self.d[row_key].get(column_key, ''))
        )


class MarkdownTableWriter(TextTableWriter):
    # class variables
    # TODO : more maintanable version
    ext = 'md'

    col_sep = '|'
    row_sep = ' |\n'

    cell_formatter = '{sep} {value} '

    def __init__(self, d, section, sorted_row,
                 filename_prefix='progress', path=os.curdir,
                 ):

        super(MarkdownTableWriter, self).__init__(d, section, sorted_row,
                                                  filename_prefix=filename_prefix, path=path,
                                                  )

        # '|   |  field1  |  field2  |  field3  |\n'
        # '|:--:|:----:|:----:|:----:|\n'

        # '|   |  field1  |  field2  |  field3 |\n'
        #  ^^
        self.header_first_row_header = f'{self.col_sep}  '
        # '|:--:|:----:|:----:|:----:|\n'
        #  ^^^
        self.header_second_row_header = f'{self.col_sep}:-'

        # '|   |  field1  |  field2  |  field3 |\n'
        #    ^^^^^      ^^^^^      ^^^^^
        self.header_first_col_sep = f'  {self.col_sep}  '
        # '|:--:|:----:|:----:|:----:|\n'
        #     ^^^^^^^^^^^^^^^^^^^^^
        self.header_second_col_sep = f'-:{self.col_sep}:---'

        # '|   |  field1  |  field2  |  field3 |\n'
        #                                     ^^^^
        # TODO : consider revising row_sep (need it?)
        self.header_first_row_sep = f'  {self.col_sep}\n'
        # '|:--:|:----:|:----:|:----:|\n'
        #                          ^^^^^
        # TODO : consider revising row_sep (need it?)
        self.header_second_row_sep = f'-:{self.col_sep}\n'

    def get_header_row(self):

        # to reuse gen_rows(), return two rows as one string
        first_line = self.header_first_row_header
        second_line = self.header_second_row_header

        for field in self.field_list:
            first_line += self.header_first_col_sep
            first_line += field

            second_line += self.header_second_col_sep

        first_line += self.header_first_row_sep
        second_line += self.header_second_row_sep

        assert first_line.count('|') == second_line.count('|')
        try:
            assert second_line.count(':') == (second_line.count('|') - 1) * 2
        except AssertionError as e:
            print('# | =', second_line.count('|'))
            print('# : =', second_line.count(':'))
            raise e

        header_row = first_line + second_line

        del first_line, second_line

        return header_row

    def start_row(self, repo_name):
        # first part of each row below header
        return self.cell_formatter.format(sep=self.col_sep, value=repo_name)


class MDlinkTableWriter(MarkdownTableWriter):
    """
    Markdown Tables with links to repositories
    """

    def __init__(self, d, section, sorted_row,
                 filename_prefix='progress', path=os.curdir,
                 repo_list=[]
                 ):

        super().__init__(d, section, sorted_row, filename_prefix, path)

        self.repo_list = repo_list

    def get_repo_url(self, repo_name):

        # TODO : consider adding a repo_url lookup table

        repo_url = False

        for repo_info_dict in self.repo_list:
            if repo_name == repo_info_dict['name']:
                repo_url = repo_info_dict.get('url', "")

        return repo_url

    def start_row(self, repo_name):
        # first part of each row below header

        repo_url = self.get_repo_url(repo_name)
        value = f"[{repo_name}]({repo_url})"

        # TODO : how to reuse code?
        #        (also in MarkdownTableWriter)

        return self.cell_formatter.format(sep=self.col_sep, value=value)

    def get_file_url(self, repo_name, file_path, ref='master'):
        repo_url = self.get_repo_url(repo_name)

        return f"{repo_url}/blob/{ref}/{file_path}"

    def get_cell_text(self, row_key, column_key, ref_name='master'):
        # This part may depend on the format : Plain text, MD, HTML, ...
        # for example
        # [tab]a[tab]b...

        # TODO : how to reuse the code more?

        value = self.d[row_key].get(column_key, '')

        if value and ' ' != column_key[0]:
            url_to_file = self.get_file_url(row_key, column_key, ref_name)
            value = f"[{value}]({url_to_file})"

        return self.cell_formatter.format(
            sep=self.col_sep,
            value=value,
        )


class HtmlTableWriter(MarkdownTableWriter):
    # class variables
    # TODO : more maintanable version
    ext = 'html'

    html_header = '<html>\n'
    html_footer = '</html>\n'

    style_definition = '<head>\n' \
                       '<style>\n' \
                       'table, th, td {\n' \
                       '    border: 1px solid black;\n' \
                       '}\n' \
        'th, td {text-align: center;}\n'\
        'tr:nth-child(even) {background-color: #f2f2f2;}\n'\
                       '</style>\n' \
                       '</head>\n'
    # Left-align Headings, https://www.w3schools.com/html/html_tables.asp
    # Striped Tables, https://www.w3schools.com/css/css_table.asp

    table_header = '<table>\n'
    table_footer = '</table>\n'

    row_header = '<tr>'
    row_footer = '</tr>\n'

    # for header row
    start_table_header = '<thead>\n'
    end_table_header = '</thead>\n'

    header_row_header = '<th>'
    header_row_footer = '</th>'

    header_col_sep = header_row_footer + header_row_header
    header_row_sep = header_row_footer + row_footer

    # rows below header
    start_table_body = '<tbody>\n'
    end_table_body = '</tbody>\n'

    item_header = '<td>'
    item_footer = '</td>'

    col_sep = item_footer + item_header
    row_sep = item_footer + row_footer

    def gen_rows(self):
        # html
        yield self.html_header

        # define table style
        yield self.style_definition

        # table
        yield self.table_header

        # reuse superclass code
        # https://stackoverflow.com/questions/11197186/how-do-i-yield-results-from-a-nested-python-generator-function
        for item in super(HtmlTableWriter, self).gen_rows():
            yield item

        yield self.table_footer
        # table end

        yield self.html_footer
        # html end

    def get_header_row(self):

        # header column
        header_column = '{row_header}{item_header} {sep}'.format(
            row_header=self.row_header,
            item_header=self.header_row_header,
            sep=self.header_col_sep,
        )

        # column loop
        body_columns = self.header_col_sep.join(
            [
                ' {item:s} '.format(item=column_key)
                for column_key in self.field_list
            ]
        )

        return '{start_header}{header_column}{body_columns}{footer}{end_header}'.format(
            start_header=self.start_table_header,
            header_column=header_column,
            body_columns=body_columns,
            footer=self.header_row_sep,
            end_header=self.end_table_header,
        )

    def start_row(self, repo_name):
        # header column
        # assume </td> follows
        return '{row_header}{item_header} {repo_name} '.format(
            row_header=self.row_header, item_header=self.item_header,
            repo_name=repo_name
        )


class HtmlLinkTableWriter(HtmlTableWriter):
    """
    Markdown Tables with links to repositories
    """

    def __init__(self, d, section, sorted_row,
                 filename_prefix='progress', path=os.curdir,
                 repo_list=[]
                 ):

        super().__init__(d, section, sorted_row, filename_prefix, path)

        self.repo_list = repo_list

    def get_repo_url(self, repo_name):

        # TODO : consider adding a repo_url lookup table
        # TODO : how to reuse the code more?
        #        (also in MDlinkTableWriter)

        repo_url = False

        for repo_info_dict in self.repo_list:
            if repo_name == repo_info_dict['name']:
                repo_url = repo_info_dict.get('url')

        return repo_url

    def start_row(self, repo_name):
        # first part of each row below header

        # TODO : how to reuse the code more?
        #        (also in MDlinkTableWriter)

        repo_url = self.get_repo_url(repo_name)
        value = f'<a href="{repo_url}">{repo_name}</a>'

        return super().start_row(value)

    def get_file_url(self, repo_name, file_path, ref='master'):

        # TODO : how to reuse the code more?
        #        (also in MDlinkTableWriter)

        repo_url = self.get_repo_url(repo_name)

        return f"{repo_url}/blob/{ref}/{file_path}"

    def get_cell_text(self, row_key, column_key, ref_name='master'):
        # This part may depend on the format : Plain text, MD, HTML, ...
        # for example
        # [tab]a[tab]b...

        # TODO : how to reuse the code more?

        value = self.d[row_key].get(column_key, '')

        if str(value) and ' ' != column_key[0]:
            url_to_file = self.get_file_url(row_key, column_key, ref_name)
            value_with_link = f'<a href="{url_to_file}">{value}</a>'
            value = value_with_link

        return self.cell_formatter.format(
            sep=self.col_sep,
            value=value,
        )
