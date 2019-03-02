"""
Collect repositories of the chapters into a subtree

Generate Report

Author : KangWon LEE

Year : 2018

"""

"""

Each chapter would need one url list file and a section in the .cfg file
In addition, "umbrella" section with folder and execution info would be necessary
Each this script would clone all chapters of each user under the "umbrella" folder
Would ignore the folders of each chapter section of cfg file
The script would also generate a file with list of folders for each participant
If that file is available, it would use it.

"""


import ast
import configparser
import itertools
import multiprocessing as mp
import os
import pprint
import sys
import urllib.parse as up

import git
import progress
import regex_test as ret
import timeit


@timeit.timeit
def main(argv):
    # read configuration file
    config = configparser.ConfigParser()
    config.read(argv[0])

    # get umbrella folder location
    # TODO : consider rename umbrella to summary
    umbrella_folder = config['operation']['umbrella']

    # make the umbrella_folder if missing
    if not os.path.exists(umbrella_folder):
        os.makedirs(umbrella_folder)
        # if the umbrella_folder was missing, alway try to update
        config['operation']['update_repo'] = 'False'

    # to save time, if list file is available and 
    # config says so, read from the folder list file
    # TODO : consider moving folder list filename to cfg file
    if (os.path.exists('participant_folder_list.txt') and ('True' != config['operation']['update_repo'])):

        # TODO : consider refactoring into a function
        print('reading list file')

        # for report generators
        participant_folder_list = []
        """
        [
            {'name': user_id_00, 'path': path_to_summary_folder/user_id_00},
            {'name': user_id_01, 'path': path_to_summary_folder/user_id_01},
            {'name': user_id_02, 'path': path_to_summary_folder/user_id_02},
            ...
        ]
        """

        # TODO : consider moving folder list filename to cfg file
        with open('participant_folder_list.txt', 'r') as pl_file:
            # TODO : consider read text and then convert for more testable code?
            # TODO : is list comprehension beneficial?
            for path in pl_file.readlines():
                participant_folder_list.append(
                    {
                        'name': os.path.split(path)[-1],
                        'path': path.strip(),
                    }
                )
        # end of reading folder list file
    else:
        print('updating subtrees')
        participant_folder_list = init_or_update_umbrella_repos(
            transpose_dict(
                get_sections_dict(config)
                ), 
            umbrella_folder
        )

        # TODO : is it required to overwrite everytime?
        write_folder_list_file(participant_folder_list)

    # reports about users with chapters
    generate_reports(participant_folder_list, config)


def write_folder_list_file(participant_folder_list):
    # TODO : consider moving folder list filename to cfg file
    # storing paths only
    # last part of path == id
    with open('participant_folder_list.txt', 'w') as folder_list_file:
        for folder_info in participant_folder_list:
            folder_list_file.write(folder_info['path']+'\n')


@timeit.timeit
def get_sections_dict(config):
    """
    Using the config info, build dict containing list of repositories of all sections

    Output
    ======

    sections_dict
    {
        'section_a':{
            'urls':[
                url_a_00, url_a_01, url_a_02, ...
            ],
            'user_ids':[
                user_id_00, user_id_01, user_id_02, ...
            ]
        }
        'section_b':{
            'urls':[
                url_b_00, url_b_01, url_b_02, ...
            ],
            'user_ids':[
                user_id_00, user_id_01, user_id_02, ...
            ]
        }
    }

    sections may have different participant (== user) sets

    """

    # result
    sections_dict = {}

    urls_path_list = []

    # to extract user ids
    url_parse_dict = {}

    # section loop
    for section in ast.literal_eval(config['operation']['sections']):
        sections_dict[section] = {
            'urls':ret.get_github_url_list(config[section]['list'].strip()),
        }

        url_parse_dict[section] = []

        # to extract user ids from the urls later
        for url in sections_dict[section]['urls']:
            url_parse_dict[section].append(up.urlparse(url))
            urls_path_list.append(url_parse_dict[section][-1].path)

    # os.path.split(parse.path)[-1][id_starts_here:] -> user_id
    id_starts_here = len(config['operation']['repo_prefix_sample'].strip())

    # set user ids of each repository
    for section in sections_dict:
        sections_dict[section]['user_ids'] = []

        # parsed url loop
        for parse in url_parse_dict[section]:
            sections_dict[section]['user_ids'].append(
                os.path.splitext(
                    os.path.split(
                        parse.path.strip('/')
                        )[-1]  # last part of the path
                    )[0][id_starts_here:]   # extract id
                )

    # TODO : is it desirable to separate id extraction?

    return sections_dict


@timeit.timeit
def transpose_dict(sections_dict):
    """
    Input
    =====
    section0: 
        'urls': [repo0_00, repo0_01, ...],
        'ids' : [id00, id01, ...]
    section1: 
        'urls': [repo1_00, repo1_01, ...],
        'ids' : [id00, id01, ...]

    Output
    =====
    id00: {section0: repo0_00, section1: repo1_00, ...},
    id01: {section0: repo0_01, section1: repo1_01, ...},
    """

    ids_dict = {}

    for section in sections_dict:
        for url, user_id in zip(sections_dict[section]['urls'], sections_dict[section]['user_ids']):
            # add url to the table
            user_dict = ids_dict.get(user_id, {})
            if not url.endswith('.git'):
                # add admin id to url
                # remove '/' if at the end
                # add .git
                url = git.set_id_to_url(url, ret.config['Admin']['id']).strip('/') + '.git'
            user_dict[section] = url
            ids_dict[user_id] = user_dict

    return ids_dict


@timeit.timeit
def init_or_update_umbrella_repos(users_dict, umbrella_folder, b_parallel=True):
    """
    Input
    =====
    user_id00: {section0: repo0_00, section1: repo1_00, ...},
    user_id01: {section0: repo0_01, section1: repo1_01, ...},

    umbrella repository
    + user_id00
    ++ subtree section0 : repo0_00
    ++ subtree section1 : repo1_00
    ++ ...

    + user_id01
    ++ subtree section0 : repo0_01
    ++ subtree section1 : repo1_01
    ++ ...
    """

    start_folder = os.getcwd()

    def gen_folder_user_dict(user_dict_item):
        for user, user_dict in user_dict_item:
            yield umbrella_folder, user, user_dict

    if b_parallel:

        p = mp.Pool(mp.cpu_count())

        # iterate over users_dict.items() repeating umbrella_folder
        repo_list = p.starmap(
            init_or_update_user_umbrella, 
            gen_folder_user_dict(users_dict.items()),
        )

        p.close()
        p.join()

    else:

        # iterate over users_dict.items() repeating umbrella_folder
        repo_list = itertools.starmap(
            init_or_update_user_umbrella, 
            gen_folder_user_dict(users_dict.items()),
        )

    os.chdir(start_folder)

    return repo_list


def init_or_update_user_umbrella(umbrella_folder, user, section_url_dict):

    assert os.path.exists(umbrella_folder), f'init_or_update_user_umbrella: missing folder {umbrella_folder}'
    assert isinstance(user, str), f'init_or_update_user_umbrella: type({user}) = {type(user)}'
    assert isinstance(section_url_dict, dict), f'init_or_update_user_umbrella: type({section_url_dict}) = {type(section_url_dict)}'

    user_folder = os.path.abspath(os.path.join(umbrella_folder, user))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    start_folder = os.getcwd()
    os.chdir(user_folder)
    if not os.path.exists('.git'):
        # initialize user umbrella repo

        init_user_umbrella_repo(section_url_dict)
        # end initializing user umbrella repo

    # section loop
    for section in section_url_dict:
        if section not in get_remote_list():
            print(f'remote add {section} {section_url_dict[section]}')
            git.git(('remote', 'add', section, section_url_dict[section]))
            print('git remote -v')
            git.git(('remote', '-v'))

        if not os.path.exists(os.path.join(user_folder, section)):
            print(f"folder missing : {os.path.join(user_folder, section)}")
            print('subtree add')
            git.git(('subtree', 'add', f'--prefix={section}', section, 'master'))
        else:
            print(f'subtree pull {section_url_dict[section]}')
            git.git(('subtree', 'pull', f'--prefix={section}', section, 'master'))

    os.chdir(start_folder)    
    return {'name': user, 'path': user_folder}


def get_remote_list():
    return [remote_line.strip() for remote_line in git.git(('remote',), bVerbose=False).splitlines()]


@timeit.timeit
def init_user_umbrella_repo(user_dict):
    # initialize user umbrella repo

    print('git init')
    git.git(('init',))

    # repository info as the first commit
    with open('repo_list.txt', 'w') as repo_list_file:
        repo_list_file.write(pprint.pformat(user_dict))

    git.git(('add', 'repo_list.txt'))
    git.git(('commit', '-m', 'initial commit'))
    # end initializing user umbrella repo


@timeit.timeit
def generate_reports(repo_list, config, results = {}):
    progress.call_commit_count(config, 'umbrella', repo_list, results)
    progress.call_pound_count(config, 'umbrella', repo_list, results)
    progress.call_run_all(config, 'umbrella', repo_list, results)


if "__main__" == __name__:
    main(sys.argv[1:])
