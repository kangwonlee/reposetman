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

import progress
import tempf

folder = os.getcwd()


class TestGettingConfigFilename(unittest.TestCase):
    def test_get_cfg_filename_from_argv_yes(self):
        input_list = ['this']

        # function under test
        result = progress.get_cfg_filename_from_argv(input_list)

        self.assertIsInstance(result, str)

        expected = input_list[0]
        self.assertEqual(expected, result)

    def test_get_cfg_filename_from_argv_none(self):
        input_list = []

        # function under test
        result = progress.get_cfg_filename_from_argv(input_list)

        self.assertIsInstance(result, str)

        expected = 'progress.cfg'
        self.assertEqual(expected, result)


class TestGettingConfig(unittest.TestCase):
    def setUp(self):
        self.config_filename = tempf.get_tempfile_name('.cfg')
        with open(self.config_filename, 'w', encoding='utf-8') as f:
            f.write(
                '[config]\n'
                'sample=sample\n'
            )

    def tearDown(self):
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)

    def test_get_config_from_filename(self):
        result = progress.get_config_from_filename(self.config_filename)

        self.assertIsInstance(result, configparser.ConfigParser)
        self.assertIn('config', result)
        self.assertIn('sample', result['config'])

    def test_get_config_from_argv(self):
        input_list = [self.config_filename, 'a', 'b', 'c']
        result = progress.get_config_from_argv(input_list)

        self.assertIsInstance(result, configparser.ConfigParser)
        self.assertIn('config', result)
        self.assertIn('sample', result['config'])


if "__main__" == __name__:
    unittest.main()
