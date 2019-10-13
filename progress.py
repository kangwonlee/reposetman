"""

Progress report generator

To automatically generate progress reports over multiple repositories

Author : KangWon LEE

Year : 2018

"""


import argparse
import ast
import configparser
import itertools
import json
import os
import re
import sys
import time
import typing

import dict_table
import eval_repo
import git
import iter_repo
import regex_test as ret
import timeit


# https://stackoverflow.com/questions/1681836/how-to-debug-a-memoryerror-in-python-tools-for-tracking-memory-use
def get_size_of(one, name):
    # may need to investigate MemoryError
    print(
        '** get_size_of({name}) = {size} **'.format(name=name, size=sys.getsizeof(one)))


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
        self.config = get_config_from_filename(config_filename)

        # compile regex here not to repeat later
        self.re_git_log = eval_repo.RepoEvalCountCommit.get_regex_parse_git_log()

    def get_section_list(self):
        op_key = 'operation'
        if 'sections' not in self.config[op_key]:
            if 'section' not in self.config[op_key]:
                raise IOError(
                    'Unable to find section list from the config file')
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
        repo_url_list = ret.get_github_url_list(
            self.config[section]['list'].strip())
        print('process_section() : # repositories =', len(repo_url_list))

        # clone or update student repositories
        repo_list = ret.clone_or_pull_repo_list(
            repo_url_list,
            section_folder=self.config[section]['folder'],
            b_update_repo=(
                'True' == self.config['operation']['update_repo'].strip())
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
def main(argv=sys.argv):
    """

    main function of progress report generator
    get project ID's
    update repositories
    initialize big dictionary
    call visit_path() thru os.walk()
    write table

    input file name : in progress.cfg

    """

    # https://docs.python.org/3.7/library/argparse.html
    ns = parse_args(argv)

    # https://docs.python.org/3/library/configparser.html
    config = get_config_from_filename(ns.config_filename)
    config['operation']['multiprocessing'] = str(ns.multiprocessing)

    # compile regex here not to repeat later
    re_git_log = eval_repo.RepoEvalCountCommit.get_regex_parse_git_log()

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
            gen_arg_process_section(iter_repo.get_section_list(config))
        )
    )


def parse_args(argv:typing.Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise Chart Builder")
    parser.add_argument('config_filename', type=str, default='progress.cfg', help="section configuration file")
    # https://docs.python.org/3.7/library/argparse.html
    # Parsing boolean values with argparse, https://stackoverflow.com/a/15008806
    parser.add_argument('--multiprocessing', dest='multiprocessing', action='store_true', help="enable multiprocessing")
    parser.add_argument('--no-multiprocessing', dest='multiprocessing', action='store_false', help="disable multiprocessing")
    parser.set_defaults(multiprocessing=True)

    ns = parser.parse_args(argv[1:])
    return ns


def get_config_from_argv(argv):

    return get_config_from_filename(get_cfg_filename_from_argv(argv))


def get_cfg_filename_from_argv(argv):
    if argv:
        config_filename = argv[0]
    else:
        config_filename = 'progress.cfg'

    return config_filename


def get_config_from_filename(config_filename=False):
    # https://docs.python.org/3/library/configparser.html
    config = configparser.ConfigParser()

    if not config_filename:
        config_filename = 'progress.cfg'

    config.read(config_filename)

    return config


def config2bool(value:str) -> bool:
    if not value:
        result = False
    else:
        result = 'false' != value.strip().lower()
    return result


@timeit.timeit
def process_section(config: configparser.ConfigParser, re_git_log:re.Pattern, section:str):
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
        b_update_repo=config2bool(config['operation']['update_repo']),
        b_multiprocessing=config2bool(config['operation']['multiprocessing']),
    )

    results = {}

    # evaluate repositories within the section
    if 'True' == config[section]['count_commits']:
        call_commit_count(config, section, repo_list, results)
    if 'True' == config[section]['pound_count']:
        call_pound_count(config, section, repo_list, results)
    if 'True' == config[section]['run_all']:
        call_run_all(config, section, repo_list, results)

    postprocess(config, section, results)

    return results


def postprocess(config, section, results):
    # not to broadcast too frequently
    last_sent_filename = get_last_sent_filename(config, section)
    comment_period_days = float(config[section]['comment_period_days'])

    last_sent_gmtime_sec = get_last_sent_gmtime_sec(last_sent_filename)

    if is_too_frequent(last_sent_gmtime_sec, comment_period_days):
        print("Message may be too frequent?")
    else:
        message_list_builder_grammar = MessageListBuilderGrammar(
            config, section, results['run_all']['table'], message_list=[])
        message_list = message_list_builder_grammar.build_message_list()

        if (
            ('True' == config[section]['count_commits'])
            and ('True' == config[section]['pound_count'])
            and ('True' == config[section]['run_all'])
        ):
            message_list_builder_pound = MessageListBuilderPound(
                config, section, results, message_list=message_list)
            message_list = message_list_builder_pound.build_message_list()

        write_message_files(
            message_list,
            get_message_filename(config, section),
            get_last_sent_filename(config, section)
        )


def get_section_name(config, section):
    return config[section]['organization']


def get_last_sent_filename(config, section):
    return config[section]['last_sent_file']


def get_message_filename(config, section):
    return config[section]['todo_list_file']


def call_run_all(config, section, repo_list, results):
    run_all_dict = run_all(config, section, repo_list)
    results.update(
        {
            'run_all': run_all_dict,
        }
    )


def call_pound_count(config, section, repo_list, results):
    pound_reports = pound_count(config, section, repo_list)
    results.update(
        {
            'pound_counts': pound_reports
        }
    )


def call_commit_count(config, section, repo_list, results):
    """
    Call count commits() and update results dict

    :param configparser.Configparser config : program configurations
    :param str section : usually '{course id}{yr}{a/b/c}', '{course id}{yr}{a/b/c}', or '{course id}{yr}{a/b/c}'
    :param list(dict) repo_list : list of repository_information_dictionary
    :param dict results: contains dictionary of results
    """
    count_commits_dict = count_commits(config, section, repo_list)
    results.update(
        {
            'count_commits': count_commits_dict,
        }
    )


@timeit.timeit
def count_commits(config:configparser.ConfigParser, section:str, repo_list:typing.Sequence):
    """
    Count commits of each file fromt eh section
    """
    # git log interval settings
    after = config[section].get('after', None)
    before = config[section].get('before', None)
    exclude_email_tuple = tuple(ast.literal_eval(
        config['operation']['initial_email_addresses']))

    commit_counter = eval_repo.RepoEvalCountOneCommitLog(
        after, before, exclude_email_tuple)
    commit_count = commit_counter.eval_repo_list(repo_list)

    # if the header row seems to include '\' character in the header row
    if commit_count.is_backslash_in_header():
        print(
            "'\\' in column title row.\n"
            'Could you please run following git command to change its configuration?\n'
            '\n'
            '    git config core.quotepath false\n'
            '\n'
            'or\n'
            '\n'
            '    git config --global core.quotepath false\n'
            '\n'
        )

    # sort with total
    # TODO : more adaptive argument?
    sorted_row = commit_count.get_sorted_row(' total')

    # write tables
    write_tables_dict = write_tables(
        section,
        repo_list,
        commit_count,
        filename_prefix='commit_count',
        sorted_row=sorted_row
    )

    write_tables_dict['table'] = commit_count

    return write_tables_dict


@timeit.timeit
def write_tables(section, repo_list, table, filename_prefix, sorted_row=None):

    # if sorted_row not given, make one from repo_list
    if sorted_row is None:
        # TODO : Possibly repeating too frequently
        sorted_row = tuple([repo_dict['name'] for repo_dict in repo_list])

    txt_table_writer = dict_table.TextTableWriter(
        table, section, sorted_row, filename_prefix=filename_prefix)
    finished_txt_table = txt_table_writer.write()

    md_table_writer = dict_table.MDlinkTableWriter(
        table, section, sorted_row, filename_prefix=filename_prefix, repo_list=repo_list)
    finished_md_table = md_table_writer.write()

    html_table_writter = dict_table.HtmlLinkTableWriter(
        table, section, sorted_row, filename_prefix=filename_prefix, repo_list=repo_list)
    finished_html_table = html_table_writter.write()

    result_dict = {
        'txt': finished_txt_table,
        'md': finished_md_table,
        'html': finished_html_table,
    }

    return result_dict


@timeit.timeit
def run_all(config, section, repo_list):
    """
    Run (almost) all .py files from the section
    """

    all_runner = eval_repo.RepoEvalRunEachSkipSomeLastCommit(
        config['operation']['python_path'])
    all_outputs = all_runner.eval_repo_list(repo_list)
    print(f'run_all() : finished eval_repo_list()')

    # repository names in order
    sorted_row = all_outputs.get_sorted_row(' total')

    # write tables
    write_tables_dict = write_tables(
        section,
        repo_list,
        all_outputs,
        filename_prefix='run_all',
        sorted_row=sorted_row,
    )
    print('run_all() : finished write_tables()')

    write_tables_dict['table'] = all_outputs

    return write_tables_dict


class MessageListBuilderBase(object):
    def __init__(self, config, section, table, b_verbose=False, message_list=[]):
        """
        Build a json file for GitHub commit messages

        config : see sample progress.cfg file
        section : section name
        table : RepoTable on each file
        b_verbose = False
        message = [] : if there is an existing message list
        """

        self.config = config
        self.section = section
        self.table = table
        self.b_verbose = b_verbose
        self.message_list = message_list

    def get_section_name(self):
        return self.config[self.section]['organization']

    def get_last_sent_filename(self):
        return self.config[self.section]['last_sent_file']

    def get_message_filename(self):
        return self.config[self.section]['todo_list_file']

    @timeit.timeit
    def build_message_list(self):
        if self.b_verbose:
            print('build_message_list() starts')

        if self.b_verbose:
            print(
                f'build_message_list() : len(message_list) = {len(self.message_list)}')

        # usually organization for the class
        org_name = self.get_section_name()

        # row loop == repository loop
        for repo_name in self.table.index:
            # column loop == folder/file loop
            for local_path in self.table[repo_name]:
                message_dict = self.build_message_dict(
                    repo_name, local_path, org_name, b_verbose=False)

                if message_dict:
                    self.message_list.append(message_dict)
                    if self.b_verbose:
                        print(
                            f"build_message_list() : appending {message_dict}")
                    if self.b_verbose:
                        print(
                            f"build_message_list() : len(message_list) = {len(self.message_list)}")
            # end of file loop
        # end of repo loop

        if self.b_verbose:
            print('build_message_list() ends')

        return self.message_list

    def build_message_dict(self, row, column, org_name, b_verbose=False):
        raise NotImplementedError


class MessageListBuilderGrammar(MessageListBuilderBase):
    def build_message_dict(self, row, column, org_name, b_verbose=False):
        run_result_dict = self.table[row][column]

        todo_dict = {}

        # otherwise, usually not a .py file
        if isinstance(run_result_dict, dict):
            # if the dict has 'grammar pass' and the value is False
            if not run_result_dict.get('grammar pass', True):
                # json example
                # {
                #   "owner": "<github user id or organization id>",
                #   "repo": "<repository id>",
                #   "sha": "<SHA of the commit of the repository>",
                #   "message": "<comment string>"
                # },
                todo_dict = {
                    "owner": self.get_section_name(),
                    "repo": row,
                    "sha": run_result_dict['sha'],
                    "message": (
                        f"파일 {column} 구문 확인 바랍니다. (자동 생성 메시지 시험중)\n"
                        f"Please verify syntax of {column}. (Testing auto comments)"
                    )
                }

        return todo_dict


class MessageListBuilderPound(MessageListBuilderBase):
    def __init__(self, config, section, result_dict, b_verbose=False, message_list=[]):
        super().__init__(config, section,
                         result_dict['run_all']['table'], b_verbose, message_list)

        self.run_all = result_dict['run_all']['table']
        self.commit_count = result_dict['count_commits']['table']
        self.pound_count = result_dict['pound_counts']['table']

    def build_message_dict(self, row, column, org_name, b_verbose=False):
        no_commits = self.commit_count[row].get(column, 0)
        no_pound_bytes = self.pound_count[row].get(column, -1)
        run_result_dict = self.table[row][column]

        todo_dict = {}

        if b_verbose:
            print(f'no_commits = {no_commits}')
            print(f'no_pound_bytes = {no_pound_bytes}')
            print(f'run_result_dict = {run_result_dict}')

        # otherwise, usually not a .py file
        if isinstance(run_result_dict, dict):
            # if the dict has 'grammar pass' and the value is False
            if (0 < no_commits) and (0 == no_pound_bytes):
                # json example
                # {
                #   "owner": "<github user id or organization id>",
                #   "repo": "<repository id>",
                #   "sha": "<SHA of the commit of the repository>",
                #   "message": "<comment string>"
                # },
                todo_dict = {
                    "owner": self.get_section_name(),
                    "repo": row,
                    "sha": run_result_dict['sha'],
                    "message": (
                        f"파일 {column} 각 행 주석 추가 바랍니다. (자동 생성 메시지 시험중)\n"
                        f"Please add comments to lines of {column}. (Testing auto comments)"
                    )
                }

        return todo_dict


def write_message_files(todo_list, todo_list_filename, last_sent_filename):

    # write to json file
    with open(todo_list_filename, 'wt', encoding='utf-8') as todo_list_file:
        json.dump(todo_list, todo_list_file, indent=4, sort_keys=True)

    # record last sent date
    with open(last_sent_filename, 'wt') as last_sent_file:
        write_last_sent(last_sent_file)


def is_too_frequent(last_sent_gmtime_sec, comment_period_days=7, b_verbose=True):
    """
    Considering last sent time, is it too frequent?
    """
    if b_verbose:
        print(
            f"last sent time : {time.asctime(time.localtime(last_sent_gmtime_sec))}")

    since_last_sent_sec = time.time() - last_sent_gmtime_sec

    # https://docs.python.org/3.7/library/time.html#time.localtime
    since_time_struct = time.gmtime(since_last_sent_sec)
    # https://docs.python.org/3.7/library/time.html#time.struct_time

    # unit == days
    since_last_sent_days = since_last_sent_sec/3600/24
    # unit == days in integer (discard hr:min info)
    since_last_sent_days_int = int(since_last_sent_days)

    # how many days since last message?
    if b_verbose:
        print(f"{since_last_sent_days_int:d}d "
              f"{since_time_struct.tm_hour:02d}h "
              f"{since_time_struct.tm_min:02d}m "
              f"{since_time_struct.tm_sec:02d}s passed"
              )

    # verdict
    b_too_frequent = since_last_sent_days < comment_period_days

    return b_too_frequent


def get_last_sent_gmtime_sec(last_sent_filename, default_days=10):
    """
    From the first line of file of last_sent_filename, get last sent time.time() in sec
    """
    try:
        # try to read from file
        with open(last_sent_filename, 'r') as sent:
            last_sent_gmtime_sec = ast.literal_eval(sent.readline().strip())
    except:
        # if not successful, set default
        last_sent_gmtime_sec = time.time() - (default_days * 24 * 3600)

    return last_sent_gmtime_sec


def write_last_sent(last_sent_file, gmtime_sec=time.time()):

    last_sent_file.write(
        f"{gmtime_sec}\n"
        f"{time.asctime(time.localtime(gmtime_sec))}\n"
    )


@timeit.timeit
def pound_count(config, section, repo_list):
    """
    count # comments of the section
    """

    pound_counter = eval_repo.RepoEvalPoundByteCounterExcludingRef()
    pound_numbers = pound_counter.eval_repo_list(repo_list)
    print('pound_count() : finished eval_repo_list()')

    # sort with total
    # TODO : more adaptive argument?
    sorted_row = pound_numbers.get_sorted_row(' total')

    # write tables
    write_tables_dict = write_tables(
        section,
        repo_list,
        pound_numbers,
        filename_prefix='pound_count',
        sorted_row=sorted_row
    )

    write_tables_dict['table'] = pound_numbers

    return write_tables_dict


if "__main__" == __name__:
    main(sys.argv)
