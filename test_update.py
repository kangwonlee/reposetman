import unittest

import regex_test as ret

# test case for project id related functions
"""
가나다(2082652342) (03.11 오후 02:33)

2082652342 가나다  https://abc@github.com/CPF18A/18pfa_lpthw-abc.git

라마바(2018007194) (03.11 오후 02:33)

2018007194 라마바 https://def@github.com/CPF18A/18pfa_lpthw-def.git

사아자(2017958076) (03.11 오후 02:33)

2017958076 사아자 https://ghi@github.com/CPF18A/18pfa_lpthw-ghi.git
"""


class TestUpdate(unittest.TestCase):
    def test_get_proj_id_list(self):
        # function under test
        projid_list = ret.get_proj_id_list(__file__)
        self.assertIn("18pfa_lpthw-abc", projid_list)
        self.assertIn("18pfa_lpthw-def", projid_list)
        self.assertIn("18pfa_lpthw-ghi", projid_list)

    def test_get_proj_info(self):
        # function under test
        proj_info_dict = ret.get_proj_info(__file__)

        # print("proj_info_dict =", proj_info_dict)

        expected_dict = {
            "18pfa_lpthw-abc": {
                "id_number": "2082652342",
                "name": "가나다",
                "github_id": "abc",
                "domain": "github.com",
            },
            "18pfa_lpthw-def": {
                "id_number": "2018007194",
                "name": "라마바",
                "github_id": "def",
                "domain": "github.com",
            },
            "18pfa_lpthw-ghi": {
                "id_number": "2017958076",
                "name": "사아자",
                "github_id": "ghi",
                "domain": "github.com",
            },
        }

        for expected_repo_name in expected_dict:
            self.assertIn(expected_repo_name, proj_info_dict)
            # just checking some of the keys and values
            for key in expected_dict[expected_repo_name]:
                self.assertIn(key, proj_info_dict[expected_repo_name])
                self.assertEqual(
                    expected_dict[expected_repo_name][key],
                    proj_info_dict[expected_repo_name][key],
                )

    def test_get_proj_id(self):
        # function under test
        result = ret.get_proj_id(
            "2082652342 가나다  https://abc@github.com/CPF18A/18pfa_lpthw-abc.git"
        )
        expected = "18pfa_lpthw-abc"
        self.assertIn(expected, result)

    def test_get_proj_info_line(self):
        # function under test
        result = ret.get_proj_info_line(
            "2082652342 가나다  https://abc@github.com/CPF18A/18pfa_lpthw-abc.git"
        )
        expected = [
            {
                "id_number": "2082652342",
                "name": "가나다",
                "github_id": "abc",
                "domain": "github.com",
                "group": "CPF18A",
                "repo_name": "18pfa_lpthw-abc",
            }
        ]

        self.maxDiff = None
        self.assertDictEqual(expected[0], result[0], msg="result = %r" % result)


if "__main__" == __name__:
    unittest.main()
