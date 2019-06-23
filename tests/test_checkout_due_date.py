import ast
import configparser
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

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
        namespace = self.p.parse_args(
            ['--date', '2019-06-08', '--config', 'config_filename.cfg'])

        self.assertIn('date', namespace)
        self.assertEqual(namespace.date, '2019-06-08')
        self.assertEqual(namespace.time, '00:00:00')

    def test_get_arg_parser_date_time(self):
        namespace = self.p.parse_args(
            ['--date', '2019-06-08', '--time', "01:23:45", '--config', 'config_filename.cfg'])

        self.assertIn('date', namespace)
        self.assertEqual(namespace.date, '2019-06-08')
        self.assertIn('time', namespace)
        self.assertEqual(namespace.time, '01:23:45')


if "__main__" == __name__:
    unittest.main()
