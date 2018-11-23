"""
Collect repositories of the chapters into a subtree

Generate Report
"""

import ast
import configparser
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
    config = configparser.ConfigParser()
    config.read(argv[0])

    umbrella_folder = config['operation']['umbrella']
    # make the umbrella_folder if missing
    if not os.path.exists(umbrella_folder):
        os.makedirs(umbrella_folder)
        config['operation']['update_repo'] = 'False'

    if (os.path.exists('participant_folder_list.txt') and ('True' != config['operation']['update_repo'])):
        print('reading list file')

        participant_folder_list = []

        with open('participant_folder_list.txt', 'r') as pl_file:
            for path in pl_file.readlines():
                participant_folder_list.append(
                    {
                        'name': os.path.split(path)[-1],
                        'path': path.strip(),
                    }
                )

    else:
        print('updating subtrees')
        participant_folder_list = init_or_update_umbrella_repos(
            transpose_dict(
                get_sections_dict(config)
                ), 
            umbrella_folder
        )

        write_folder_list_file(participant_folder_list)

    generate_reports(participant_folder_list, config)


def write_folder_list_file(participant_folder_list):
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
    + section_a
    ++ urls
    +++ url_a_00
    +++ url_a_01
    +++ url_a_02
    ++ user_ids
    +++ user_id_00
    +++ user_id_01
    +++ user_id_02

    + section_b
    ++ urls
    +++ url_b_00
    +++ url_b_01
    +++ url_b_02
    ++ user_ids
    +++ user_id_00
    +++ user_id_01
    +++ user_id_02

    """
    sections_dict = {}

    urls_path_list = []

    url_parse_dict = {}

    """
    sections_dict
    + section_a
    ++ urls
    +++ url_a_00
    +++ url_a_01
    +++ url_a_02

    + section_b
    ++ urls
    +++ url_b_00
    +++ url_b_01
    +++ url_b_02
    """

    for section in ast.literal_eval(config['operation']['sections']):
        sections_dict[section] = {
            'urls':ret.get_github_url_list(config[section]['list'].strip()),
        }

        url_parse_dict[section] = []

        for url in sections_dict[section]['urls']:
            url_parse_dict[section].append(up.urlparse(url))
            urls_path_list.append(url_parse_dict[section][-1].path)

    # os.path.split(parse.path)[-1][id_starts_here:] -> user_id
    id_starts_here = len(config['operation']['repo_prefix_sample'].strip())

    """
    sections_dict
    + section_a
    ++ urls
    +++ url_a_00
    +++ url_a_01
    +++ url_a_02
    ++ user_ids
    +++ user_id_00
    +++ user_id_01
    +++ user_id_02

    + section_b
    ++ urls
    +++ url_b_00
    +++ url_b_01
    +++ url_b_02
    ++ user_ids
    +++ user_id_00
    +++ user_id_01
    +++ user_id_02
    """

    # set user ids of each repository
    for section in sections_dict:
        sections_dict[section]['user_ids'] = []
        for parse in url_parse_dict[section]:
            sections_dict[section]['user_ids'].append(os.path.splitext(os.path.split(parse.path.strip('/'))[-1])[0][id_starts_here:])

    return sections_dict


@timeit.timeit
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
def init_or_update_umbrella_repos(users_dict, umbrella_folder):
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

    repo_list = []

    # because it seems not desirable to update multiple subtrees at once
    # if parallelize, in the user == participant level
    for user, section_url_dict in users_dict.items():
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
                print(f'remote add {section}')
                git.git(('remote', 'add', section, section_url_dict[section]))
                print('git remote -v')
                git.git(('remote', '-v'))

            if not os.path.exists(os.path.join(user_folder, section)):
                print(f"folder missing : {os.path.join(user_folder, section)}")
                print('subtree add')
                git.git(('subtree', 'add', f'--prefix={section}', section, 'master'))
            else:
                print('subtree pull')
                git.git(('subtree', 'pull', f'--prefix={section}', section, 'master'))

        os.chdir(start_folder)
        repo_list.append({'name': user, 'path': user_folder})

    os.chdir(start_folder)

    return repo_list


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


if "__main__" == __name__:
    main(sys.argv[1:])
