"""
Consolidate tags

If one commit of repository contains too many tags, consolidate.
Compare with remote tags using `git ls-remote --tags origin` and keep if in the remote.

ref : https://stackoverflow.com/questions/1841341/remove-local-git-tags-that-are-no-longer-on-the-remote-repository
"""

import configparser
import os
import time

import git


def main():

    config = configparser.ConfigParser()
    filename = 'detect_conflict.cfg'

    if os.path.exists(filename):
        # if file exists
        config.read(filename)
    else:
        raise IOError('unable to find {filename}'.format(filename=filename))

    for section_name in config['folders']:
        process_section(section_name, config)


def process_section(section_name, config):
    print('section_name = ', section_name)
    section_path = config['folders'][section_name]

    for repo_name in os.listdir(os.path.abspath(section_path)):
        process_repo(section_path, repo_name)


def process_repo(section_path, repo_name):
    repo_path = os.path.join(section_path, repo_name)

    if os.path.isdir(repo_path):
        print('\trepo_path = ', repo_path)
        cwd_backup = os.getcwd()
        os.chdir(repo_path)

        process_tags()

        os.chdir(cwd_backup)


def process_tags():
    print('\t\tproces_tags(): cwd =', os.getcwd())
    result = git.get_refs_tag_deref()
    print('\t\tproces_tags(): len(result) =', len(result))

    git.clean_xdf()

    tags_dict = {}
    # sha : [tag1, tag2, ...]

    # tag loop
    tag_sha_list = git.get_refs_tag_deref()
    for tag__sha in tag_sha_list:
        tag, sha = tag__sha
        tags_dict[sha] = tags_dict.get(sha, [])
        date_time_str, small_sha = tag.split('__')

        assert sha.startswith(small_sha)

        # Tue_Apr_24_16_54_15_2018
        datetime_struct = time.strptime(date_time_str, '%a_%b_%d_%H_%M_%S_%Y')

        tags_dict[sha].append((datetime_struct, tag))

    # sha loop
    s = 0  # to see if processed all tags
    for k, sha in enumerate(tags_dict):
        n = len(tags_dict[sha])
        print('\t\tproces_tags(): {k:3d} {sha} {n}'.format(sha=sha, k=k, n=n))
        tags_dict[sha].sort()

        for time__tag in tags_dict[sha][1:]:
            _, tag = time__tag
            if not git.delete_tag(tag):
                print('Unable to delete tag {tag}?'.format(tag=tag))

        s += n
    assert len(tag_sha_list) == s


if "__main__" == __name__:
    main()
