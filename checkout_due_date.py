import argparse
import ast
import configparser
import os
import sys

import git
import progress
import regex_test


def main(argv):

    parser = get_arg_parser()

    if argv[1:]:

        namespace = parser.parse_args(argv[1:])

    else:

        parser.parse_args(['--help'])


def gen_section(config):
    sections_list = ast.literal_eval(config['operation']['sections'])

    for section in sections_list:
        yield section


def gen_repo_path(config):

    for section in gen_section(config):
        due_date = config[section]['before']
        repo_path_rel = config[section]['folder']
        list_filename = config[section]['list']
        proj_id_list = regex_test.get_proj_id_list(list_filename)

        for proj_id in proj_id_list:
            full_path_to_repo = os.path.abspath(
                os.path.join(repo_path_rel, proj_id)
            )

            yield full_path_to_repo, due_date


def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='checkout date in yyyy-mm-dd')
    parser.add_argument('--time', help='checkout time in hh:mm:ss', default='00:00:00')
    parser.add_argument('--config', help='config file')
    return parser


if "__main__" == __name__:
    main(sys.argv)
