import ast
import configparser
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )
    )
)

import progress


def get_temp_filename(mode='w+t'):
    f = tempfile.NamedTemporaryFile(mode=mode)
    name = f.name

    f.close()
    return name


class BaseTestBuildMessageList(unittest.TestCase):
    config_filename = 'test_build_todo_list.cfg'

    def init_test_cfg_build_todo_list(self):
        config = configparser.ConfigParser()

        self.section_name = 'test_section'

        config['operation'] = {
            'python_path': shutil.which('python'),
            'sections': [self.section_name],
        }

        config[self.section_name] = {
            'todo_list_file': 'test-todo.json',
            'last_sent_file': 'test-todo-lastsent.txt',
            'comment_period_days': '7',
            'organization': 'test-group',
        }

        with open(self.config_filename, 'w') as cfg_file:
            config.write(cfg_file)

    def init_all_outputs(self):

        send_sha = ['sha_send_01', 'sha_send_11']

        # input case
        all_outputs_dict = {
            'repo0': {
                'do not send 00': 'N/A',
                'send 01': {
                    'sha': send_sha[0],
                    'grammar pass': False,
                },
                'do not send 02': {
                    'sha': 'sha_do_not_send_02',
                    'stdout': 256,
                    'stderr': 0,
                },
            },  # repo 0
            'repo1': {
                'do not send 10': 'N/A',
                'send 11': {
                    'sha': send_sha[1],
                    'grammar pass': False,
                },
            },  # repo 1
        }  # all_outputs

        all_outputs = progress.RepoTable()
        for repo in all_outputs_dict:
            for filename in all_outputs_dict[repo]:
                all_outputs.set_row_column(
                    repo, filename, all_outputs_dict[repo][filename])

        return all_outputs, send_sha

    def setUp(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_filename):
            self.init_test_cfg_build_todo_list()

        self.config.read(self.config_filename)
        self.section_list = ast.literal_eval(
            self.config['operation']['sections'])

        self.all_outputs, self.send_sha = self.init_all_outputs()

    def tearDown(self):
        del self.all_outputs
        del self.config
        del self.send_sha


class TestBuildTodoListGrammar(BaseTestBuildMessageList):
    def setUp(self):
        super().setUp()

        self.object_under_test = progress.MessageListBuilderGrammar(
            self.config, 
            self.section_list[0], 
            self.all_outputs, 
            b_verbose=True
        )

    def tearDown(self):

        del self.object_under_test

        super().tearDown()

    def test_build_todo_list_grammar(self):

        section_name = self.section_list[0]

        # force always run
        self.config[section_name]['last_sent_file'] = get_temp_filename()
        if os.path.exists(self.config[section_name]['last_sent_file']):
            os.remove(self.config[section_name]['last_sent_file'])

        # function under test
        result_list = self.object_under_test.build_message_list()

        send_sha = list(self.send_sha)

        for send_record_dict in result_list:
            if 'do not send' not in send_record_dict:
                if send_record_dict['sha'] in send_sha:
                    send_sha.remove(send_record_dict['sha'])
                else:
                    raise ValueError(
                        '\n'
                        f'send_record_dict = {send_record_dict}'
                    )

        # check all sent
        self.assertFalse(send_sha)

        # remove temp file
        if os.path.exists(self.config[section_name]['last_sent_file']):
            os.remove(self.config[section_name]['last_sent_file'])


class TestBuildTodoSupportFunctions(unittest.TestCase):
    def test_write_last_sent(self):
        gmtime_sec = time.time()

        with tempfile.NamedTemporaryFile(mode='w+t', delete=False) as f:
            # function under test
            progress.write_last_sent(f, gmtime_sec=gmtime_sec)
            name = f.name

        # may not be the best practice to test two functions in one method

        last_sent_gmtime_sec = progress.get_last_sent_gmtime_sec(name)

        try:
            self.assertAlmostEqual(last_sent_gmtime_sec, gmtime_sec)
            os.remove(name)
        except BaseException as e:
            if os.path.exists(name):
                os.remove(name)
            raise e

    def test_is_too_frequent_do_not_send(self):
        gmtime_sec = time.time()

        close_last_send_gmtime_sec = gmtime_sec - 10
        # function under test
        result = progress.is_too_frequent(
            close_last_send_gmtime_sec, comment_period_days=1, b_verbose=False)

        self.assertTrue(result, msg=(
            f"close_last_send_gmtime_sec = {close_last_send_gmtime_sec}\n"
        )
        )

    def test_is_too_frequent_send(self):
        gmtime_sec = time.time()

        far_last_send_gmtime_sec = gmtime_sec - 10 * 24 * 3600
        # function under test
        result = progress.is_too_frequent(
            far_last_send_gmtime_sec, comment_period_days=1, b_verbose=False)

        self.assertFalse(result, msg=(
            f"far_last_send_gmtime_sec = {far_last_send_gmtime_sec}\n"
        )
        )

    def test_get_last_sent_gmtime_sec_available(self):
        last_sent_filename = get_temp_filename()

        gmtime_sec = time.time()

        with open(last_sent_filename, 'wt') as f:
            f.write(str(gmtime_sec))
        # function under test
        last_sent_gmtime_sec = progress.get_last_sent_gmtime_sec(
            last_sent_filename)

        self.assertAlmostEqual(last_sent_gmtime_sec, gmtime_sec)

    def test_get_last_sent_gmtime_sec_not_available(self):
        last_sent_filename = get_temp_filename()

        gmtime_sec = time.time()
        # function under test
        last_sent_gmtime_sec = progress.get_last_sent_gmtime_sec(
            last_sent_filename)

        self.assertLess(last_sent_gmtime_sec, gmtime_sec)


class TestBuildTodoListPound(BaseTestBuildMessageList):
    def init_pound_count(self):

        # input case
        pound_comments_dict = {
            'repo0': {
                'do not send 00': 'N/A',
                'send 01': 0,
                'do not send 02': 300,
            },  # repo 0
            'repo1': {
                'do not send 10': 'N/A',
                'send 11': 0,
            },  # repo 1
        }  # pound_counts

        pound_counts = progress.RepoTable()
        for repo in pound_comments_dict:
            for filename in pound_comments_dict[repo]:
                pound_counts.set_row_column(
                    repo, filename, pound_comments_dict[repo][filename])

        return pound_counts

    def init_commit_counts(self):
        # input case
        commit_comments_dict = {
            'repo0': {
                'do not send 00': 1,
                'send 01': 1,
                'do not send 02': 0,
            },  # repo 0
            'repo1': {
                'do not send 10': 1,
                'send 11': 2,
            },  # repo 1
        }  # commit_comments_dict

        commit_comments = progress.RepoTable()
        for repo in commit_comments_dict:
            for filename in commit_comments_dict[repo]:
                commit_comments.set_row_column(
                    repo, filename, commit_comments_dict[repo][filename])

        return commit_comments

    def setUp(self):
        super().setUp()

        self.pound_counts = self.init_pound_count()
        self.commit_counts = self.init_commit_counts()

        self.result_dict = {
            'count_commits': {'table': self.commit_counts},
            'pound_counts': {'table': self.pound_counts},
            'run_all': {'table': self.all_outputs},
        }

        self.object_under_test = progress.MessageListBuilderPound(
            self.config, self.section_list[0], self.result_dict, b_verbose=True)

    def tearDown(self):
        del self.object_under_test

        del self.result_dict

        del self.pound_counts
        del self.commit_counts

        super().tearDown()

    def test_build_message_list_pound(self):

        section_name = self.section_list[0]

        # force always run
        self.config[section_name]['last_sent_file'] = get_temp_filename()
        if os.path.exists(self.config[section_name]['last_sent_file']):
            os.remove(self.config[section_name]['last_sent_file'])

        # function under test
        result_list = self.object_under_test.build_message_list()

        self.assertTrue(result_list)

        send_sha = list(self.send_sha)

        for send_record_dict in result_list:
            if 'do not send' not in send_record_dict:
                if send_record_dict['sha'] in send_sha:
                    send_sha.remove(send_record_dict['sha'])
                else:
                    raise ValueError(
                        '\n'
                        f'send_record_dict = {send_record_dict}'
                    )

        # check all sent
        self.assertFalse(send_sha)

        # remove temp file
        if os.path.exists(self.config[section_name]['last_sent_file']):
            os.remove(self.config[section_name]['last_sent_file'])


if "__main__" == __name__:
    unittest.main()
