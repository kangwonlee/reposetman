import configparser
import os
import sys
import tempfile
import unittest

sys.path.insert(0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )
    )
)

import checkout_due_date as cdd


class TestGetArgParser(unittest.TestCase):
    def setUp(self):
        self.p = cdd.get_arg_parser()

    def tearDown(self):
        del self.p

    def test_get_arg_parser_config_filename(self):
        namespace = self.p.parse_args(['--config', 'config_filename.cfg'])

        self.assertIn('config', namespace)
        self.assertEqual('config_filename.cfg', namespace.config)
        self.assertFalse(namespace.date)

    def test_get_arg_parser_date(self):
        namespace = self.p.parse_args(['--date', '2019-06-08'])

        self.assertIn('date', namespace)
        self.assertEqual(namespace.date, '2019-06-08')
        self.assertEqual(namespace.time, '00:00:00')

    def test_get_arg_parser_date_time(self):
        namespace = self.p.parse_args(['--date', '2019-06-08', '--time', "01:23:45"])

        self.assertIn('date', namespace)
        self.assertEqual(namespace.date, '2019-06-08')
        self.assertIn('time', namespace)
        self.assertEqual(namespace.time, '01:23:45')


class TestGenRepoPath(unittest.TestCase):
    def setUp(self):
        self.list_file = tempfile.NamedTemporaryFile(
            suffix='.txt',
            mode='wt',
            encoding='utf-8',
            )

        self.list_file.write(
            "가나다(2082652342) (03.11 오후 02:33)\n"
            "\n"
            "2082652342 가나다  https://github.com/CPF18A/18pfa_lpthw-abc.git\n"
            "\n"
            "라마바(2018007194) (03.11 오후 02:33)\n"
            "\n"
            "2018007194 라마바 https://def@github.com/CPF18A/18pfa_lpthw-def.git\n"
            "\n"
            "사아자(2017958076) (03.11 오후 02:33)\n"
            "\n"
            "2017958076 사아자 라마바 https://github.com/CPF18A/18pfa_lpthw-ghi.git\n"
        )

        self.expected_list = [
            '18pfa_lpthw-abc',
            '18pfa_lpthw-def',
            '18pfa_lpthw-ghi',
        ]

        self.list_file.seek(0)

        self.config = configparser.ConfigParser()
        self.config['operation'] = {
            'sections':['a']
        }

        self.rel_path = 'rel_path'

        self.config['a'] = {
            'before': 'due date',
            'folder': self.rel_path,
            'list': self.list_file.name,
        }

    def tearDown(self):
        del self.list_file
        del self.config

    def test_gen_arg_parser(self):
        expected_full_path_list = [
            os.path.join(os.getcwd(), self.rel_path, proj)
            for proj in self.expected_list
        ]

        for path, due in cdd.gen_repo_path(self.config):
            self.assertIn(path, expected_full_path_list)
            self.assertEqual(due, self.config['a']['before'], msg=due)


if "__main__" == __name__:
    unittest.main()
