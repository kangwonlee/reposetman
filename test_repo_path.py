import unittest
import repo_path


class TestRepoPath(unittest.TestCase):
    def test_get_repo_name_from_url(self):
        # ending with .git
        input_text = 'https://github.com/abc/def.git'
        # function under test
        result = repo_path.get_repo_name_from_url(input_text)
        expected = 'def'
        self.assertEqual(expected, result)

    def test_get_repo_name_from_url_ending_with_slash(self):
        # what if a url ends with a '/'?
        input_text = 'https://github.com/abc/def/'
        # function under test
        result = repo_path.get_repo_name_from_url(input_text)
        expected = 'def'
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
