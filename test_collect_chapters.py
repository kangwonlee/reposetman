import configparser
import pprint
import unittest

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
