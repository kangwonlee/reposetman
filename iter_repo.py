import ast
import os
import re


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
    with open(filename, 'rb') as f:
        data = f.read()

    try:
        txt = data.decode('utf-8')
    except UnicodeDecodeError:
        txt = data.decode('cp949')
    
    return txt


def get_github_urls(txt):
    return re.findall(r"(https://[\w+?@]*github.com/\S+?/\S+?)[\"\s]", txt)


def iter_github_urls(txt):
    for p in re.finditer(r"(https://[\w+?@]*github.com/\S+?/\S+?)[\"\s]", txt):
        yield p[0].strip()


def iter_github_urls_in_file(filename):
    for url in iter_github_urls(read_b_decode(filename)):
        yield url
