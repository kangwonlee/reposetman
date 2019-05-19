import ast
import configparser
import datetime
import glob
import os
import shutil
import subprocess
import tempfile
import time
import unittest

import progress


class TestProgress(unittest.TestCase):
    def setUp(self):
        self.msg = 'commit 0095423cbee960ab0e59c05bf0f1b75ea9ab5b18\n' \
                   'Author: Kangwon Lee <kangwon_fwd@naver.com>\n' \
                   'Date:   Fri Apr 4 21:51:58 2014 +0900\n' \
                   '\n' \
                   '    popen -> popen3; to access error messages;\n' \
                   '    encoding -> cp949; to read Korean error messages correctly;\n' \
                   '\n' \
                   'commit 85aa1a43881c9c1cf041b47d347a401509194604\n' \
                   'Author: Kangwon Lee <kangwon_fwd@naver.com>\n' \
                   'Date:   Fri Apr 4 02:43:55 2014 +0900\n' \
                   '\n' \
                   "    ** doesn't work yet ** \n" \
                   '    tried to use mingw32 to run git in UNIX style environment;\n' \
                   '    \n' \
                   '    moved path to ..\\.. to run submodule add\n' \
                   '\n' \
                   'commit 27bb0904481765a966f2ce6c831a40a27408254b\n' \
                   'Author: Kangwon Lee <kangwon_fwd@naver.com>\n' \
                   'Date:   Thu Apr 3 23:12:59 2014 +0900\n' \
                   '\n' \
                   '    refactored git() to git.py\n'

    def test_get_date_string_tuple_from_git_log_msg(self):
        '''
        from a txt of multiple git log messages, extract time info
        '''

        time_list = progress.get_date_string_tuple_from_git_log_msg(self.msg)
        expected = (
            time.strptime("Fri Apr 4 21:51:58 2014"),
            time.strptime("Fri Apr 4 02:43:55 2014"),
            time.strptime("Thu Apr 3 23:12:59 2014"),
        )
        self.assertSequenceEqual(time_list, expected)

    def test_get_regex_parse_git_log(self):
        # function under test
        r = progress.RepoEvalCountCommit.get_regex_parse_git_log()

        expected_list = [
            {
                'sha': '0095423cbee960ab0e59c05bf0f1b75ea9ab5b18',
                'author': 'Kangwon Lee <kangwon_fwd@naver.com>',
                'date': 'Fri Apr 4 21:51:58 2014 +0900',
            },
            {
                'sha': '85aa1a43881c9c1cf041b47d347a401509194604',
                'author': 'Kangwon Lee <kangwon_fwd@naver.com>',
                'date': 'Fri Apr 4 02:43:55 2014 +0900',
            },
            {
                'sha': '27bb0904481765a966f2ce6c831a40a27408254b',
                'author': 'Kangwon Lee <kangwon_fwd@naver.com>',
                'date': 'Thu Apr 3 23:12:59 2014 +0900',
            },
        ]

        for expected, result in zip(expected_list, r.finditer(self.msg)):
            self.assertDictEqual(expected, result.groupdict())

    def te_st_eval_repo(self):
        if os.path.exists('test_eval_repo.cfg'):
            # function needs arguments: args, repo
            args = {
                "fields": set(),
                "re_git_log": progress.get_regex_parse_git_log(),
            }

            config = configparser.ConfigParser()
            config.read('test_eval_repo.cfg')

            repo = {
                'path': config['repo']['path'],
                'name': config['repo']['name'],
            }

            # args['repo name'] = repo['name']

            # function under test
            progress.eval_repo(args, repo)

            self.assertIn(repo['name'], args)

            result = args[repo['name']]
            self.assertTrue(result)

    def te_st_proc_file(self):
        config_filename = 'test_proc_file.cfg'
        if os.path.exists(config_filename):
            arg = {
                'fields': {'readme.md', 'error_note.txt'},
                're_git_log': progress.get_regex_parse_git_log(),
            }

            config = configparser.ConfigParser()
            config.read(config_filename)

            arg['repo'] = config['repo']

            path = config['file']['path']
            filename = config['file']['name']

            current_path = os.getcwd()

            os.chdir(config['file']['cd_to'])

            # function under test
            progress.eval_file(arg, path, filename, arg['repo']['name'])

            column_key = config['file']['path_in_repo'] + \
                '/' + config['file']['name']

            # repository name
            self.assertIn(config['repo']['name'], arg)
            # file name
            self.assertIn(column_key, arg[config['repo']['name']])
            # at least one commit
            self.assertLessEqual(1, arg[config['repo']['name']][column_key][0])

            os.chdir(current_path)

        else:
            raise IOError("can't find config file {filename}".format(
                filename=config_filename))


class TestRepoTable(unittest.TestCase):
    def setUp(self):
        self.table = progress.RepoTable()

    def test_add_row_column_new(self):
        row_key, column_key, value = 'row', 'column', 'value'
        # function under test
        self.table.set_row_column(row_key, column_key, value)

        # check value access
        self.assertIn(row_key, self.table)
        self.assertIn(column_key, self.table[row_key])
        self.assertIn(value, self.table[row_key][column_key])

        # check header
        self.assertIn(column_key, self.table.column)

    def test_add_row_column_duplicate(self):
        row_key, column_key, value = 'row', 'column', 'value'
        self.table.set_row_column(row_key, column_key, value)
        # function under test
        duplicate_value = 'duplicate_value'

        with self.assertRaises(ValueError):
            self.table.set_row_column(row_key, column_key, duplicate_value)

    def test_matrix_new(self):
        index = ('r1', 'r2')
        column = ('c1', 'c2', 'c3')

        # function under test
        for row in index:
            for col in column:
                self.table.set_row_column(row, col, (row, col))

        # check result
        for row in index:
            self.assertIn(row, self.table)
            for col in column:
                self.assertIn(col, self.table[row])
                self.assertEqual((row, col), self.table[row][col])

        for col in column:
            self.assertIn(col, self.table.column)

    def test_matrix_duplicate(self):
        index = ('r1', 'r2')
        column = ('c1', 'c2', 'c3')
        new_value = 'new_value'

        for row in index:
            for col in column:
                self.table.set_row_column(row, col, (row, col))

        # function under test
        for row in index:
            for col in column:

                with self.assertRaises(ValueError):
                    self.table.set_row_column(row, col, (row, col, new_value))

        for col in column:
            self.assertIn(col, self.table.column)


class TestRepoEvalPoundCounter(unittest.TestCase):
    def setUp(self):
        self.code = """\n# this is comment 01
            # this is comment 02
            ' this is string one '
            # this is comment 03
            ' this is string # two '
            # this is comment 4
            " this is string three "
            # this is comment 05
            " this is string # four "
            # this is comment 06
            ''' this is string five '''
            # this is comment 07
            ''' this is string # six '''
            # this is comment 08
            ''' this is 
            string seven '''
            # this is comment 09
            ''' this is 
            string # eight '''
            # this is comment 10
            """

    def test_comments(self):

        evaluator = progress.RepoEvalPoundLineCounter()

        # tokenize.generate_tokens() requires a file object
        with tempfile.TemporaryFile('w+t') as file_object:
            file_object.write(self.code)
            file_object.seek(0)

            comments = set(evaluator.get_comments_list_from_readline(
                file_object.readline))

        expected = set(('this is comment 10', 'this is comment 08', 'this is comment 03', 'this is comment 4', 'this is comment 01',
                        'this is comment 06', 'this is comment 05', 'this is comment 07', 'this is comment 09', 'this is comment 02'))

        self.assertSetEqual(expected, comments)


folder = os.getcwd()


class TestRepoEvalRunEachBase(unittest.TestCase):
    config_filename = 'test_run_each.cfg'

    def init_test_run_each(self):
        if not os.path.exists(self.config_filename):
            config = configparser.ConfigParser()

            config['operation'] = {
                'python_path': shutil.which('python')
            }

            config['tests'] = {
                'count_commits': True,
                'run_all': True,
                'pound_count': True,
            }

            with open(self.config_filename, 'w') as cfg_file:
                config.write(cfg_file)

    def setUp(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_filename):
            self.init_test_run_each()

        self.config.read(self.config_filename)
        self.e = progress.RepoEvalRunEachSkipSome(
            self.config['operation']['python_path'])

    def tearDown(self):
        del self.e
        del self.config


class TestRepoEvalRunEach(TestRepoEvalRunEachBase):

    def test_run_script_input(self):
        # function under test
        msgo, msge = self.e.run_script_input([self.config['operation']['python_path'], os.path.join(
            os.path.split(__file__)[0], 'input_example.py')])
        self.assertFalse(msge, msg='\nstderr : %s' % msge)
        self.assertTrue(msgo, msg='\nstderr : %s' % msge)

    def test_run_script_input_cases(self):
        print('')
        for case in self.config['tests']:
            # .replace('/c/', 'c:\\').replace('/', '\\')
            path_hint = self.config['tests'][case]
            py_file_list = glob.glob(path_hint+'*/*.py')

            for py_file in py_file_list:
                msgo, msge = self.e.run_script_input('{python} {script}'.format(
                    python=self.config['operation']['python_path'],
                    script=py_file,
                ))

                if 'ValueError' in msge:
                    print('script {script} raise ValueError'.format(
                        script=py_file))
                else:
                    self.assertFalse(msge, msg='\nstderr : %s' % msge)
                    self.assertTrue(msgo, msg='\n{file}\nstderr : {stderr}'.format(
                        file=py_file, stderr=msge))

    def test_update_args_ex23(self):

        folder_name = tempfile.mkdtemp(prefix='ex23')
        with tempfile.TemporaryDirectory(prefix='ex23') as folder_name:
            cwd = os.getcwd()
            os.chdir(folder_name)
            
            input_args = []
            copy_input_args = list(input_args)

            with tempfile.TemporaryFile('a+t', encoding='utf-8') as temp_file:
                result_args = self.e.update_args(script_file=temp_file, arguments=input_args)

            os.chdir(cwd)

        self.assertSequenceEqual(['utf-8', 'replace'], result_args)
        self.assertSequenceEqual(input_args, copy_input_args)

    def test_get_sys_argv_assign_line_from_sys_import_argv(self):
        input_txt = (
            'from sys import argv\n'
            'script = argv\n'
        )

        found_list = self.e.findall_sys_argv_assign_line(input_txt)

        self.assertTrue(found_list)

        expected = 'script'

        self.assertEqual(expected, found_list[0])

    def test_get_sys_argv_assign_line_from_sys_import_argv_1(self):
        input_txt = (
            'from sys import argv\n'
            'script, a = argv\n'
        )

        found_list = self.e.findall_sys_argv_assign_line(input_txt)

        self.assertTrue(found_list)

        expected = 'script, a'

        self.assertEqual(expected, found_list[0])


class TestRepoEvalRunEachSkipSome(TestRepoEvalRunEachBase):

    def test_is_input_just_comments(self):
        txt = '# coding: utf-8\n' \
              '# 입력 후 add, commit / Enter source code, add, and commit\n' \
              '# 각 행 주석 입력 후 commit / Enter comment for each line and commit\n' \
              '# 각자 Study drills 시도 후 필요시 commit / Try Study Drills and commit if necessary\n' \
              "# print 'abc' -> print('abc')\n" \
              "# print 'abc', 123 -> print('abc %s' % (123))\n" \
              "# print 'abc', abc, 'def' -> print('abc %s def' % (abc))\n" \
              "# print 'abc', -> print('abc', end=" ")\n" \
              '# 이 예제는 command-line 에서 실행시킬 것 / Please run this from the command-line\n'

        result = self.call_is_input_txt(txt)

        self.assertFalse(result)

    def test_is_input_just_functions(self):
        txt = '''# coding: utf-8\n''' \
            '''# reference: http://learnpythonthehardway.org/book/ex25.html\n''' \
            '''# 입력 후 add, commit / Enter source code, add, and commit\n''' \
            '''# 각 행 주석 입력 후 commit / Enter comment for each line and commit\n''' \
            '''# 각자 Study drills 시도 후 필요시 commit / Try Study Drills and commit if necessary\n''' \
            '''# print 'abc' -> print('abc')\n''' \
            '''# print 'abc', 123 -> print('abc %s' % (123))\n''' \
            '''# print 'abc', abc, 'def' -> print('abc %s def' % (abc))\n''' \
            '''# print 'abc', -> print('abc', end=" ")\n''' \
            '''# raw_input('abc') -> input('abc')\n''' \
            '''# 오류노트 에 각자 오류노트 작성 / Please use your error-note\n''' \
            '''\n''' \
            '''\n''' \
            '''def break_words(stuff):\n''' \
            '''    """This function will break up words for us."""\n''' \
            '''    words = stuff.split(' ')\n''' \
            '''    return words\n''' \
            '''\n''' \
            '''\n''' \
            '''def sort_words(words):\n''' \
            '''    """Sorts the words."""\n''' \
            '''    return sorted(words)\n''' \
            '''\n''' \
            '''\n''' \
            '''def print_first_word(words):\n''' \
            '''    """Prints the first word after popping it off."""\n''' \
            '''    word = words.pop(0)\n''' \
            '''    print(word)\n''' \
            '''\n''' \
            '''\n''' \
            '''def print_last_word(words):\n''' \
            '''    """Prints the last word after popping it off."""\n''' \
            '''    word = words.pop(-1)\n''' \
            '''    print(word)\n''' \
            '''\n''' \
            '''\n''' \
            '''def sort_sentence(sentence):\n''' \
            '''    """Takes in a full sentence and returns the sorted words."""\n''' \
            '''    words = break_words(sentence)\n''' \
            '''    return sort_words(words)\n''' \
            '''\n''' \
            '''\n''' \
            '''def print_first_and_last(sentence):\n''' \
            '''    """Prints the first and last words of the sentence."""\n''' \
            '''    words = break_words(sentence)\n''' \
            '''    print_first_word(words)\n''' \
            '''    print_last_word(words)\n''' \
            '''\n''' \
            '''\n''' \
            '''def print_first_and_last_sorted(sentence):\n''' \
            '''    """Sorts the words then prints the first and last one."""\n''' \
            '''    words = sort_sentence(sentence)\n''' \
            '''    print_first_word(words)\n''' \
            '''    print_last_word(words)\n'''

        result = self.call_is_input_txt(txt)

        self.assertFalse(
            result, msg='\ntoktype, tok, start, end, line = %r' % str(result))

    def prepare_input_file(self, txt):
        # create a temporary file in a secure manner
        fd, filename = tempfile.mkstemp(text=True)
        # close the temporary file for now https://www.logilab.org/blogentry/17873
        os.close(fd)

        # write content
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(txt)
        # finished preparing for the temporary file

        return filename

    def call_is_input_txt(self, txt):
        filename = self.prepare_input_file(txt)

        # function under test
        result = self.e.is_input(filename)

        # delete temporary file after test
        os.remove(filename)

        return result


class TestRepoEvalRunEachSkipSomeLastCommit(TestRepoEvalRunEachBase):

    def setUp(self):
        super().setUp()
        self.e = progress.RepoEvalRunEachSkipSomeLastCommit(
            self.config['operation']['python_path'])

    def test_eval_file_base(self):
        file_path = __file__
        result_dict = self.e.eval_file_base(filename=file_path)
        self.assertIn('sha', result_dict)

        final_sha = result_dict['sha']

        # get git log of the last commit
        p = subprocess.Popen(('git', 'log', '-1', file_path),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msgo, msge = str(
            p.stdout.read(), encoding='utf-8'), str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        if msgo:
            self.assertIn(final_sha, msgo,
                          msg=f'\nresult = {final_sha}\nlog = {msgo}')
        else:
            raise IOError('Unable to obtain git log\nmsgo = {log!r}\nmsge = {err!r}'.format(
                log=msgo, err=msge))


class TestRepoEvalCountOneCommitLog(unittest.TestCase):
    def setUp(self):
        self.e = progress.RepoEvalCountOneCommitLog()

    def tearDown(self):
        del self.e

    def test_get_git_cmd(self):
        # function under test
        result = self.e.get_git_cmd('1990-01-01', '2018-08-31')

        command = list(result)
        command.insert(0, 'git')

        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = p.stdout.read()
        p.stdout.close()

        # git log command should not fail
        self.assertNotEqual(stdout, 'FAIL', msg=result)

        # for debugging
        # print('\ncommand = {cmd}'.format(cmd=command))
        # for k, line in enumerate(stdout.splitlines()):
        #     print(k, str(line, encoding='utf-8'))

        # test line
        test_line = str(stdout.splitlines()[0], encoding='utf-8')

        # check if the line contains all the information correctly
        expected_list = ['7dbdb9', 'KangWon LEE', 'kangwon.lee@kpu.ac.kr',
                         'Wed Jul 4 18:48:00 2018 +0900', 'Initial commit']

        for item in expected_list:
            self.assertIn(item, test_line)

    def test_convert_git_log_to_table(self):
        # sample multiline input text

        # TODO : check if a test is desirable to depend on the internal architecture

        txt = (
            f'{self.e.commit_split_token}0333282e3184bc17b16d42a313897a6c35ded482'
            f'{self.e.field_split_token}Kang Won LEE'
            f'{self.e.field_split_token}kangwon.lee@kpu.ac.kr'
            f'{self.e.field_split_token}Fri Sep 14 01:44:09 2018 +0900'
            f'{self.e.field_split_token}first-commit\n'
            '185\t0\t00.ipynb\n'
            '257\t0\t01.ipynb\n'
            '404\t0\t02.ipynb\n'
            '\n'
            f'{self.e.commit_split_token}83274fd5396a2e81e0ad067371cebed8f54e547f'
            f'{self.e.field_split_token}\'Kangwon Lee (Education)\''
            f'{self.e.field_split_token}\'kangwonlee@users.noreply.github.com\''
            f'{self.e.field_split_token}\'Thu Sep 13 09:42:31 2018 -0700\''
            f'{self.e.field_split_token}\'Initial-commit\'\n'
            '104\t0\t.gitignore\n'
        )

        result_columns, result_index = self.e.convert_git_log_to_table(txt)

        expected_files_set = {'02.ipynb',
                              '00.ipynb', '01.ipynb',  '.gitignore'}
        expected_eval_dict = {'01.ipynb': 1.0,
                              '00.ipynb': 1.0, '02.ipynb': 1.0, '.gitignore': 1.0}

        self.assertFalse(expected_files_set - set(result_columns),
                         f"set(result_columns) = {set(result_columns)}")
        self.assertFalse(expected_files_set - set(result_index.keys()),
                         f"set(result_index.keys()) = {set(result_index.keys())}")

        for filename in expected_files_set:
            self.assertAlmostEqual(
                expected_eval_dict[filename], expected_eval_dict[filename])

    def get_git_log_commit_line(self, sha, author, email, date, subject,):
        return (
            sha +
            f'{self.e.field_split_token}{author}'
            f'{self.e.field_split_token}{email}'
            f'{self.e.field_split_token}{date}'
            f'{self.e.field_split_token}{subject}'
        )

    def test_get_commit_dict_00(self):

        sha = '3a3e9a2f73e7edca47edae11fccfd9e508b63478'
        author = u'LAPTOP-XXXXX\\USER'
        email = u'email@domain.name'
        date = 'Thu Oct 4 22:06:46 2018 +0900'
        subject = u'22222'

        txt = self.get_git_log_commit_line(sha, author, email, date, subject,)

        result = self.e.get_commit_dict(txt)

        expected = {
            'sha': sha,
            'author': author,
            'email': email,
            'date': date,
            'subject': subject,
        }

        self.assertDictEqual(
            expected, result, msg=f"type(result) = {type(result)}")

    def test_get_commit_dict_01(self):
        """
        This test tries to figure out if git log with formatting is suitable to extract information
        """

        sha = '9bfd20b43355df5fceb8098356f5a3267020872e'
        author = u'Name'
        email = u'email@domain.name'
        date = 'Fri Apr 13 21:58:07 2018 +0900'
        subject = u'ex08-n'

        txt = self.get_git_log_commit_line(
            sha,
            author,
            email, date, subject,
        )

        result = self.e.get_commit_dict(txt)
        expected = {'sha': sha,
                    'author': author,
                    'email': email,
                    'date': date,
                    'subject': subject}
        self.assertEqual(expected['sha'], result['sha'])
        self.assertEqual(expected['date'], result['date'])
        self.assertEqual(expected['subject'], result['subject'])

    def test_get_commit_dict_02(self):
        """
        This test tries to figure out if git log with formatting is suitable to extract information
        """
        sha = 'shashashashasha'
        author = u'authorauthorauthorauthor'
        email = u'emailemailemail'
        date = 'datedatedate'
        subject = u'  Merge branch \'hotfix/branch_figure\'  '

        txt = self.get_git_log_commit_line(
            sha,
            author,
            email, date, subject,
        )

        result = self.e.get_commit_dict(txt)
        expected = {
            'sha': sha,
            'author': author,
            'email': email,
            'date': date,
            'subject': subject,
        }

        self.assertEqual(expected['sha'], result['sha'])
        self.assertEqual(expected['date'], result['date'])
        self.assertEqual(expected['subject'], result['subject'])

    def get_input_string(self, filename, sha):
        # obtain input string

        git_cmd = self.e.get_git_cmd()

        problem_repo_path = open(filename, 'r').read()

        cwd_backup = os.getcwd()
        os.chdir(problem_repo_path)

        git_cmd = ['git'] + git_cmd

        p = subprocess.Popen(
            git_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = str(p.stdout.read(), encoding='utf-8')
        stderr = str(p.stderr.read(), encoding='utf-8')

        p.stdout.close()
        p.stderr.close()

        os.chdir(cwd_backup)

        self.assertFalse(stderr, msg=stderr)

        txt = None

        # search for the line of interest
        for line in stdout.splitlines():
            if sha in line:
                txt = line
                break

        self.assertIsNotNone(txt, "Unable to find input string\n%s" % stdout)

        # done identifying the input string

        return txt

    def test_get_commit_dict_03(self):

        txt = '{\'sha\':\'94e4ecc8bd8d02121b0824b14c5e7fed4459e2f8\', \'author\':u\'\'\'name\'\'\', \'email\':u\'email@email.com\', \'date\':\'Fri Mar 30 12:02:40 2018 +0900\', \'subject\': u\'\'\'"""가 print 명령어를 반복하지 않아도 되게 한다. 백슬래쉬를 사용하는 방법. (줄을 변경하게 함. 엔터효과)\\\\\\\'\'\'}'

        sha = '94e4ecc8bd8d02121b0824b14c5e7fed4459e2f8'
        author = u'name'
        email = u'email@email.com'
        date = 'Fri Mar 30 12:02:40 2018 +0900'
        subject = u'''"""가 print 명령어를 반복하지 않아도 되게 한다. 백슬래쉬를 사용하는 방법. (줄을 변경하게 함. 엔터효과)\\\\\\'''

        txt = self.get_git_log_commit_line(
            sha,
            author,
            email, date, subject,
        )

        result = self.e.get_commit_dict(txt)

        expected = {
            'sha': sha,
            'author': author,
            'email': email,
            'date': date,
            'subject': subject,
        }

        # """가 print 명령어를 반복하지 않아도 되게 한다.
        # 백슬래쉬를 사용하는 방법. (줄을 변경하게 함. 엔터효과)\\\
        self.maxDiff = None
        self.assertEqual(expected['sha'], result['sha'])
        self.assertEqual(expected['date'], result['date'])
        self.assertEqual(expected['subject'], result['subject'])


class TestSysArgv(unittest.TestCase):
    def setUp(self):
        self.txt = "# comment 1\n" \
            "# comment 2\n" \
            "# comment 3\n" \
            "import sys\n" \
            "\n" \
            "a, b, c = sys.argv\n" \
            "\n" \
            "print('a = %s' % a)\n" \
            "print('b = %s' % b)\n" \
            "print('c = %s' % c)\n"

    def test_is_sys_argv_00_true(self):

        result = progress.is_sys_argv(self.txt)

        self.assertTrue(result)

    def test_is_argv_00_true(self):

        result = progress.is_argv(self.txt)

        self.assertTrue(result)

    def test_get_argn(self):

        result = progress.get_argn(os.path.join(
            os.path.split(__file__)[0], 'sys_argv_example_00.py'))

        expected = 3

        self.assertEqual(expected, result)


class TestFromSysImportArgv(unittest.TestCase):
    def setUp(self):
        self.txt = "# comment 1\n" \
            "# comment 2\n" \
            "# comment 3\n" \
            "from sys import argv\n" \
            "\n" \
            "a, b = argv\n" \
            "\n" \
            "print('a = %s' % a)\n" \
            "print('b = %s' % b)\n"

    def test_is_sys_argv_00_true(self):

        result = progress.is_from_sys_argv(self.txt)

        self.assertTrue(result)

    def test_get_argn(self):

        result = progress.get_argn(os.path.join(os.path.split(__file__)[
                                   0], 'from_sys_argv_example_00.py'))

        expected = 2

        self.assertEqual(expected, result)

    def test_is_argv_00_true(self):

        result = progress.is_argv(self.txt)

        self.assertTrue(result)


class TestRepoEvalCountOneCommitLogTimeSetting(unittest.TestCase):
    def setUp(self):
        # for consistency
        self.after_date_str = '2014-04-30 +0900'
        self.before_date_str = '2014-06-01 +0900'

        strptime_format = '%Y-%m-%d %z'

        self.after_date_struct = time.strptime(
            self.after_date_str, strptime_format)
        self.after_date_datetime = datetime.datetime.strptime(
            self.after_date_str, strptime_format)

        self.before_date_struct = time.strptime(
            self.before_date_str, strptime_format)
        self.before_date_datetime = datetime.datetime.strptime(
            self.before_date_str, strptime_format)

        self.e = progress.RepoEvalCountOneCommitLog(
            after=time.strftime('%Y-%m-%d', self.after_date_struct),
            before=time.strftime('%Y-%m-%d', self.before_date_struct),
        )

    def tearDown(self):
        del self.e
        del self.before_date_struct, self.after_date_struct

    def test_constructor_time_setting(self):
        result = self.e.get_git_cmd(self.e.after, self.e.before)

        command = list(result)
        command.insert(0, 'git')

        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = str(p.stdout.read(), 'utf-8')
        p.stdout.close()

        # git log command should not fail
        self.assertNotEqual(stdout, 'FAIL', msg=result)

        # for debugging
        # print('\ncommand = {cmd}'.format(cmd=command))
        for k, line in enumerate(stdout.splitlines()):
            if line.startswith('{'):
                commit_dict = ast.literal_eval(line)
                commit_date_str = commit_dict['date']
                # print(k, commit_date_str)
                commit_datetime = datetime.datetime.strptime(commit_date_str,
                                                             # Wkd Mnt dd hh:mm:ss yyyy +tmzn
                                                             # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
                                                             "%a %b %d %H:%M:%S %Y %z")

                msg = 'line = %d' % k

                self.assertGreater(
                    commit_datetime, self.after_date_datetime, msg=msg)
                self.assertLess(commit_datetime,
                                self.before_date_datetime, msg=msg)


if "__main__" == __name__:
    unittest.main()
