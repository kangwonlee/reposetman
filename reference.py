"""
Reference builder

Objective : Build a set of comments that are already in the reference repositories

Input : configuration file
 
"""

import configparser
import os

import git
import ignore
import read_python
import regex_test as ret
import timeit
import unique_list


@timeit.timeit
def main(argv=False):
    rb = ReferenceBuilder(argv)
    rb.run()


class ReferenceBuilder(object):
    def __init__(self, config_filename=False):
        # prepare configuration
        self.config = configparser.ConfigParser()

        if config_filename:
            config_filename = config_filename
        else:
            config_filename = 'reference.cfg'

        if os.path.exists(config_filename):
            self.config.read(config_filename)
        else:
            raise IOError("Can't find config file %s" % config_filename)

        # folder
        self.folder = os.path.abspath(self.config['operation']['folder'])
        print(self.folder)

        # comments
        self.comments = unique_list.unique_list()

        # initialize from the file
        if os.path.exists(self.config['operation']['comment_output_file']):
            with open(self.config['operation']['comment_output_file'], 'rt', encoding='utf-8') as f_in:
                start_list = f_in.readlines()

            for item in start_list:
                self.comments.add(item.strip())

    def __del__(self):
        del self.config

    def run(self, b_verbose=False):
        # prepare folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # clone or update repositories
        for k, url in enumerate(self.config['urls']):
            self.process_section(k, url)

        if b_verbose:
            print(self.comments)

        with open(self.config['operation']['comment_output_file'], 'wt', encoding='utf-8') as f_out:
            for line in self.comments:
                f_out.write(line + '\n')

    def get_commit(self, section):
        return self.config['commits'][section]

    def process_section(self, k, section):
        # github url to browse commit of a repository
        print('{sec} {url}/tree/{commit}'.format(
            sec=section, url=self.config['urls'][section], commit=self.get_commit(
                section),
        ))

        # clone or update the repository
        repo = ret.clone_or_pull_repo_cd(k,
                                         self.config['urls'][section],
                                         self.folder,
                                         b_update_repo='True' == self.config['operation']['folder'],
                                         b_tag_after_update=False,
                                         )

        # abs path to the repository
        repo_path = os.path.join(self.folder, repo['name'])

        git.checkout(self.get_commit(section), repo_path=repo_path)

        self.comments = collect_comments_recursively(repo_path, self.comments)

        return self.comments


def collect_comments_recursively(path, comments=unique_list.unique_list(), b_verbose=False):

    for root_path, _, file_names in os.walk(path):
        if not ignore.is_ignore_path(root_path):
            for file_name in file_names:
                if ignore.is_python(file_name):
                    full_path = os.path.join(root_path, file_name)
                    for line in read_python.get_comments_list_from_filename(full_path):
                        comments.add(line)

                    if b_verbose:
                        print('len(comments) =', len(comments))
                else:
                    if b_verbose:
                        print('ignore file %s' % file_name)
        else:
            if b_verbose:
                print('ignore path %s' % root_path)

    return comments


if '__main__' == __name__:
    main()
