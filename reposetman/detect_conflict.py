import configparser
import itertools
import multiprocessing
import os
import pprint

import git
import ignore
import read_python
import regex_test as ret
import timeit
import unique_list


@timeit.timeit
def main(argv=False):
    cd = ConflictDetector(argv)
    cd.run()


class ConflictDetector(object):
    def __init__(self, config_filename=False):
        # prepare configuration
        self.config = configparser.ConfigParser()

        if config_filename:
            config_filename = config_filename
        else:
            config_filename = 'detect_conflict.cfg'
        
        if os.path.exists(config_filename):
            self.config.read(config_filename)
        else:
            raise IOError("Can't find config file %s" % config_filename)

        # to store conflict info
        self.conflict_list = unique_list.unique_list()

    def __del__(self):
        del self.config

    def run(self, b_verbose=False):
        # section loop
        def gen_section():
            for section_name in self.config['folders']:
                yield section_name, b_verbose
        return tuple(itertools.starmap(self.process_section, gen_section()))

    def process_section(self, section_name, b_verbose=False):

        # this sections' repositories are under this folder
        section_folder = os.path.abspath(self.config['folders'][section_name])

        # get conflict list of the section
        self.conflict_list = collect_conflicts(section_folder)

        # filter blank
        write_this = [conflict for conflict in self.conflict_list if conflict]

        # no point of writing if no conflict
        if write_this:
            with open(section_name + '_' +self.config['operation']['conflict_output_file'], 'wt', encoding='utf-8') as f_out:
                for conflict in write_this:
                    f_out.write(pprint.pformat(conflict) + '\n')

        # return value
        result = self.conflict_list

        # reset conflict storage
        self.conflict_list = unique_list.unique_list()

        return result


@timeit.timeit
def collect_conflicts(section_folder, b_verbose=False):

    def gen_repo_path(repo_name_list):
        for repo_name in repo_name_list:
            yield os.path.join(section_folder, repo_name)

    p = multiprocessing.Pool()

    result = p.imap_unordered(process_repository, gen_repo_path(os.listdir(section_folder)))

    p.close()
    p.join()

    return result


def process_repository(repository_full_path):
    repo_result = {}

    if os.path.isdir(repository_full_path) and not ignore.is_ignore_path(repository_full_path):

        _, repository = os.path.split(repository_full_path)

        # process repository
        cwd_backup = os.getcwd()
        os.chdir(repository_full_path)

        msgo, msge = git.reset_hard_head()
        if 'CONFLICT' in msgo or msge:
            repo_result['reset'] = get_error_info('git reset --hard HEAD', msgo, msge, repository)

        msgo, msge = git.checkout('master')
        if 'CONFLICT' in msgo or "Already on 'master'" != msge.strip():
            repo_result['checkout'] = get_error_info('git checkout master', msgo, msge, repository)

        msgo, msge = git.pull()
        if 'CONFLICT' in msgo or ('error' in msge) or ('fatal' in msge):
            repo_result['pull'] = get_error_info('git pull', msgo, msge, repository)

        msgo, msge = git.status()
        if 'CONFLICT' in msgo or msge:
            repo_result['status'] = get_error_info('git status', msgo, msge, repository)

        os.chdir(cwd_backup)
    return repo_result


def get_error_info(cmd_msg, msgo, msge, item):
    print('collect_comments_recursively() :', os.getcwd())
    print('collect_comments_recursively() : {cmd_msg}'.format(cmd_msg=cmd_msg))
    print('msgo :', msgo)
    print('msge :', msge)
    return {'folder':os.getcwd(), 'repository':item, 'stdout': msgo, 'stderr': msge}


if '__main__' == __name__:
    main()
