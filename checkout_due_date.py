"""
Checkout repositories to a date

Usage : 
$ python checkout_due_date.py --config [.cfg file] --force --date yyyy-mm-dd --time hh:mm:ss

"""
import argparse
import ast
import configparser
import os
import sys

import git
import regex_test
import repo_path


def main(argv):

    config = get_config_from_argv(argv)

    for full_path_to_repo, due_date in gen_repo_path(config):
        print(f"{os.path.split(full_path_to_repo)[-1]} ".ljust(60, '='))
        git.checkout_date(due_date, full_path_to_repo, b_force=True, b_verbose=True)


def get_config_from_argv(argv):
    parser = get_arg_parser()

    if argv[1:]:
        namespace = parser.parse_args(argv[1:])
    else:
        # show help and exit
        parser.parse_args(['--help'])
        sys.exit(0)

    # init config
    if namespace.config:

        assert os.path.exists(namespace.config)

        config = configparser.ConfigParser()
        config.read(namespace.config)

    # --date --time override
    if namespace.date and namespace.time:
        date_time = namespace.date + ' ' + namespace.time

        for section in gen_section(config):
            config[section]['before'] = date_time

    # --date override
    elif namespace.date and (not namespace.time):
        date_time = namespace.date + ' ' + '23:59:59'

        for section in gen_section(config):
            config[section]['before'] = date_time

    return config


def gen_section(config):
    """
    Iterate over sections of the config file:

    [operation]
    ...
    sections=['a', 'b', 'c']
    ...

    """
    sections_list = ast.literal_eval(config['operation']['sections'])

    for section in sections_list:
        yield section


def gen_repo_path(config, b_assert=True):

    for section in gen_section(config):
        due_date = config[section]['before']
        repo_path_rel = config[section]['folder']
        list_filename = config[section]['list']
        github_url_list = regex_test.get_github_url_list(list_filename)

        for url in github_url_list:
            proj_id = repo_path.get_repo_name_from_url(url)

            full_path_to_repo = os.path.abspath(
                os.path.join(repo_path_rel, proj_id)
            )

            if b_assert:
                assert os.path.exists(full_path_to_repo), full_path_to_repo

            yield full_path_to_repo, due_date


def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='checkout date in yyyy-mm-dd')
    parser.add_argument('--time', help='checkout time in hh:mm:ss', default='00:00:00')
    parser.add_argument('--force', help='force checkout', action='store_true')
    parser.add_argument('--config', help='config file', required=True)
    return parser


if "__main__" == __name__:
    main(sys.argv)
