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


def main(argv):
    config = configparser.ConfigParser()
    config.read(argv[0])

    umbrella_folder = config['operation']['umbrella']
    # make the umbrella_folder if missing
    if not os.path.exists(umbrella_folder):
        os.makedirs(umbrella_folder)

    if (os.path.exists('participant_folder_list.txt') and ('True' != config['operation']['update_repo'])):
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
        participant_folder_list = init_or_update_umbrella_repos(
            transpose_dict(
                get_sections_dict(config)
                ), 
            umbrella_folder
        )

    generate_reports(participant_folder_list, config)


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
            if not url.endswith('.git'):
                # add admin id to url
                # remove '/' if at the end
                # add .git
                url = git.set_id_to_url(url, ret.config['Admin']['id']).strip('/') + '.git'
            user_dict[section] = url
            ids_dict[user_id] = user_dict

    return ids_dict


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
    for user in users_dict:
        user_folder = os.path.abspath(os.path.join(umbrella_folder, user))
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        os.chdir(user_folder)
        if not os.path.exists('.git'):
            # initialize user umbrella repo

            init_user_umbrella_repo(users_dict[user])
            # end initializing user umbrella repo

        # section loop
        for section in users_dict[user]:
            if section not in get_remote_list():
                print(f'remote add {section}')
                git.git(('remote', 'add', section, users_dict[user][section]))
                print('git remote -v')
                git.git(('remote', '-v'))

            if not os.path.exists(os.path.join(user_folder, section)):
                print(f"folder missing : {os.path.join(user_folder, section)}")
                print('subtree add')
                git.git(('subtree', 'add', f'--prefix={section}', section, 'master'))
            else:
                print('subtree pull')
                git.git(('subtree', 'pull', f'--prefix={section}', section, 'master'))

        repo_list.append({'name': user, 'path': user_folder})
        os.chdir(start_folder)

    os.chdir(start_folder)

    return repo_list


def get_remote_list():
    return [remote_line.strip() for remote_line in git.git(('remote',), bVerbose=False).splitlines()]


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


def generate_reports(repo_list, config, results = {}):
    progress.call_commit_count(config, 'umbrella', repo_list, results)


if "__main__" == __name__:
    main(sys.argv[1:])
