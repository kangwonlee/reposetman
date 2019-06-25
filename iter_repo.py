import ast
import os
import re

import repo_path

def get_section_list(config):
    # https://stackoverflow.com/questions/335695/lists-in-configparser
    return ast.literal_eval(config['operation']['sections'])


def gen_section(config):
    """
    Iterate over sections of the config file:

    """

    for section in get_section_list(config):
        yield section


def read_b_decode(filename):
    """
    Read a file in binary mode and try to decode

    Try utf-8 and cp949 for now

    """
    with open(filename, 'rb') as f:
        data = f.read()

    try:
        txt = data.decode('utf-8')
    except UnicodeDecodeError:
        txt = data.decode('cp949')
    
    return txt


def compile_re_github_urls():
    return re.compile(r"(https://[\w+?@]*github.com/\S+?/\S+?)[\"\s]")


def get_github_urls(txt):
    return compile_re_github_urls().findall(txt)


def iter_github_urls(txt):
    for p in compile_re_github_urls().finditer(txt):
        yield p[0].strip()


def iter_github_urls_in_file(filename):
    for url in iter_github_urls(read_b_decode(filename)):
        yield url


def iter_repo_path_with_due(config, b_assert=True):
    """
    Iterate over full paths to each local repository

    """

    for section in gen_section(config):
        due_date = config[section]['before']

        for full_path_to_repo in iter_repo_path_in_section(config, section, b_assert=b_assert):
            yield full_path_to_repo, due_date


def iter_repo_path(config, b_assert=True):
    """
    Iterate over full paths to each local repository in all sections

    """

    for section in gen_section(config):

        for full_path_to_repo in iter_repo_path_in_section(config, section, b_assert=b_assert):
            yield full_path_to_repo


def iter_repo_path_in_section(config, section, b_assert=True):
    repo_path_rel = config[section]['folder']

    for url in iter_github_urls_in_file(config[section]['list']):
        proj_id = repo_path.get_repo_name_from_url(url)

        full_path_to_repo = os.path.abspath(
            os.path.join(repo_path_rel, proj_id)
        )

        if b_assert:
            assert os.path.exists(full_path_to_repo), full_path_to_repo

        yield full_path_to_repo
