"""
Collect repositories of the chapters into a submodule
"""

import ast
import configparser
import pprint
import sys
import urllib.parse as up

import regex_test as ret


def main(argv):
    config = configparser.ConfigParser()
    config.read(argv[0])

    pprint.pprint(get_sections_dict(config))


def get_sections_dict(config):
    """
    Using the config info, build dict containing list of repositories of all sections
    """
    sections_dict = {}

    for section in ast.literal_eval(config['operation']['sections']):
        sections_dict[section] = ret.get_github_url_list(config[section]['list'].strip())

    return sections_dict


if "__main__" == __name__:
    main(sys.argv[1:])
