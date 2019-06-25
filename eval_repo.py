import ast
import configparser
import fractions
import multiprocessing
import os
import re
import time
import tokenize

import dict_table
import git
import iter_repo
import repo_path
import unique_list
import read_python


class RepoEval(object):
    """
    To evaluate one repository
    """

    def __init__(self, ):
        # table of repository names in rows and relative path/file names in columns
        self.table = dict_table.RepoTable()
        self.repo_name = None
        self.repo_path = None

    def eval_repo_list(self, repo_list,  b_multiprocessing=True):
        """

        :param list(dict) repo_list:
        :param bool b_multiprocessing:
        :return:
        """
        # integrate evaluation results
        # multiprocessing args are different from student_dict here
        # initialize student dictionary

        student_dict = dict_table.RepoTable()

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
        print('{repoEval}.eval_repo({k:2d}) start: name={name}'.format(
            repoEval=self.get_class_name(), k=k, name=repo['name']))

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
        b_ignore = any((is_dot_git_path, is_xcode_path, is_pycharm_path,
                        is_vscode_path, is_pycache_path, is_ipynb_checkpoints_path))
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
            result = iter_repo.read_b_decode(filename)
        except UnicodeDecodeError:
            print('%s : unable to read %s' %
                  (self.get_class_name(), os.path.join(os.getcwd(), filename)))
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
            'log',  # must be the first
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
        print('{repoEval}.eval_repo({k:2d}) start: name={name}'.format(
            repoEval=self.get_class_name(), k=k, name=repo['name']))

        path_org = os.getcwd()
        os.chdir(self.repo_path)

        git_log__err_msg = git.git_common_list(
            self.get_git_cmd(), b_verbose=False)

        os.chdir(path_org)

        git_log = git_log__err_msg[0]

        column_set, eval_dict = self.convert_git_log_to_table(git_log)

        # update evaluation result
        for column in column_set:
            self.table.set_row_column(
                self.repo_name, column, eval_dict[column])

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

        last_commit_dict = {'subject': 'no commit yet'}

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
                last_commit_dict = self.get_commit_dict(
                    git_log_lines[0].strip('"'))

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

            line = 'could be a merge commit'

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
                    eval_dict[files_in_commit] = eval_dict.get(
                        files_in_commit, 0) + point

                # if it is still not a dict
                if isinstance(last_commit_dict, str):
                    # try to convert it again
                    print(f'last_commit_dict = {repr(last_commit_dict)}')
                    last_commit_dict = ast.literal_eval(last_commit_dict)
                    if not isinstance(last_commit_dict, dict):
                        raise ValueError(
                            f'last_commit_dict = {repr(last_commit_dict)}')
                last_commit_dict['files'] = temporary_file_list
            else:
                print(
                    f'\n{self.get_class_name()}.convert_git_log_to_table() : end of file list but temporary_file_list empty')
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
                    comments_list = self.get_comments_list_from_readline(
                        file_object.readline, filename=filename)
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
        self.table.set_row_column(
            repo_name, ' total', self.get_total(repo_name))

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
        # sample cfg file
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
            'comment_output_file': 'reference_comment.txt',
        }
        config_ref['urls'] = {
            # urls of the reference repositories
            'a': 'reference repository a url here',
            'b': 'reference repository b url here',
            'c': 'reference repository c url here',
        }
        config_ref['commits'] = {
            # hashes of reference commits here
            'a': 'reference repository a base hash here',
            'b': 'reference repository b base hash here',
            'c': 'reference repository c base hash here',
        }

        with open(self.reference_cfg_filename, 'w') as ref_cfg_file:
            config_ref.write(ref_cfg_file)

        raise FileNotFoundError(
            f'please configure {self.reference_cfg_filename}, run reference.py, and restart')

    def get_line_point(self, comment, b_verbose=False):
        if comment.strip() not in self.comments_ref:
            if b_verbose:
                print(comment)
            point = super(RepoEvalPoundByteCounterExcludingRef,
                          self).get_line_point(comment)
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

    def run_script(self, filename, arguments='a b c'):

        # some file names may contain space
        python_cmd_list = [self.python_path, filename]

        if isinstance(arguments, str):
            arguments = arguments.split()

        # more adaptive arguments
        arguments = self.get_arguments(filename)

        if isinstance(arguments, list):
            python_cmd_list += arguments
        else:
            raise NotImplementedError(
                msg='type of arguments = %s' % type(arguments))

        # print('RepoEvalRunEach.run_script() : cwd = ', os.getcwd())
        # print('RepoEvalRunEach.run_script() : python_cmd = ', python_cmd)

        # subprocess.Popen() needs bytes as input
        msgo, msge = self.run_script_input(python_cmd_list)
        if 'Error' in msge:
            # to help debugging
            # present info only if exception happens
            print('{type:s}.run_script() : cwd = {cwd}'.format(
                type=self.get_class_name(), cwd=os.getcwd()))
            print('{type:s}.run_script() : python_cmd = {cmd!s}'.format(
                type=self.get_class_name(), cmd=python_cmd_list))
            try:
                print('{type:s}.run_script() : error message = {msge}'.format(
                    type=self.get_class_name(), msge=msge))
            except UnicodeEncodeError:
                print('{type:s}.run_script() : error message(r) = {msge}'.format(
                    type=self.get_class_name(), msge=repr(msge)))

            # If the .py script cannot find a file, present list of available files
            # to help improvement
            if 'FileNotFoundError:' in msge:
                print('{type:s}.run_script() : available files = {files}\n'.format(type=self.get_class_name(),
                                                                                   files=str(
                                                                                       os.listdir())
                                                                                   ))

        # else:
        #     print('RepoEvalRunEach.run_script() : {cmd} OK'.format(cmd=python_cmd))

        result = {'stdout': len(msgo.strip()), 'stderr': len(msge.strip())}

        # explicitly delete temporary variables to save memory
        del python_cmd_list[:]
        del msgo, msge, python_cmd_list

        return result

    def get_arguments(self, filename):
        # more adaptive arguments
        if os.path.basename(os.getcwd()).startswith('ex23'):
            arguments = ['utf-8', 'replace']
        else:
            arguments = []

            n_argv = get_argn(filename)

            if 1 < n_argv:
                arguments = list(str(i) for i in range(1, n_argv))

                other_file_list = list(
                    filter(
                        lambda fname: os.path.isfile(fname) and (
                            not fname.endswith('.py')),
                        os.listdir()
                    )
                )

                if other_file_list:
                    del arguments[-1]
                    arguments.insert(0, other_file_list[0])

        return arguments

    def count_nargv(self, txt):

        n_argv = 0

        match = self.search_sys_argv_assign_line(txt)

        if match:
            argv_list = match.group(1).split(',')
            n_argv = len(argv_list) - 1

        return n_argv

    def search_sys_argv_assign_line(self, txt):
        return re.search(r'^(.+?)\s*=\s*(?:(?:sys.argv)|(?:argv))\s*$', txt, re.M)

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
        input_list = list(str(i) for i in range(10))

        # frequent filename
        if 'test.txt' in os.listdir():
            input_list.insert(0, 'test.txt')
        elif 'ex15_sample.txt' in os.listdir():
            input_list.insert(0, 'ex15_sample.txt')

        input_txt = '\n'.join(input_list)

        # subprocess.Popen() needs bytes as input
        msgo, msge = git.run_command(
            python_cmd,
            in_txt=input_txt,
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
                            arguments_txt += '{c}.txt '.format(
                                c=chr(ord('a') + i))

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
                                argv=arguments_txt,
                                argn=argn,
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
                # https://docs.python.org/3/library/tokenize.html#tokenize.tokenize
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
                print('{type} : {filename} : IndentationError'.format(
                    type=type(self).__name__, filename=filename))

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


class RepoEvalRunEachSkipSomeLastCommit(RepoEvalRunEachSkipSome):
    def eval_file_base(self, filename, b_verbose=False):
        """
        Evaluate file and attach last commit info
        """
        result = super().eval_file_base(filename=filename, b_verbose=b_verbose)

        # TODO : What if other subclasses of RepoEval need similar feature?
        #        Rename RepoEval to RepoEvalBase and add this to RepoEval?

        if isinstance(result, dict):
            result['sha'] = git.get_last_sha(path=filename)

        return result


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
    is_from_sys_import_argv = re.findall(
        r'from\s+sys\s+import\s+argv', txt, re.M | re.S)
    return is_from_sys_import_argv


def is_sys_argv(txt):
    """
    Using regex, check import sys and ??? = sys.argv
    """
    is_sys_argv = re.findall(
        r'import\s+sys\s+.*=\s+sys.argv', txt, re.M | re.S)
    return is_sys_argv


def get_argn(filename):
    # find maximum number of arguments
    # initial value
    result = 0

    token_list = []

    last_new_line = 0
    equals_of_this_line = []
    # initial -> equal ->

    with open(filename, 'r', encoding='utf-8') as f:
        try:
            # token loop
            # https://docs.python.org/3/library/tokenize.html#tokenize.tokenize

            token_list = list(tokenize.generate_tokens(f.readline))

            # https://docs.python.org/3.6/library/tokenize.html#examples
            for k, toktype__tok__start__end__line in enumerate(token_list):
                toktype, tok, start, end, line = toktype__tok__start__end__line

                if (toktype == tokenize.NEWLINE):
                    last_new_line = k
                    equals_of_this_line = []

                elif (toktype == tokenize.OP) and ('=' == tok):
                    equals_of_this_line.append(k)

                elif (toktype == tokenize.NAME) and ('argv' == tok):

                    if 1 == len(equals_of_this_line):
                        left_list = token_list[(
                            last_new_line + 1):equals_of_this_line[-1]]

                        # count the number of names
                        result = 0
                        for item in left_list:
                            if (tokenize.NAME == item[0]):
                                result += 1
                        break
                    # if two or more '='s
                    elif 2 <= len(equals_of_this_line):
                        raise NotImplementedError

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
            result.append(time.strptime(date_string))
            # print(result[-1])
    return tuple(result)
