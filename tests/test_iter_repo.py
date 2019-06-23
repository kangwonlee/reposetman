import ast
import configparser
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)))

import iter_repo


class TestIterRepo(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config['operation'] = {
            'sections': ['a', 'b']
        }

        self.list_file_a = tempfile.NamedTemporaryFile(
            suffix='.txt',
            mode='wt',
            encoding='utf-8',
        )

        self.list_file_a.write(
            "가나다(2082652342) (03.11 오후 02:33)\n"
            "\n"
            "2082652342 가나다  https://github.com/CPF18A/18pfa_lpthw-abc\n"
            "\n"
            "라마바(2018007194) (03.11 오후 02:33)\n"
            "\n"
            "2018007194 라마바 https://def@github.com/CPF18A/18pfa_lpthw-def\n"
            "\n"
            "사아자(2017958076) (03.11 오후 02:33)\n"
            "\n"
            "2017958076 사아자 라마바 https://github.com/CPF18A/18pfa_lpthw-ghi\n"
        )

        self.expected_list_a = [
            '18pfa_lpthw-abc',
            '18pfa_lpthw-def',
            '18pfa_lpthw-ghi',
        ]

        self.list_file_a.seek(0)

        self.rel_path_a = 'rel_path_a'

        self.config['a'] = {
            'before': 'due date',
            'folder': self.rel_path_a,
            'list': self.list_file_a.name,
        }

        self.list_file_b = tempfile.NamedTemporaryFile(
            suffix='.txt',
            mode='wt',
            encoding='utf-8',
        )

        self.list_file_b.write(
            "jkl(2082652342) (03.11 오후 02:33)\n"
            "\n"
            "2082652342 jkl  https://github.com/CPF18B/18pfb_lpthw-jkl.git\n"
            "\n"
            "mno(2018007194) (03.11 오후 02:33)\n"
            "\n"
            "2018007194 mno https://mno@github.com/CPF18B/18pfb_lpthw-mno.git\n"
            "\n"
            "pqr(2017958076) (03.11 오후 02:33)\n"
            "\n"
            "2017958076 pqr stu https://github.com/CPF18B/18pfb_lpthw-pqr.git\n"
        )

        self.expected_list_b = [
            '18pfb_lpthw-jkl',
            '18pfb_lpthw-mno',
            '18pfb_lpthw-pqr',
        ]

        self.list_file_b.seek(0)

        self.rel_path_b = 'rel_path_b'

        self.config['b'] = {
            'before': 'due date b',
            'folder': self.rel_path_b,
            'list': self.list_file_b.name,
        }

    def tearDown(self):
        del self.list_file_a
        del self.list_file_b
        del self.config

    def test_get_section_list(self):
        self.assertSequenceEqual(iter_repo.get_section_list(self.config), 
        ast.literal_eval(self.config['operation']['sections']),)


if "__main__" == __name__:
    unittest.main()
