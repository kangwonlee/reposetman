import configparser
import os
import shutil
import tempfile
import unittest

import progress


def get_temp_filename(mode='w+t'):
    f = tempfile.NamedTemporaryFile(mode=mode)
    name = f.name

    f.close()
    return name


class TestBuildTodoListGrammar(unittest.TestCase):
    config_filename = 'test_build_todo_list.cfg'
    def init_test_cfg_build_todo_list(self):
        if not os.path.exists(self.config_filename):
            config = configparser.ConfigParser()

            config['operation'] = {
                'python_path': shutil.which('python'),
                'todo_list_file' : 'cpf19-lpthw-todo.json',
                'last_sent_file' : 'cpf19-lpthw-todo-lastsent.txt',
                'comment_period_days' : '7',
                'organization' : 'kpumecpf',
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
            }, # repo 0
            'repo1': {
                    'do not send 10': 'N/A',
                    'send 11': {
                        'sha': send_sha[1],
                        'grammar pass': False,
                        },
            }, # repo 1
        } # all_outputs

        all_outputs = progress.RepoTable()
        for repo in all_outputs_dict:
            for filename in all_outputs_dict[repo]:
                all_outputs.set_row_column(repo, filename, all_outputs_dict[repo][filename])

        return all_outputs, send_sha

    def setUp(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_filename):
            self.init_test_cfg_build_todo_list()

        self.config.read(self.config_filename)

        self.all_outputs, self.send_sha = self.init_all_outputs()

    def tearDown(self):
        del self.config
        del self.all_outputs
        del self.send_sha

    def test_build_todo_list_grammar(self):
        # force always run
        self.config['operation']['last_sent_file'] = get_temp_filename()
        if os.path.exists(self.config['operation']['last_sent_file']):
            os.remove(self.config['operation']['last_sent_file'])

        # function under test
        result_list = progress.build_todo_list_grammar(self.config, self.all_outputs,)

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
        if os.path.exists(self.config['operation']['last_sent_file']):
            os.remove(self.config['operation']['last_sent_file'])
