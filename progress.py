"""

Progress report generator

To automatically generate progress reports over multiple repositories

Author : KangWon LEE

Year : 2018

"""


import ast
import configparser
import fractions
import itertools
import multiprocessing
import os
import re
import sys
import time
import tokenize

import git
import read_python
import regex_test as ret
import repo_path
import timeit
import unique_list


# https://stackoverflow.com/questions/1681836/how-to-debug-a-memoryerror-in-python-tools-for-tracking-memory-use
def get_size_of(one, name):
    # may need to investigate MemoryError
    print('** get_size_of({name}) = {size} **'.format(name=name, size=sys.getsizeof(one)))


def get_type(arg):
    # to obtain the name of the type:
    # https://stackoverflow.com/questions/510972/getting-the-class-name-of-an-instance-in-python
    return type(arg).__name__


class ProgressReportBuilder(object):
    """

    Umbrella class of progress report generator
    get project ID's
    update repositories
    initialize big dictionary
    call visit_path() thru os.walk()
    write table

    input file name : in progress.cfg

    """
    def __init__(self, config_filename=False):
        self.config = configparser.ConfigParser()

        if not config_filename:
            config_filename = 'progress.cfg'

        self.config.read(config_filename)        

        # compile regex here not to repeat later
        self.re_git_log = RepoEvalCountCommit.get_regex_parse_git_log()

    def get_section_list(self):
        op_key = 'operation'
        if 'sections' not in self.config[op_key]:
            if 'section' not in self.config[op_key]:
                raise IOError('Unable to find section list from the config file')
            else:
                sections_txt = self.config[op_key]['section']
        else:
            sections_txt = self.config[op_key]['sections']

        # to obtain the list from text
        # https://stackoverflow.com/questions/335695/lists-in-configparser
        return ast.literal_eval(sections_txt)

    def run(self):
        return tuple(
            map(
                self.process_section, self.get_section_list()
            )
        )

    @timeit.timeit
    def process_section(self, section):
        """
        Clone or pull from remote repositories
        For each repository,
            visit all folders and evaluate all files

        :param configparser.ConfigParser config:
        :param regex re_git_log:
        :param str section: 'a' | 'b' | 'c'
        :return:
        """
        # get repository url list
        repo_url_list = ret.get_github_url_list(self.config[section]['list'].strip())
        print('process_section() : # repositories =', len(repo_url_list))

        # clone or update student repositories
        repo_list = ret.clone_or_pull_repo_list(
            repo_url_list, 
            section_folder=self.config[section]['folder'], 
            b_update_repo=('True' ==self.config['operation']['update_repo'].strip())
        )

        results = {}

        # evaluate repositories within the section
        if 'True' == self.config[section]['count_commits']:
            call_commit_count(self.config, section, repo_list, results) 
        if 'True' == self.config[section]['pound_count']:
            call_pound_count(self.config, section, repo_list, results)
        if 'True' == self.config[section]['run_all']:
            call_run_all(self.config, section, repo_list, results) 

        return results


@timeit.timeit
def main(argv=False):
    """

    main function of progress report generator
    get project ID's
    update repositories
    initialize big dictionary
    call visit_path() thru os.walk()
    write table

    input file name : in progress.cfg

    """
    # https://docs.python.org/3/library/configparser.html
    config = configparser.ConfigParser()
    if argv:
        config_filename = argv[0]
    else:
        config_filename = 'progress.cfg'
    config.read(config_filename)

    '''
    project id loop : for all project id's

        go in

        get list

        if doesn't start with '.'

            if file, get log

                # commits

                # begin ~ end

                # average commit interval
    '''

    # compile regex here not to repeat later
    re_git_log = RepoEvalCountCommit.get_regex_parse_git_log()

    def gen_arg_process_section(section_list):
        """
        generator for process_section()
        """
        # (star) map function requires a sequence of arguments
        # use yield hopefully to save memory and time
        for section in section_list:
            yield config, re_git_log, section

    # http://n-s-f.github.io/2016/12/23/starmap-pattern.html
    return tuple(
        itertools.starmap(
            process_section,
            gen_arg_process_section(get_section_list(config))
        )
    )


def get_section_list(config):
    op_key = 'operation'
    if op_key in config:
        if 'sections' not in config[op_key]:
            if 'section' not in config[op_key]:
                raise IOError('Unable to find section list from the config file')
            else:
                sections_txt = config[op_key]['section']
        else:
            sections_txt = config[op_key]['sections']

    else:
        raise ValueError(f"key 'operation' missing\nAvailable keys : {list(config.keys())}")

    # to obtain the list from text
    # https://stackoverflow.com/questions/335695/lists-in-configparser
    return ast.literal_eval(sections_txt)


@timeit.timeit
def process_section(config, re_git_log, section):
    """
    Clone or pull from remote repositories
    For each repository,
        visit all folders and evaluate all files

    :param configparser.ConfigParser config:
    :param regex re_git_log:
    :param str section: 'a' | 'b' | 'c'
    :return:
    """
    # get repository url list
    repo_url_list = ret.get_github_url_list(config[section]['list'].strip())
    print('process_section() : # repositories =', len(repo_url_list))

    # clone or update student repositories
    repo_list = ret.clone_or_pull_repo_list(
        repo_url_list, 
        section_folder=config[section]['folder'], 
        b_update_repo=('True' ==config['operation']['update_repo'].strip())
    )

    results = {}

    # evaluate repositories within the section
    if 'True' == config[section]['count_commits']:
        call_commit_count(config, section, repo_list, results) 
    if 'True' == config[section]['pound_count']:
        call_pound_count(config, section, repo_list, results)
    if 'True' == config[section]['run_all']:
        call_run_all(config, section, repo_list, results) 

    return results

def call_run_all(config, section, repo_list, results):
    run_all_txt, run_all_md, run_all_html = run_all(config, section, repo_list)
    results.update({
        'run_all':
            {
            'txt': run_all_txt, 
            'md': run_all_md, 
            'html': run_all_html
            }
    }) 


def call_pound_count(config, section, repo_list, results):
    pound_reports = pound_count(config, section, repo_list)
    results.update({
        'pound_counts':
            {
                'txt': pound_reports[0],
                'md': pound_reports[1],
                'html': pound_reports[2],
            }
    })


def call_commit_count(config, section, repo_list, results):
    """
    Call count commits() and update results dict

    :param configparser.Configparser config : program configurations
    :param str section : usually '{course id}{yr}{a/b/c}', '{course id}{yr}{a/b/c}', or '{course id}{yr}{a/b/c}'
    :param list(dict) repo_list : list of repository_information_dictionary
    :param dict results: contains dictionary of results
    """
    commit_count_txt, commit_count_md, commit_count_html = count_commits(config, section, repo_list) 
    results.update({
        'count_commits':
            {
            'txt': commit_count_txt, 
            'md': commit_count_md, 
            'html': commit_count_html
            }
    }) 


@timeit.timeit
def count_commits(config, section, repo_list):
    """
    Count commits of each file fromt eh section
    """
    # git log interval settings
    after = config[section].get('after', None)
    before = config[section].get('before', None)
    exclude_email_tuple = tuple(ast.literal_eval(config['operation']['initial_email_addresses']))

    commit_counter = RepoEvalCountOneCommitLog(after, before, exclude_email_tuple)
    commit_count = commit_counter.eval_repo_list(repo_list)

    # if the header row seems to include '\' character in the header row
    if commit_count.is_backslash_in_header():
        print(
            "'\\' in column title row.\n" \
            'Could you please run following git command to change its configuration?\n' \
            '\n'\
            '    git config core.quotepath false\n'\
            '\n'\
            'or\n'\
            '\n'\
            '    git config --global core.quotepath false\n'\
            '\n'
        )

    # sort with total
    # TODO : more adaptive argument?    
    sorted_row = commit_count.get_sorted_row(' total')

    # write tables
    commit_count_txt, commit_count_md, commit_count_html = write_tables(
        section, 
        repo_list,
        commit_count, 
        filename_prefix='commit_count',
        sorted_row=sorted_row
    )

    return commit_count_txt, commit_count_md, commit_count_html


@timeit.timeit
def write_tables(section, repo_list, table, filename_prefix, sorted_row=None):

    #if sorted_row not given, make one from repo_list
    if sorted_row is None:
        # TODO : Possibly repeating too frequently
        sorted_row = tuple([repo_dict['name'] for repo_dict in repo_list])

    txt_table_writer = TextTableWriter(table, section, sorted_row, filename_prefix=filename_prefix)
    finished_txt_table = txt_table_writer.write()

    md_table_writer = MarkdownTableWriter(table, section, sorted_row, filename_prefix=filename_prefix)
    finished_md_table = md_table_writer.write()

    html_table_writter = HtmlTableWriter(table, section, sorted_row, filename_prefix=filename_prefix)
    finished_html_table = html_table_writter.write()

    return finished_txt_table, finished_md_table, finished_html_table


@timeit.timeit
def run_all(config, section, repo_list):
    """
    Run (almost) all .py files from the section
    """

    all_runner = RepoEvalRunEachSkipSome(config['operation']['python_path'])
    all_outputs = all_runner.eval_repo_list(repo_list)
    print('run_all() : finished eval_repo_list()')

    # repository names in order
    sorted_row = all_outputs.get_sorted_row(' total')

    # write tables
    run_all_txt, run_all_md, run_all_html = write_tables(
        section, 
        repo_list, 
        all_outputs,
        filename_prefix='run_all',
        sorted_row=sorted_row,
    )

    return run_all_txt, run_all_md, run_all_html


@timeit.timeit
def pound_count(config, section, repo_list):
    """
    count # comments of the section
    """

    pound_counter = RepoEvalPoundByteCounterExcludingRef()
    pound_numbers = pound_counter.eval_repo_list(repo_list)
    print('pound_count() : finished eval_repo_list()')

    # sort with total
    # TODO : more adaptive argument?    
    sorted_row = pound_numbers.get_sorted_row(' total')

    # write tables
    pound_count_txt, pound_count_md, pound_count_html = write_tables(
        section, 
        repo_list, 
        pound_numbers, 
        filename_prefix='pound_count',
        sorted_row=sorted_row
    )

    return pound_count_txt, pound_count_md, pound_count_html


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


class RepoEval(object):
    """
    To evaluate one repository
    """

    def __init__(self, ):
        # table of repository names in rows and relative path/file names in columns
        self.table = RepoTable()
        self.repo_name = None
        self.repo_path = None

    def eval_repo_list(self, repo_list,  b_multiprocessing = True):
        """

        :param list(dict) repo_list:
        :param bool b_multiprocessing:
        :return:
        """
        # integrate evaluation results
        # multiprocessing args are different from student_dict here
        # initialize student dictionary

        student_dict = RepoTable()

        if b_multiprocessing:
            p = multiprocessing.Pool()

            # visit all folders
            # p.map() or map() requires all members' instance on the memory at the same time
            # "p.imap() returns an iterator"
            # https://stackoverflow.com/questions/25429799/memory-error-with-multiprocessing-in-python
            for result_dict in p.imap_unordered(self.eval_repo, enumerate(repo_list)):
                student_dict.update(result_dict)

            p.close()
            p.join()
        else:
            # for debugging, single processing could be easier
            for k_repo in enumerate(repo_list):
                result_dict = self.eval_repo(k_repo)
                student_dict.update(result_dict)

        return student_dict

    def eval_repo(self, k_repo):
        """
        Evaluate one repository

        :return:
        """
        start_time_sec = time.time()

        k, repo = k_repo
        # to explicitly pass repository name
        # update repo information
        self.repo_name = repo['name']
        self.repo_path = repo['path']
        # to obtain the name of the class:
        # https://stackoverflow.com/questions/510972/getting-the-class-name-of-an-instance-in-python
        print('{repoEval}.eval_repo({k:2d}) start: name={name}'.format(repoEval=self.get_class_name(), k=k, name=repo['name']))

        for path_dirs_files in os.walk(self.repo_path):
            self.eval_folder_in_repo(path_dirs_files[0], path_dirs_files[2])

        print('{repoEval:s}.eval_repo({k:2d}) end: name={name} ({time:g} sec)'.format(
                k=k, name=repo['name'], time=(time.time() - start_time_sec),
                repoEval=self.get_class_name()
            ))
        return self.table

    def eval_folder_in_repo(self, path, filename_list):

        """
        call back function for os.path.walk()
        filter if path interesting (.git, xcode, ...)
        go to the path
        run through namelist loop
        return to the original path
        """

        if self.is_ignore_path(path):
            pass
        else:

            # cd. return is original path
            org_path = repo_path.cd(os.path.abspath(path))

            # print('-'*80)
            # print(os.path.abspath(os.curdir))
            # print('-'*80)

            for filename in filename_list:
                self.eval_file(path, filename, self.repo_name)

            os.chdir(org_path)

    def eval_file(self, path, filename, repo_name):
        isfile = os.path.isfile(filename)

        if isfile and (not self.is_ignore_filename(filename)):
            evaluation = self.eval_file_base(filename)

            # path in repository for column key
            rel_path = os.path.relpath(path, self.repo_path)
            column_key = '/'.join((rel_path, filename)).lower()

            self.table.set_row_column(repo_name, column_key, evaluation)

    @staticmethod
    def is_ignore_path(path):
        # check if ignore
        # TODO : more flexible ignore list
        is_dot_git_path = ".git" in path
        is_xcode_path = "python.xcodeproj" in path
        is_pycharm_path = '.idea' in path
        is_vscode_path = '.vscode' in path
        is_pycache_path = '__pycache__' in path
        is_ipynb_checkpoints_path = '.ipynb_checkpoints' in path
        b_ignore = any((is_dot_git_path, is_xcode_path, is_pycharm_path, is_vscode_path, is_pycache_path, is_ipynb_checkpoints_path))
        return b_ignore

    def is_ignore_filename(self, filename):
        return any((
            self.is_readme(filename), 
            self.is_dot_git(filename),
        ))

    @staticmethod
    def is_readme(filename):
        return filename.startswith('README')
    
    @staticmethod
    def is_dot_git(filename):
        return '.git' == filename

    def eval_file_base(self, filename):
        """
        Override this

        :param str filename:
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def is_python(filename):
        return filename.endswith('.py')

    def is_readable(self, filename):
        try:
            result = ret.read_utf_or_cp(filename)
        except UnicodeDecodeError:
            print('%s : unable to read %s' % (self.get_class_name(), os.path.join(os.getcwd(), filename)))
            result = ''

        return result        

    def get_class_name(self):
        # to obtain the name of the class:
        # https://stackoverflow.com/questions/510972/getting-the-class-name-of-an-instance-in-python
        return type(self).__name__


class RepoEvalCountCommit(RepoEval):
    """
    To count number of commits per each file
    """

    def __init__(self, re_git_log):
        super(RepoEvalCountCommit, self).__init__()
        self.re_git_log = re_git_log

    @staticmethod
    def get_regex_parse_git_log():
        """
        make regular expression pattern to identify date within each commit record from 'git log'
        """

        '''
        commit fc8fb8e9b3a5174303d3733e1646d53a3dc5f638
        Author: naverdev <naverdev@naver.com>
        Date:   Tue Mar 4 06:58:15 2014 +0000
        
            initialized Git repository    
        '''
        
        # regular expression pattern
        # https://stackoverflow.com/questions/587345/regular-expression-matching-a-multiline-block-of-text
        pattern_string_1 = r"^commit\s+(?P<sha>.+)\nAuthor:\s+(?P<author>.+)\nDate:\s+(?P<date>.+)\n"

        return re.compile(pattern_string_1, re.M | re.I)

    def eval_file_base(self, filename):
        return self.count_file_commits(filename)

    def count_file_commits(self, filename):
        # TODO : one commit including multiple files
        # TODO : benefit of get_git_log_dict_list as one of the methods
        return len(self.get_git_log_dict_list(filename))

    @staticmethod
    def get_git_cmd(filename):
        # this part became a method to apply various git log commands more easily
        return '''log --follow "{filename}"'''.format(filename=filename)

    def get_dict_list_from_git_log(self, git_log_msg):
        # extracts information fom the git log text
        # in the form of a list of dictionaries
        return [match.groupdict() for match in self.re_git_log.finditer(git_log_msg)]

    def get_git_log_dict_list(self, filename):
        """

        :param str filename:file under evaluation
        :return: list(dict)
        """
        # git log with follow rename
        # TODO : consider using -C option instead of changing folders
        # TODO : as a method of the evaluator class?
        # TODO : pair git command & regex pattern ?

        # some file name may contain space
        git_cmd_string = self.get_git_cmd(filename)

        # other candidates
        # ref : git log help
        # git log --format="%h, %ai, %an %ae '%s'" --numstat --after=<date> --before=<date>

        # run git command
        git_log_msg = git.git(git_cmd_string, bVerbose=False)

        # extract information from git log message and return its list
        return self.get_dict_list_from_git_log(git_log_msg)


class RepoEvalCountOneCommitLog(RepoEval):
    """
    Obtain information on all files from one git log
    """
    def __init__(self, after=None, before=None, exclude_email_tuple=[], 
            commit_split_token='__reposetman_new_commit_start__',
            field_split_token='__reposetman_field_split__',):
        """
        One commit log from one repository

        :param str after : commits after this date and time
        :param str before : commits before this date and time
        :param list exclude_email_tuple : ignore commits with these email addresses
        :param str commit_split_token : identifies start point of a new token

        """
        super(RepoEvalCountOneCommitLog, self).__init__()
        self.after = after
        self.before = before
        self.exclude_email_tuple = exclude_email_tuple
        self.commit_split_token = commit_split_token
        self.field_split_token = field_split_token

    def get_git_cmd(self, after=None, before=None):
        # To let git generate string compatible with python ast as much as possible
        # Author name may include \' character so use triple quotes
        # For time format, this works : 'yyyy-mm-dd hh:mm' (local time)
        # Other date options are also available : --since=2.weeks

        # not easy to handle if too long
        cmd_list = [
            'log', # must be the first
            '--encoding=utf-8',
            '--numstat',
            '--all',
            f"""--pretty=format:{self.commit_split_token}%H{self.field_split_token}%an{self.field_split_token}%ae{self.field_split_token}%ad{self.field_split_token}%s""",
        ]

        if after:
            cmd_list.append('--after="{after}"'.format(after=after))
        elif self.after:
            cmd_list.append('--after="{after}"'.format(after=self.after))
        
        if before:
            cmd_list.append('--before="{before}"'.format(before=before))
        elif self.before:
            cmd_list.append('--before="{before}"'.format(before=self.before))

        return cmd_list

    def eval_repo(self, k_repo):
        """
        Evaluate one repository
        """        
        start_time_sec = time.time()

        k, repo = k_repo
        # to explicitly pass repository name
        # update repo information
        self.repo_name = repo['name']
        self.repo_path = repo['path']
        # to obtain the name of the class:
        # https://stackoverflow.com/questions/510972/getting-the-class-name-of-an-instance-in-python
        print('{repoEval}.eval_repo({k:2d}) start: name={name}'.format(repoEval=self.get_class_name(), k=k, name=repo['name']))

        path_org = os.getcwd()
        os.chdir(self.repo_path)

        git_log__err_msg = git.git_common_list(self.get_git_cmd(), b_verbose=False)

        os.chdir(path_org)

        git_log = git_log__err_msg[0]

        column_set, eval_dict = self.convert_git_log_to_table(git_log)

        # update evaluation result
        for column in column_set:
            self.table.set_row_column(self.repo_name, column, eval_dict[column])

        # to obtain the name of the class:
        # https://stackoverflow.com/questions/510972/getting-the-class-name-of-an-instance-in-python
        print('{repoEval:s}.eval_repo({k:2d}) end: name={name} ({time:g} sec)'.format(
                k=k, name=repo['name'], time=(time.time() - start_time_sec),
                repoEval=self.get_class_name()
            ))
        return self.table

    def convert_git_log_to_table(self, git_log):
        # column titles == unique file names in the git log
        column_set = unique_list.unique_list()

        commits_list = []
        eval_dict = {}

        # one big git log -> list of commits
        git_log_split_blocks = git_log.split(self.commit_split_token)

        # remove empty string
        # TODO : consider git_log.strip(self.commit_split_token).split(self.commit_split_token) 
        #        to avoid a special case
        if not git_log_split_blocks[0]:
            del git_log_split_blocks[0]

        temporary_file_list = unique_list.unique_list(['no commit yet'])

        last_commit_dict = {'subject':'no commit yet'}

        # commit loop
        for git_log_block in git_log_split_blocks:
            # TODO : refactor into a method?

            # one commit example:
            # < commit information >
            # <int add>    <int del>    <filename 0>
            # <int add>    <int del>    <filename 1>
            # <int add>    <int del>    <filename 2>
            # <int add>    <int del>    <filename 3>
            # <blank line>

            git_log_lines = git_log_block.splitlines()

            # using git log output as input to python
            last_commit_dict = self.get_commit_dict(git_log_lines[0])

            if isinstance(last_commit_dict, (str, bytes)):
                # if double quote is wrapping the output from the git log
                last_commit_dict = self.get_commit_dict(git_log_lines[0].strip('"'))

            if isinstance(last_commit_dict, (str, bytes)):
                # if still a str or bytes, try again
                last_commit_dict = self.get_commit_dict(last_commit_dict)

            assert isinstance(last_commit_dict, dict), f"git_log_lines[0] = {repr(git_log_lines[0])}\n" \
                f"convert_git_log_to_table(): last_commit_dict = {last_commit_dict}" \
                f"convert_git_log_to_table(): isinstance(last_commit_dict, dict) = {isinstance(last_commit_dict, dict)}" \
                f"convert_git_log_to_table(): type(last_commit_dict) = {type(last_commit_dict)}"

            # filer using email address
            # TODO : consider refactoring into a function
            if last_commit_dict['email'] in self.exclude_email_tuple:
                last_commit_dict = {}
                continue

            # keep note of commits
            commits_list.append(last_commit_dict)

            # reset storage for 'files in commit'
            temporary_file_list = unique_list.unique_list()

            # process file list
            for line in git_log_lines[1:]:
                # lines below the new commit
                line_strip = line.strip()

                if line_strip:
                    # a file in the last_commit_dict

                    # get path/filename
                    add__delete__key = line_strip.split()
                    column_key = add__delete__key[2]

                    path, filename = os.path.split(column_key)
                    # check ignore list
                    if not (self.is_ignore_path(path) or self.is_ignore_filename(filename)):
                        # if n files in one commit, evaluation would be 1/n

                        # TODO : simplify data structures
                        # for header of the table
                        column_set.add(column_key)

                        # to count the number of
                        temporary_file_list.add(column_key)

            # end of files list
            if temporary_file_list:
                point = fractions.Fraction(1, len(temporary_file_list))

                # build commit count table
                # loop over files in commit
                for files_in_commit in temporary_file_list:
                    eval_dict[files_in_commit] = eval_dict.get(files_in_commit, 0) + point

                # if it is still not a dict
                if isinstance(last_commit_dict, str):
                    # try to convert it again
                    print(f'last_commit_dict = {repr(last_commit_dict)}')
                    last_commit_dict = ast.literal_eval(last_commit_dict)
                    if not isinstance(last_commit_dict, dict):
                        raise ValueError(f'last_commit_dict = {repr(last_commit_dict)}')
                last_commit_dict['files'] = temporary_file_list
            else:
                print(f'\n{self.get_class_name()}.convert_git_log_to_table() : end of file list but temporary_file_list empty')
                print(f'line = {line}')
                print('last_commit_dict =', repr(last_commit_dict))

        # total number of commits
        # to make it the first element
        # Sorting feature may use this feature
        column_key = ' total'
        column_set.add(column_key)
        eval_dict[column_key] = len(commits_list)

        return column_set, eval_dict

    def filter_commit_list(self, commits_list):
        # remove if email is in exclude list
        for k in range((len(commits_list) - 1), -1, -1):
            if commits_list[k]['email'] in self.exclude_email_tuple:
                del commits_list[k]

        for c_dict in commits_list:
            assert c_dict['email'] not in self.exclude_email_tuple, f"{c_dict['email']} in {self.exclude_email_tuple}"
            assert '.travis.yml' not in c_dict['files'], f".travis.yml in {c_dict}\n" \
                f"len(c_dict['files']) = {len(c_dict['files'])}\n" \
                f"c_dict['files'] = {c_dict['files']}\n" \
                f"'a' in c_dict['files'] = {'a' in c_dict['files']}\n" \
                f"'.travis.yml' in c_dict['files'] = {'.travis.yml' in c_dict['files']}"

    def get_commit_dict(self, line):

        fields = line.split(self.field_split_token)

        if 5 == len(fields):
            last_commit_dict = {
                'sha': fields[0],
                'author': fields[1],
                'email': fields[2],
                'date': fields[3],
                'subject': fields[4],
            }
        else:
            raise ValueError(
                    f'len(fields) == {len(fields)}\n'
                    f'line = {line}\n'
                    f'fields = {fields}\n'
            )

        return last_commit_dict

    @staticmethod
    def replace_in_subject(line, old_str, new_str):
        # use signature to locate start of subject
        i_subject_start = line.find("'subject': u'''")
        i_subject_offset = i_subject_start + 15

        subject = line[i_subject_offset:-4]

        # replace """ within the subject line
        new_subject = subject.replace(old_str, new_str)

        # assemble a new line
        new_line = line[:i_subject_offset] + new_subject + "'''}"

        return new_line


class RepoEvalPoundLineCounter(RepoEval):
    """
    To count # comments
    """

    # TODO : what if a student comments using triple quotes?
    def __init__(self):
        super(RepoEvalPoundLineCounter, self).__init__()

    def eval_file_base(self, filename):
        if not self.is_python(filename):
            result = 'N/A'
        else:
            txt = self.is_readable(filename)

            if not txt:
                result = {'readable': False}
            else:
                with open(filename, encoding='utf-8') as file_object:
                    comments_list = self.get_comments_list_from_readline(file_object.readline, filename=filename)
                result = self.get_points_from_comments_list(comments_list)
        return result

    @staticmethod
    def get_points_from_comments_list(comments_list):
        return len(comments_list)

    def get_comments_list_from_readline(self, readline, filename=None):
        return read_python.get_comments_list_from_readline(readline, filename=filename)

    def eval_repo(self, k_repo):
        """
        Find total number of comment lines
        """
        super(RepoEvalPoundLineCounter, self).eval_repo(k_repo)

        repo_name = k_repo[1]['name']

        # add a representative number
        self.table.set_row_column(repo_name, ' total', self.get_total(repo_name))

        return self.table

    def get_total(self, repo_name):
        """
        count total number of comment lines in one repository
        """
        total = 0

        # column loop
        for field in self.table.index[repo_name].keys():
            # it could be 'N/A'
            if isinstance(self.table[repo_name][field], (int, float)):
                total += self.table[repo_name][field]

        return total


class RepoEvalPoundByteCounter(RepoEvalPoundLineCounter):
    """
    Count bytes of pound comments
    """

    def get_points_from_comments_list(self, comments_list, b_verbose=False):
        # initialize file comment
        points = 0
        for comment in comments_list:
            # line point
            # TODO : how to encourage more desirable practice?
            # TODO : remove "baseline" comments
            point = self.get_line_point(comment)
            if b_verbose and point:
                print(point, comment)

            points += point

        return points

    @staticmethod
    def get_line_point(comment):
        return len(comment.strip('#').strip())


class RepoEvalPoundByteCounterExcludingRef(RepoEvalPoundByteCounter):
    reference_cfg_filename = 'reference.cfg'
    def __init__(self):
        super(RepoEvalPoundByteCounterExcludingRef, self).__init__()

        if os.path.exists(self.reference_cfg_filename):
            self.comments_ref = unique_list.unique_list()
            self.config_ref = configparser.ConfigParser()
            self.config_ref.read(self.reference_cfg_filename)

            reference_comment_filename = self.config_ref['operation']['comment_output_file']

            with open(reference_comment_filename, 'r', encoding='utf-8') as f_in:
                for line in f_in:
                    self.comments_ref.add(line.strip())

        else:
            self.init_reference_cfg_file()

    def init_reference_cfg_file(self):
        """
        Initialize reference config file and raise error
        """
        config_ref = configparser.ConfigParser()
        #sample cfg file
        r'''
        [operation]
        folder=data\ref
        comment_output_file=reference_comment.txt
        [urls]
        a=https://github.com/<github id>/<repository a name>
        b=https://github.com/<github id>/<repository b name>
        c=https://github.com/<github id>/<repository c name>
        [commits]
        a=<hash value of reference commit in repo a>
        b=<hash value of reference commit in repo b>
        c=<hash value of reference commit in repo c>
        '''
        config_ref['operation'] = {
            # will clone reference repositories to this folder
            'folder': os.path.join('data', 'ref'),
            # will write sample comment set to this file
            'comment_output_file' : 'reference_comment.txt',
        }
        config_ref['urls'] = {
            # urls of the reference repositories
            'a':'reference repository a url here',
            'b':'reference repository b url here',
            'c':'reference repository c url here',
        }
        config_ref['commits'] = {
            # hashes of reference commits here
            'a':'reference repository a base hash here',
            'b':'reference repository b base hash here',
            'c':'reference repository c base hash here',
        }

        with open(self.reference_cfg_filename, 'w') as ref_cfg_file:
            config_ref.write(ref_cfg_file)

        raise FileNotFoundError(f'please configure {self.reference_cfg_filename}, run reference.py, and restart')

    def get_line_point(self, comment, b_verbose=False):
        if comment.strip() not in self.comments_ref:
            if b_verbose: 
                print(comment)
            point = super(RepoEvalPoundByteCounterExcludingRef, self).get_line_point(comment)
        else:
            point = 0
        return point


class RepoEvalRunEach(RepoEval):
    def __init__(self, python_path):
        super(RepoEvalRunEach, self).__init__()
        self.python_path = python_path

    def eval_file_base(self, filename):
        if not self.is_python(filename):
            result = 'N/A'
        else:
            result = self.run_script(filename)
        return result

    def check_grammar(self, filename):
        # https://stackoverflow.com/questions/4284313/how-can-i-check-the-syntax-of-python-script-without-executing-it
        # some file names may contain space

        python_cmd_list = [self.python_path, '-m', 'py_compile', filename]

        msgo, msge = git.run_command(python_cmd_list)

        # as run_command() is happening within a separated subprocess, try except may not catch the exception from the file
        if 'FileNotFoundError' in msge:
            print('check_grammar() : unable to find file =', filename)
            print('check_grammar() : os.getcwd() =', os.getcwd())
            print('check_grammar() : python_cmd =', python_cmd_list)

        result = {'grammar pass': not (msgo or msge)}

        # free memory after use
        del msgo, msge

        return result

    def eval_repo(self, k_repo, b_verbose=False):
        """
        Find total number of comment lines
        """
        super(RepoEvalRunEach, self).eval_repo(k_repo)

        repo_name = k_repo[1]['name']

        total = self.get_total(repo_name)

        self.table.set_row_column(repo_name, ' total', total)

        if b_verbose:
            print("{class_name}.eval_repo(): d[{repo_name}][' total']={value}".format(
                class_name=self.get_class_name(),
                repo_name=repo_name,
                value=self.table[repo_name][' total']
            ))

        return self.table

    def run_script(self, filename, arguments='test.txt b.txt c.txt'):

        # some file names may contain space
        python_cmd_list = [self.python_path, filename]
        if isinstance(arguments, str):
            python_cmd_list += arguments.split()
        elif isinstance(arguments, list):
            python_cmd_list += arguments
        else:
            raise NotImplementedError(msg='type of arguments = %s' % type(arguments))

        # print('RepoEvalRunEach.run_script() : cwd = ', os.getcwd())
        # print('RepoEvalRunEach.run_script() : python_cmd = ', python_cmd)

        # subprocess.Popen() needs bytes as input
        msgo, msge = self.run_script_input(python_cmd_list)
        if 'Error' in msge:
            # to help debugging
            # present info only if exception happens
            print('{type:s}.run_script() : cwd = {cwd}'.format(type=self.get_class_name(), cwd=os.getcwd()))
            print('{type:s}.run_script() : python_cmd = {cmd!s}'.format(type=self.get_class_name(), cmd=python_cmd_list))
            print('{type:s}.run_script() : error message = {msge}'.format(type=self.get_class_name(), msge=msge))

            # If the .py script cannot find a file, present list of available files
            # to help improvement
            if 'FileNotFoundError:' in msge:
                print('{type:s}.run_script() : available files = {files}\n'.format(type=self.get_class_name(), 
                    files=str(os.listdir())
                ))

        # else:
        #     print('RepoEvalRunEach.run_script() : {cmd} OK'.format(cmd=python_cmd))

        result = {'stdout': len(msgo.strip()), 'stderr': len(msge.strip())}

        # explicitly delete temporary variables to save memory
        del python_cmd_list[:]
        del msgo, msge, python_cmd_list

        return result

    def get_total(self, repo_name, b_verbose=False):
        """
        Representative number on outputs and errors
        """
        total = 0

        # TODO : better ways to present status

        # column loop
        for field in self.table.index[repo_name].keys():
            # ignore 'N/A'
            if isinstance(self.table[repo_name][field], dict):

                # ran program
                if 'stdout' in self.table[repo_name][field]:

                    if self.table[repo_name][field]['stdout']:
                        total += 1

                    if self.table[repo_name][field]['stderr']:
                        total += -1

                # just checked grammar
                elif 'grammar pass' in self.table[repo_name][field]:

                    if self.table[repo_name][field]['grammar pass']:
                        total += 1
                
                # if not readable
                elif 'readable' in self.table[repo_name][field]:
                    if False == self.table[repo_name][field]['readable']:
                        total += 0

                else:
                    print('{type}.get_total() : field={field}'.format(
                        type=self.get_class_name(),
                        field=field,
                    ))
                    print(list(self.table[repo_name][field].keys()))
                    raise NotImplementedError

        if b_verbose:
            print('{class_name}.get_total({repo_name}) : total = {total}'.format(
                class_name=self.get_class_name(),
                repo_name=repo_name,
                total=total,
            ))

        return total

    def run_script_input(self, python_cmd):

        # adaptive input string based on list of available files
        # to prevent excessive file not found error
        input_list = ['aa', 'bb', 'cc', 'dd', 'ee']

        # frequent filename        
        if 'test.txt' in os.listdir():
            input_list.insert(0, 'test.txt')
        elif 'ex15_sample.txt' in os.listdir():
            input_list.insert(0, 'ex15_sample.txt')

        input_txt = '\n'.join(input_list)

        # subprocess.Popen() needs bytes as input
        msgo, msge = git.run_command(
                python_cmd, in_txt=bytes(input_txt, encoding='utf-8'),
                b_verbose=False,
            )
        return msgo, msge


class RepoEvalRunEachSkipSome(RepoEvalRunEach):
    """
    If a script file contains matplotlib, its window would stop automated execution
    """

    def eval_file_base(self, filename, b_verbose=False):
        """
        Check filename & content and run if seems fine
        """

        if not self.is_python(filename):
            result = 'N/A'
        else:
            # some files may have unreadable character
            txt = self.is_readable(filename)

            if not txt:
                result = {'readable': False}
            else:
                # if it was readable, first check grammar
                result = self.check_grammar(filename)

                if result['grammar pass']:

                    if self.is_pylab(txt):
                        # to save time and click
                        result = self.check_grammar(filename)
                        result['type'] = 'pylab'
                    elif self.is_while_true(txt):
                        # to save time
                        result = self.check_grammar(filename)
                        result['type'] = 'while true'
                    elif self.has_while(filename):
                        # to save time
                        result = self.check_grammar(filename)
                        result['type'] = 'while'
                    elif self.is_tkinter(txt):
                        result = self.check_grammar(filename)
                        result['type'] = 'tkinter'
                    elif self.has_exit_on_click(txt):
                        # to save time and click
                        result = self.check_grammar(filename)
                        result['type'] = 'exit on click'
                    elif self.has_hanoi(txt):
                        # to save time
                        result = self.check_grammar(filename)
                        result['type'] = 'hanoi'
                    elif self.is_recursion_filename(filename):
                        # to save time
                        result = self.check_grammar(filename)
                        result['type'] = 'recursion filename'
                    elif is_argv(txt):
                        # adaptive number of arguments
                        argn = get_argn(filename)

                        # generate adaptive arguments
                        arguments_txt = ''

                        # leave a room for the default argument
                        for i in range(argn - 2):
                            arguments_txt += '{c}.txt '.format(c=chr(ord('a') + i))

                        # handle one special case
                        if filename.startswith('ex15'):
                            default_filename = 'ex15_sample.txt'
                        else:
                            default_filename = 'test.txt'

                        # frequent filename as the first argument
                        arguments_txt = default_filename + ' ' + arguments_txt

                        if b_verbose:
                            print('{class_name}.eval_file_base({filename}) : argn = {argn} : arguments = {argv}'.format(
                                    class_name=self.get_class_name(),
                                    filename=filename,
                                    argv = arguments_txt,
                                    argn = argn,
                            ))

                        result = self.run_script(filename, arguments_txt)
                        result.update({'type': 'argv'})
                        
                    else:
                        result = self.run_script(filename)

            # explicitly delete temporary variable to save memory
            del txt

        return result

    @staticmethod
    def is_pylab(txt):
        return ('pylab' in txt) or ('matplotlib' in txt)

    def has_token(self, filename, token):
        result = False
        with open(filename, encoding='utf-8') as f:
            try:
                for toktype, tok, start, end, line in tokenize.generate_tokens(f.readline):
                    if (tokenize.COMMENT != toktype) and (token in tok):
                        result = toktype, tok, start, end, line
                        break
            except tokenize.TokenError:
                print('*** tokenize.TokenError ***')
                if filename is not None:
                    print('cwd=', os.getcwd())
                    print('filename =', filename)
            except IndentationError:
                    print('{type} : {filename} : IndentationError'.format(type=type(self).__name__, filename=filename))

        return result

    def is_input(self, filename):
        return self.has_token(filename, 'input')

    def has_while(self, filename):
        return self.has_token(filename, 'while')

    @staticmethod
    def is_while_true(txt):
        return ('while True' in txt) or ('while (True)' in txt)

    @staticmethod
    def is_tkinter(txt):
        return 'tkinter' in txt

    @staticmethod
    def has_exit_on_click(txt):
        return '.exitonclick()' in txt

    @staticmethod
    def has_hanoi(txt):
        # hanoi tower problem tend to generate too much output
        # TODO : detect recursion
        return re.findall(r'def\s+hanoi\s*\(', txt, re.M)

    @staticmethod
    def is_recursion_filename(filename):
        """
        See if a filename starts with recursion
        """
        # TODO : detect recursion
        return filename.startswith('recursion')


def is_argv(txt):
    """
    Is argv of sys in the text?
    """
    result = any((
        is_sys_argv(txt), 
        is_from_sys_argv(txt)
    ))

    return result


def is_from_sys_argv(txt):
    """
    Using regex, check from sys import argv
    """
    is_from_sys_import_argv = re.findall(r'from\s+sys\s+import\s+argv', txt, re.M|re.S)
    return is_from_sys_import_argv


def is_sys_argv(txt):
    """
    Using regex, check import sys and ??? = sys.argv
    """
    is_sys_argv = re.findall (r'import\s+sys\s+.*=\s+sys.argv', txt, re.M|re.S)
    return is_sys_argv


def get_argn(filename):
    # find maximum number of arguments
    # initial value
    result = 0

    with open(filename, 'r', encoding='utf-8') as f:
        try:
            # token loop
            for toktype__tok__start__end__line in tokenize.generate_tokens(f.readline):
                toktype = toktype__tok__start__end__line[0]
                tok = toktype__tok__start__end__line[1]
                line = toktype__tok__start__end__line[4]
                # find line with argv
                if (toktype == tokenize.NAME) and ('argv' == tok) and ('=' in line):
                    # would need to look into the left side of '=' in this line
                    left__right = line.strip().split('=')

                    n_equal = line.count('=')

                    # only one '=' in the line
                    if 1 == n_equal:
                        left = left__right[0]
                        # try to find number of variables on the left side
                        # TODO : what if (a, b, c) = argv?
                        # TODO : what if a, b, c            = argv?
                        # TODO : what if a, b, c, = argv?
                        # TODO : what if # a, b, c, = argv?
                        # TODO : repeat above for sys.argv case
                        # TODO : repeat above for import sys as ?? case
                        argv_list = left.strip().split(',')

                        # count the number of arguments
                        len_argv_now = len(argv_list)

                    # if two or more '='s
                    elif 2 <= n_equal:
                        # `script = sys, user_name = argv` is equivalent to
                        # script = sys = argv1, user_name = argv2

                        # remove the left most element
                        left__right.pop()

                        # reassemble the left side
                        left_side = '='.join(left__right).split(',')

                        # number of arguments = number of commas plus one
                        len_argv_now = left_side.count(',') + 1

                        # indicate the file
                        print("get_argn() : more than one '='s in {filename} of {path}".format(
                            filename=filename, path=os.getcwd()
                        ))

                    # find maximum
                    if len_argv_now > result:
                        result = len_argv_now

        except tokenize.TokenError:
            print('*** tokenize.TokenError ***')
            if filename is not None:
                print('cwd=', os.getcwd())
                print('filename =', filename)

        except IndentationError:
                print('{filename} : IndentationError'.format(filename=filename))

    return result


def get_date_string_tuple_from_git_log_msg(msg):
    """
    identify date within each commit record from 'git log'
    """

    '''
    commit fc8fb8e9b3a5174303d3733e1646d53a3dc5f638
    Author: naverdev <naverdev@naver.com>
    Date:   Tue Mar 4 06:58:15 2014 +0000
    
        initialized Git repository    
    '''
    
    # long text -> list of lines
    lines = msg.split('\n')
    
    # initialize result list 
    result = []
    
    for line in lines:
        # if string 'Date:' spotted
        if "Date:" == line.strip()[:5]:
            # date in string
            date_string = line[5:-5].strip()

            # print(date_string)

            # convert time string into time structure
            # 'Fri Apr 4 21:51:58 2014' 
            # -> time.struct_time(
            #       tm_year=2014, tm_mon=4, tm_mday=4, 
            #       tm_hour=21, tm_min=51, tm_sec=58, 
            #       tm_wday=4, tm_yday=94, tm_isdst=-1
            # )
            result.append( time.strptime(date_string) )
            # print(result[-1])
    return tuple(result)


class TextTableWriter(object):
    # class variables
    ext = 'txt'
    col_sep='\t'
    row_sep='\n'

    # for each cell
    # to reuse get_cell_text() code
    cell_formatter='{sep}{value}'    

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
        self.header_first_row_header = '{col_sep}  '.format(col_sep=self.col_sep)
        # '|:--:|:----:|:----:|:----:|\n'
        #  ^^^
        self.header_second_row_header = '{col_sep}:-'.format(col_sep=self.col_sep)

        # '|   |  field1  |  field2  |  field3 |\n'
        #    ^^^^^      ^^^^^      ^^^^^ 
        self.header_first_col_sep = '  {col_sep}  '.format(col_sep=self.col_sep)
        # '|:--:|:----:|:----:|:----:|\n'
        #     ^^^^^^^^^^^^^^^^^^^^^ 
        self.header_second_col_sep = '-:{col_sep}:---'.format(col_sep=self.col_sep)

        # '|   |  field1  |  field2  |  field3 |\n'
        #                                     ^^^^
        self.header_first_row_sep = '  {col_sep}\n'.format(row_sep=self.row_sep, col_sep=self.col_sep)
        # '|:--:|:----:|:----:|:----:|\n'
        #                          ^^^^^
        self.header_second_row_sep = '-:{col_sep}\n'.format(row_sep=self.row_sep, col_sep=self.col_sep)

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
            assert second_line.count(':') == (second_line.count('|') - 1)* 2
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

        ## table
        yield self.table_header

        # reuse superclass code
        # https://stackoverflow.com/questions/11197186/how-do-i-yield-results-from-a-nested-python-generator-function
        for item in super(HtmlTableWriter, self).gen_rows():
            yield item

        yield self.table_footer
        ## table end

        yield self.html_footer
        # html end

    def get_header_row(self):

        #### header column
        header_column = '{row_header}{item_header} {sep}'.format(
            row_header=self.row_header,
            item_header=self.header_row_header,
            sep=self.header_col_sep,
        )

        #### column loop
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
        #### header column
        # assume </td> follows
        return '{row_header}{item_header} {repo_name} '.format(
            row_header=self.row_header, item_header=self.item_header,
            repo_name=repo_name
        )


if "__main__" == __name__:
    main(sys.argv[1:])
