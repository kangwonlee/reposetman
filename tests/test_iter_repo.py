import ast
import configparser
import os
import pprint
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import iter_repo
import tempf


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

    def test_gen_section(self):
        self.assertSequenceEqual(list(iter_repo.gen_section(self.config)), ast.literal_eval(
            self.config['operation']['sections']),)


class TestReadByteDecode(unittest.TestCase):
    def setUp(self):
        self.txt = """강화학습"""

        self.utf_file_name = tempf.get_tempfile_name(suffix='.txt')
        with open(self.utf_file_name, 'wt', encoding='utf-8') as utf_file:
            utf_file.write(self.txt)

        self.cp9_file_name = tempf.get_tempfile_name(suffix='.txt')
        with open(self.cp9_file_name, 'wt', encoding='utf-8') as cp9_file:
            cp9_file.write(self.txt)

        self.maxDiff = None

    def tearDown(self):
        os.remove(self.utf_file_name)
        os.remove(self.cp9_file_name)
        del self.txt

    def test_read_b_decode_utf8(self):
        result = iter_repo.read_b_decode(self.utf_file_name)
        self.assertEqual(result, self.txt)

    def test_read_b_decode_cp949(self):
        result = iter_repo.read_b_decode(self.cp9_file_name)
        self.assertEqual(result, self.txt)


class TestGetGithubUrls(unittest.TestCase):
    def setUp(self):
        self.txt = '''
가나다(2082652342) (03.11 오후 02:33)

2082652342 가나다  https://github.com/CPF18B/18pfb_lpthw-jkl

라마바(2018007194) (03.11 오후 02:33)

2018007194 라마바 https://github.com/CPF18A/18pfa_lpthw-def.git

사아자(2017958076) (03.11 오후 02:33)

2017958076 사아자 https://ghi@github.com/CPF18A/18pfa_lpthw-ghi

가나다(2082652342) (03.11 오후 02:33)

2082652342 가나다  https://github.com/CPF 18B/18pfb_lpthw-jkl
'''

        self.expected_url_list = [
            "https://github.com/CPF18B/18pfb_lpthw-jkl",
            "https://github.com/CPF18A/18pfa_lpthw-def.git",
            "https://ghi@github.com/CPF18A/18pfa_lpthw-ghi",
        ]

    def tearDown(self):
        del self.txt

    def test_get_github_urls(self):
        result_list = iter_repo.get_github_urls(self.txt)

        self.assertSequenceEqual(result_list, self.expected_url_list, msg=(
            f"expected = \n{pprint.pformat(self.expected_url_list)}\n"
            f"result = \n{pprint.pformat(result_list)}"
        ))

    def test_iter_github_urls(self):
        result_list = list(iter_repo.iter_github_urls(self.txt))

        self.assertSequenceEqual(result_list, self.expected_url_list, msg=(
            f"expected = \n{pprint.pformat(self.expected_url_list)}\n"
            f"result = \n{pprint.pformat(result_list)}"
        ))


class TestIterGithubUrlsInFile(unittest.TestCase):
    def setUp(self):
        self.txt = '''
가나다(2082652342) (03.11 오후 02:33)

2082652342 가나다  https://github.com/CPF18B/18pfb_lpthw-jkl

라마바(2018007194) (03.11 오후 02:33)

2018007194 라마바 https://github.com/CPF18A/18pfa_lpthw-def.git

사아자(2017958076) (03.11 오후 02:33)

2017958076 사아자 https://ghi@github.com/CPF18A/18pfa_lpthw-ghi

가나다(2082652342) (03.11 오후 02:33)

2082652342 가나다  https://github.com/CPF 18B/18pfb_lpthw-jkl
'''

        self.expected_url_list = [
            "https://github.com/CPF18B/18pfb_lpthw-jkl",
            "https://github.com/CPF18A/18pfa_lpthw-def.git",
            "https://ghi@github.com/CPF18A/18pfa_lpthw-ghi",
        ]

        self.input_file = tempf.write_to_temp_file(self.txt)

    def tearDown(self):
        del self.txt
        os.remove(self.input_file.name)

    def test_iter_github_urls_in_file(self):
        result_list = list(iter_repo.iter_github_urls_in_file(self.input_file.name))

        self.assertSequenceEqual(result_list, self.expected_url_list, msg=(
            f"expected = \n{pprint.pformat(self.expected_url_list)}\n"
            f"result = \n{pprint.pformat(result_list)}"
        ))


class TestIterRepoPath(unittest.TestCase):
    def setUp(self):

        self.sections = ['a', 'b']

        self.config = configparser.ConfigParser()
        self.config['operation'] = {
            'sections': self.sections
        }

        self.list_file_a_name = tempf.get_tempfile_name(suffix='.txt')

        self.list_file_a = open(self.list_file_a_name, 'wt', encoding='utf-8')

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

        self.list_file_a.close()

        self.rel_path_a = 'rel_path_a'

        self.config[self.sections[0]] = {
            'before': 'due date',
            'folder': self.rel_path_a,
            'list': self.list_file_a_name,
        }

        self.list_file_b_name = tempf.get_tempfile_name(suffix='.txt')

        self.list_file_b = open(self.list_file_b_name, 'wt', encoding='utf-8')

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

        self.list_file_b.close()

        self.rel_path_b = 'rel_path_b'

        self.config[self.sections[1]] = {
            'before': 'due date b',
            'folder': self.rel_path_b,
            'list': self.list_file_b_name,
        }

    def tearDown(self):
        os.remove(self.list_file_a_name)
        os.remove(self.list_file_b_name)
        del self.config

    def test_iter_repo_path(self):
        expected_full_path_list = [
            os.path.join(os.getcwd(), self.rel_path_a, proj)
            for proj in self.expected_list_a
        ] + [
            os.path.join(os.getcwd(), self.rel_path_b, proj)
            for proj in self.expected_list_b
        ]

        self.assertSequenceEqual([path for path in iter_repo.iter_repo_path(self.config, b_assert=False)],
            expected_full_path_list
        )

    def test_iter_repo_path_with_due(self):
        expected_full_path_list = [
            os.path.join(os.getcwd(), self.rel_path_a, proj)
            for proj in self.expected_list_a
        ] + [
            os.path.join(os.getcwd(), self.rel_path_b, proj)
            for proj in self.expected_list_b
        ]

        for path, due in iter_repo.iter_repo_path_with_due(self.config, b_assert=False):
            self.assertIn(path, expected_full_path_list)
            self.assertTrue(due, msg=due)

    def test_iter_repo_path_in_section(self):
        expected_full_path_list = [
            os.path.join(os.getcwd(), self.rel_path_a, proj)
            for proj in self.expected_list_a
        ]

        self.assertSequenceEqual([full_path for full_path in iter_repo.iter_repo_path_in_section(self.config, self.sections[0], b_assert=False)],
            expected_full_path_list
        )


if "__main__" == __name__:
    unittest.main()
