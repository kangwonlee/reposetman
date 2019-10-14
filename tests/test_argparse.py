import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )
    )
)

import progress


class TestArgParser(unittest.TestCase):
    def test_parse_args_usual(self):
        config_filename = 'config.cfg'

        input_arguments  = ['script.py', config_filename]
        result_namespace = progress.parse_args(input_arguments)

        self.assertEqual(config_filename, result_namespace.config_filename)
        self.assertTrue(result_namespace.multiprocessing)

    def test_parse_args_disable_multiprocessing(self):
        config_filename = 'config.cfg'
        input_arguments  = ['script.py', config_filename, '--no-multiprocessing',]
        result_namespace = progress.parse_args(input_arguments)

        self.assertTrue(result_namespace.config_filename)
        self.assertTrue(result_namespace.config_filename.endswith('cfg'))
        self.assertFalse(result_namespace.multiprocessing)


class TestConfig2Bool(unittest.TestCase):
    def test_confg2bool_False(self):
        self.assertFalse(progress.config2bool('False'))

    def test_confg2bool_null(self):
        self.assertFalse(progress.config2bool(''))

    def test_confg2bool_True(self):
        self.assertTrue(progress.config2bool('True'))


if "__main__" == __name__:
    unittest.main()
