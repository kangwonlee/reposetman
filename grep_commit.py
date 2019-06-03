"""
Grep commits

Find a string within the git logs of repositories under `data` folder.

Example:
$ python grep_commit.py [root path]
** path to the first repository **
"""

import os
import sys

import git


def main(argv):
    if 1 < len(argv):
        path_to_section = os.path.abspath(argv[0])
        string_to_find = argv[1]

    else:
        path_to_section = os.path.join("data")
        string_to_find = "ex01"

    for full_path in gen_repo(path_to_section):
        if os.path.isdir(full_path):
            cwd = os.getcwd()
            os.chdir(full_path)

            result = git.git_common_list(["log"], b_verbose=False)
            if string_to_find in result[0]:
                print(full_path)

            os.chdir(cwd)


def gen_repo(root):
    for path in os.listdir(root):
        full_path = os.path.abspath(os.path.join(root, path))
        for path2 in os.listdir(full_path):
            full_path2 = os.path.abspath(os.path.join(full_path, path2))
            if os.path.isdir(full_path):
                yield full_path2


if "__main__" == __name__:
    main(sys.argv[1:])
