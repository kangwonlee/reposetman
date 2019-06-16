import os
import sys
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
    def test_get_arg_parser_config_filename(self):
        p = cdd.get_arg_parser()

        namespace = p.parse_args(['--config', 'config_filename.cfg'])

        self.assertIn('config', namespace)
        self.assertEqual('config_filename.cfg', namespace.config)
        self.assertFalse(namespace.date)


if "__main__" == __name__:
    unittest.main()
