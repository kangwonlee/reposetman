import configparser
import copy
import os
import pprint
import sys
import tempfile
import unittest
import urllib.parse as up


sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )
    )
)


import collect_chapters as col


class TestCollectChapters(unittest.TestCase):
    def test_transpose_dict(self):

        user_id_list = (
            'user_id_00',
            'user_id_01',
            'user_id_02',
            'user_id_03',
        )

        url_a_list = (
            'url_a_00',
            'url_a_01',
            'url_a_02',
            'url_a_03',
        )

        url_b_list = (
            'url_b_00',
            'url_b_01',
            'url_b_02',
            'url_b_03',
        )

        sections_dict = {
            'section_a': {
                'urls': url_a_list[:3],
                'user_ids': user_id_list[:3],
            },
            'section_b': {
                'urls': url_b_list[1:],
                'user_ids': user_id_list[1:],
            },
        }

        result_dict = col.transpose_dict(sections_dict)
        pprint.pprint(result_dict)

        self.assertSetEqual(
            set(user_id_list),
            set(result_dict.keys()),
        )

        for user in result_dict:
            self.assertIsInstance(result_dict[user], dict)

            for section in result_dict[user]:
                self.assertIn(section, sections_dict.keys())

                url = result_dict[user][section]
                in_list = list(
                    map(lambda x: x in url, url_a_list + url_b_list))
                self.assertTrue(any(in_list))


class TestSetUserIdsBase(unittest.TestCase):
    def setUp(self):
        self.sections_dict = self.get_sections_dict()
        self.config = self.get_config()
        self.id_set = set(['abc', 'def', 'ghi-eca00a'])

    @staticmethod
    def get_sections_dict():
        return {
            'cls12a_00':{
                'urls':[
                    'https://github.com/cls12a/cls12a-nmisp-00-abc',
                    'https://github.com/cls12a/cls12a-nmisp-00-def',
                    'https://github.com/cls12a/cls12a-nmisp-00-ghi-eca00a',
                ]
            },
            'cls12a_01':{
                'urls':[
                    'https://github.com/cls12a/cls12a-nmisp-01-abc',
                    'https://github.com/cls12a/cls12a-nmisp-01-def',
                    'https://github.com/cls12a/cls12a-nmisp-01-ghi-eca00a',
                ]
            },
            'cls12a_tutorial':{
                'urls':[
                    'https://github.com/cls12a/cls12a-nmisp-tutorial-abc',
                    'https://github.com/cls12a/cls12a-nmisp-tutorial-def',
                    'https://github.com/cls12a/cls12a-nmisp-tutorial-ghi-eca00a',
                ]
            },
        }

    @staticmethod
    def get_config():
        config = configparser.ConfigParser()

        config.read_dict(
            {
                'operation':{
                    'sections': "['cls12a_00', 'cls12a_01', 'cls12a_tutorial']"
                },
                'cls12a_00':{'repo_prefix': 'cls12a-nmisp-00-'},
                'cls12a_01':{'repo_prefix': 'cls12a-nmisp-01-'},
                'cls12a_tutorial':{'repo_prefix': 'cls12a-nmisp-tutorial-'},
            }
        )

        return config


class TestSetUserIds(TestSetUserIdsBase):
    def test_set_user_ids(self):

        url_parse_dict = {
            'cls12a_00': [
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-00-abc'),
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-00-def'),
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-00-ghi-eca00a'),
            ],
            'cls12a_01': [
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-01-abc'),
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-01-def'),
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-01-ghi-eca00a'),
            ],
            'cls12a_tutorial': [
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-tutorial-abc'),
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-tutorial-def'),
                up.urlparse('https://github.com/cls12a/cls12a-nmisp-tutorial-ghi-eca00a'),
            ],
        }

        storage = copy.deepcopy(self.sections_dict)

        # TODO : see if the following function is definitely necessary
        col.set_user_ids(self.config, storage, url_parse_dict)

        expected_set = set(['abc', 'def', 'ghi-eca00a'])

        for _, value in storage.items():
            self.assertIn('user_ids', value)
            self.assertSetEqual(set(value['user_ids']), expected_set)


class TestGetSectionsDict(TestSetUserIdsBase):
    def get_config(self):
        config = super().get_config()

        with tempfile.NamedTemporaryFile('wt', suffix='.txt') as lst_00:
            lst_00_name = os.path.basename(lst_00.name)
        with open(lst_00_name, 'wt', encoding='utf-8') as lst_00:
            lst_00.write(
                '123 abcde https://github.com/cls12a/cls12a-nmisp-00-abc\n'
                '456 fghij https://github.com/cls12a/cls12a-nmisp-00-def\n'
                '789 klmno https://github.com/cls12a/cls12a-nmisp-00-ghi-eca00a\n'
            )

        with tempfile.NamedTemporaryFile('wt', suffix='.txt') as lst_01:
            lst_01_name = os.path.basename(lst_01.name)
        with open(lst_01_name, 'wt', encoding='utf-8') as lst_01:
            lst_01.write(
                '456 fghij https://github.com/cls12a/cls12a-nmisp-01-def\n'
                '123 abcde https://github.com/cls12a/cls12a-nmisp-01-abc\n'
                '789 klmno https://github.com/cls12a/cls12a-nmisp-01-ghi-eca00a\n'
            )

        with tempfile.NamedTemporaryFile('wt', suffix='.txt') as lst_tutorial:
            lst_tutorial_name = os.path.basename(lst_tutorial.name)
        with open(lst_tutorial_name, 'wt', encoding='utf-8') as lst_tutorial:
            lst_tutorial.write(
                '789 klmno https://github.com/cls12a/cls12a-nmisp-tutorial-ghi-eca00a\n'
                '456 fghij https://github.com/cls12a/cls12a-nmisp-tutorial-def\n'
                '123 abcde https://github.com/cls12a/cls12a-nmisp-tutorial-abc\n'
            )

        config['cls12a_00']['list'] = lst_00_name
        config['cls12a_01']['list'] = lst_01_name
        config['cls12a_tutorial']['list'] = lst_tutorial_name

        self.del_these_later = [lst_00_name, lst_01_name, lst_tutorial_name,]

        return config

    def tearDown(self):
        [os.remove(name) for name in self.del_these_later]

    def test_get_sections_dict(self):

        result = col.get_sections_dict(self.config)

        self.assertIsInstance(result, dict)

        self.assertSetEqual(
            set(self.sections_dict.keys()), 
            set(list(result.keys()))
        )

        for section, d in result.items():
            self.assertIn('urls', d)
            self.assertSetEqual(
                set(self.sections_dict[section]['urls']),
                set(d['urls'])
            )
            self.assertIn('user_ids', d)
            self.assertSetEqual(self.id_set, set(d['user_ids']))


if "__main__" == __name__:
    unittest.main()
