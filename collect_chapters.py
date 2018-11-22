"""
Collect repositories of the chapters into a submodule
"""

import ast
import configparser
import os
import pprint
import sys
import urllib.parse as up

import regex_test as ret


def main(argv):
    config = configparser.ConfigParser()
    config.read(argv[0])

    umbrella_folder = config['operation']['umbrella']
    # make the umbrella_folder if missing
    if not os.path.exists(umbrella_folder):
        os.makedirs(umbrella_folder)


def get_sections_dict(config):
    """
    Using the config info, build dict containing list of repositories of all sections
    """
    sections_dict = {}

    for section in ast.literal_eval(config['operation']['sections']):
        sections_dict[section] = ret.get_github_url_list(config[section]['list'].strip())

    return sections_dict


def transpose_dict(sections_dict):
    """
    Input
    =====
    section0: [repo0_00, repo0_01, ...],
    section1: [repo1_00, repo1_01, ...],

    Output
    =====
    id00: {section0: repo0_00, section1: repo1_00, ...},
    id01: {section0: repo0_01, section1: repo1_01, ...},
    """

    ids_dict = {}

    for section in sections_dict:
        for url in sections_dict[section]:
            parse = up.urlparse(url)
            # user_id is the last part of the url path except extension if there is
            user_id = os.path.splitext(os.path.split(parse.path)[-1])[0].split('-')[-1]
            # add url to the table
            user_dict = ids_dict.get(user_id, {})
            user_dict[section] = url
            ids_dict[user_id] = user_dict

    return ids_dict


if "__main__" == __name__:
    main(sys.argv[1:])
