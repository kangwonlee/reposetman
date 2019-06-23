import ast
import configparser
import os
import pprint
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

    def test_gen_section(self):
        self.assertSequenceEqual(list(iter_repo.gen_section(self.config)), ast.literal_eval(
            self.config['operation']['sections']),)


class TestReadByteDecode(unittest.TestCase):
    def setUp(self):
        self.txt = """위키백과 기여자, "강화 학습," 위키백과, , https://ko.wikipedia.org/w/index.php?title=%EA%B0%95%ED%99%94_%ED%95%99%EC%8A%B5&oldid=24452709 (2019년 6월 23일에 접근).
강화 학습(Reinforcement learning)은 기계 학습의 한 영역이다. 행동심리학에서 영감을 받았으며, 어떤 환경 안에서 정의된 에이전트가 현재의 상태를 인식하여, 선택 가능한 행동들 중 보상을 최대화하는 행동 혹은 행동 순서를 선택하는 방법이다. 이러한 문제는 매우 포괄적이기 때문에 게임 이론, 제어이론, 운용 과학, 정보 이론, 시뮬레이션 기반 최적화, 다중 에이전트 시스템, 군집 지능, 통계학, 유전 알고리즘 등의 분야에서도 연구된다. 운용 과학과 제어 이론에서 강화 학습이 연구되는 분야는 "근사 동적 계획법"이라고 불린다. 또한 최적화 제어 이론에서도 유사한 문제를 연구하지만, 대부분의 연구가 최적해의 존재와 특성에 초점을 맞춘다는 점에서 학습과 근사의 측면에서 접근하는 강화 학습과는 다르다. 경제학과 게임 이론 분야에서 강화 학습은 어떻게 제한된 합리성 하에서 평형이 일어날 수 있는지를 설명하는 데에 사용되기도 한다.

강화 학습에서 다루는 '환경'은 주로 마르코프 결정 과정으로 주어진다.[1] 마르코프 결정 과정 문제를 해결하는 기존의 방식과 강화 학습이 다른 지점은, 강화 학습은 마르코프 결정 과정에 대한 지식을 요구하지 않는다는 점과, 강화 학습은 크기가 매우 커서 결정론적 방법을 적용할 수 없는 규모의 마르코프 결정 과정 문제를 다룬다는 점이다.

강화 학습은 또한 입출력 쌍으로 이루어진 훈련 집합이 제시되지 않으며, 잘못된 행동에 대해서도 명시적으로 정정이 일어나지 않는다는 점에서 일반적인 지도 학습과 다르다. 대신, 강화학습의 초점은 학습 과정에서의(on-line) 성능이며, 이는 탐색(exploration)과 이용(exploitation)의 균형을 맞춤으로써 제고된다.[2] 탐색과 이용의 균형 문제 강화 학습에서 가장 많이 연구된 문제로, 다중 슬롯 머신 문제(multi-armed bandit problem)와 유한한 마르코프 결정 과정 등에서 연구되었다.
"""

        self.utf_file = tempfile.NamedTemporaryFile(mode='wt', suffix='.txt', encoding='utf-8')
        self.utf_file.write(self.txt)
        self.utf_file.seek(0)

        self.cp9_file = tempfile.NamedTemporaryFile(mode='wt', suffix='.txt', encoding='cp949')
        self.cp9_file.write(self.txt)
        self.cp9_file.seek(0)

    def tearDown(self):
        del self.utf_file
        del self.cp9_file
        del self.txt

    def test_read_b_decode_utf8(self):
        result = iter_repo.read_b_decode(self.utf_file.name)
        self.assertEqual(result, self.txt)

    def test_read_b_decode_cp949(self):
        result = iter_repo.read_b_decode(self.cp9_file.name)
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

        self.input_file = tempfile.NamedTemporaryFile(suffix='.txt', mode='wt', encoding='utf-8')

        self.input_file.write(self.txt)
        self.input_file.seek(0)

    def tearDown(self):
        del self.txt
        del self.input_file

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

        self.config[self.sections[0]] = {
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

        self.config[self.sections[1]] = {
            'before': 'due date b',
            'folder': self.rel_path_b,
            'list': self.list_file_b.name,
        }

    def tearDown(self):
        del self.list_file_a
        del self.list_file_b
        del self.config

    def test_iter_repo_path(self):
        expected_full_path_list = [
            os.path.join(os.getcwd(), self.rel_path_a, proj)
            for proj in self.expected_list_a
        ] + [
            os.path.join(os.getcwd(), self.rel_path_b, proj)
            for proj in self.expected_list_b
        ]

        for path, due in iter_repo.iter_repo_path(self.config, b_assert=False):
            self.assertIn(path, expected_full_path_list)
            self.assertTrue(due, msg=due)


if "__main__" == __name__:
    unittest.main()
