import configparser
import itertools
import multiprocessing as mp
import os
import re
import time

import git
import repo_path
import timeit
import unique_list


cfg_filename = 'regex_test.cfg'


def init_regex_test_cfg():
    list_filename = 'test_list.txt'
    repo_path = 'sample'
    if not os.path.exists(cfg_filename):
        config = configparser.ConfigParser()
        config['repository'] = {
            'listFile': list_filename,
            'path': repo_path,
        }
        config['Admin'] = {
            'id': 'please configure github id'
        }

        with open(cfg_filename, 'w') as cfg_file:
            config.write(cfg_file)
        raise FileNotFoundError(
            f'Please configure github id in {cfg_filename} and restart')


config = configparser.ConfigParser()

if not os.path.exists(cfg_filename):
    init_regex_test_cfg()

config.read(cfg_filename)


def get_proj_id_list(filename=config['repository']['listFile']):
    """

    :param str filename:
    :return:
    """
    txt = read_txt(filename)
    # using regular expression, find all repository names
    found = get_proj_id(txt)

    # delete text object after use
    del txt

    return found


@timeit.timeit
def get_github_url_list(filename):
    txt = read_utf_or_cp(filename)
    # using regular expression, find all repository addresses
    return get_github_urls(txt)


def get_github_urls(txt):
    return re.findall(r"(https://github.com/.+?/.+?)[\"\s]", txt)


def get_proj_id(txt):
    return re.findall("https://.*?@github.com/.+[/,](.+).git", txt)


def get_proj_info_line(txt):
    """
    expected input txt : '2082652342 가나다  https://abc@github.com/CPF18A/18pfa_lpthw-abc.git'
    """
    possible_separators = r"[,\s]" + "+?"

    # pattern to find most of the fields
    pattern = r"^(?P<id_number>\w+?){sep}(?P<name>\w+?){sep}https://(?P<domain>.+)/(?P<group>.+)/(?P<repo_name>.+).git\s*?$".format(
        sep=possible_separators)

    r = re.compile(pattern, re.M)

    # pattern to identify github id
    r_id = re.compile(r'(?P<github_id>\w+?)@(?P<domain>.+)')

    # https://stackoverflow.com/questions/11103856/re-findall-which-returns-a-dict-of-named-capturing-groups
    proj_info_list = []

    # search loop
    for m in r.finditer(txt):
        # dictionary from match group
        new_dict = m.groupdict()
        # add new entry to the list
        proj_info_list.append(new_dict)

        # if github id in the domain
        if '@' in new_dict['domain']:
            # try to find id and domain
            found_list = r_id.match(new_dict['domain']).groupdict()
            # debug message
            # print('found_list =', found_list)

            # update the entry
            new_dict.update(found_list)

    return proj_info_list


def get_proj_info(txt_fname):
    '''
    get list of project info including project id

    string of interest :
    2082652342 가나다  https://abc@github.com/CPF18A/18pfa_lpthw-abc.git

    '''
    txt = read_txt(txt_fname)
    # regular expression

    proj_info_list = get_proj_info_line(txt)

    '''
    expected_dict = {
                         project_id : (section ,student_id,student_name, domain_id, domain,),
                         project_id : (section ,student_id,student_name, domain_id, domain,),
                        }    
    '''

    proj_info_dict = {}

    for one_dict in proj_info_list:
        proj_info_dict[one_dict['repo_name']] = one_dict

    # delete objects after use
    del proj_info_list[:]
    del txt, proj_info_list

    return proj_info_dict


@timeit.timeit
def clone_or_pull_repo_list(
    repo_url_list,
    section_folder=os.path.abspath(config['repository']['path']),
    b_update_repo=True,
    b_multiprocessing=True
):
    """
    process repository list
    if duplicate, don't do anything
    if path does not exist, clone
    if path exists, pull

    """
    # TODO : avoid confusion between .cfg files

    abs_section_folder = os.path.abspath(section_folder)

    # if missing, make a new folder for the new section
    if not os.path.exists(abs_section_folder):
        os.makedirs(abs_section_folder)

    def gen_update_arg(repo_url_list):
        """
        generates argument for mapping clone_or_pull_repo_split()
        """
        for k, repo_url in enumerate(repo_url_list):
            yield (k, repo_url, abs_section_folder, b_update_repo)

    if b_multiprocessing:
        p = mp.Pool()

        repo_list = tuple(p.starmap(clone_or_pull_repo_cd,
                                    gen_update_arg(repo_url_list)))

        # multiprocessing cleanup
        p.close()
        p.join()
    else:
        repo_list = tuple(itertools.starmap(
            clone_or_pull_repo_cd, gen_update_arg(repo_url_list)))

    return repo_list


def clone_or_pull_repo_cd(k, repo_url, abs_section_folder, b_update_repo, b_tag_after_update=True):
    # cloning should create local repository under this folder
    org_path = repo_path.cd(abs_section_folder)

    result = clone_or_pull_repo(
        k, repo_url, b_update_repo, b_tag_after_update=b_tag_after_update)

    os.chdir(org_path)

    return result


def clone_or_pull_repo(k, repo_url, b_updte_repo, b_tag_after_update=True):
    # initialize repository info
    repo = {
        'url': repo_url,
        'name': repo_path.get_repo_name_from_url(repo_url),  # repository name
    }

    # get project path
    repo_path_in_section = repo_path.get_local_repo_path(repo['name'])

    repo['path'] = os.path.abspath(repo_path_in_section)

    # just in case
    dir_backup = os.getcwd()

    # even if b_updte_repo is False,
    # if not cloned yet, do it now.
    if not os.path.exists(repo_path_in_section):
        print('clone_or_pull_repo(%2d) : clone %s' % (k, repo['url']))
        git.clone(repo['url'], id=config['Admin']['id'])
    else:
        if b_updte_repo:
            print('clone_or_pull_repo(%2d) : pull %s' % (k, repo['url']))
            fetch_and_reset(repo_path_in_section)

    # tag with time stamp after clone or pull
    tag_all_remote_branches(
        b_tag_after_update, os.path.abspath(repo_path_in_section), repo)

    # just in case
    os.chdir(dir_backup)

    return repo


def get_timestamp_str():
    return time.strftime('%a_%b_%d_%H_%M_%S_%Y')


def tag_stamp(b_tag_after_update, repo_path_in_section, repo, branch='', commit=''):
    """
    Tag with time stamp after clone or pull
    """
    if b_tag_after_update:
        # store current path
        cwd = os.getcwd()

        # move to the repository path
        os.chdir(repo_path_in_section)

        # get latest hash value
        last_sha = git.get_last_sha(branch=branch)

        # decide tag string
        if branch:
            # add branch name
            tag_string = '{time_stamp}__{branch}__{sha}'.format(
                time_stamp=time.asctime().replace(' ', '_').replace(':', '_'),
                sha=last_sha,
                branch=branch,
            )
        else:
            # just time stamp
            tag_string = '{time_stamp}__{sha}'.format(
                time_stamp=time.asctime().replace(' ', '_').replace(':', '_'),
                sha=last_sha,
            )

        # Tag if the latest commit does not already have a tag
        if not git.has_a_tag(commit=commit):
            if not git.tag(tag_string, revision=commit):
                raise IOError('Unable to tag {name} {tag}'.format(
                    tag=tag_string, name=repo['name']))

        # return to the stored path
        os.chdir(cwd)


def tag_all_remote_branches(b_tag_after_update, repo_abs_path, repo):
    """
    Tag all remote branches with timestamps and branch names
    """
    # preserve current status
    # current_section_branch = git.get_current_branch()
    # probably section path
    section_path = os.getcwd()

    if b_tag_after_update:
        # need to obtain the branch list in the repository
        os.chdir(repo_abs_path)

        # preserve repository status
        current_repo_branch = git.get_current_branch()

        # branch name loop
        for repo_branch in git.get_remote_branch_list():
            # A remote branch would be like : remote_name/branch_name/##
            tag_stamp(b_tag_after_update, repo_abs_path, repo, branch=repo_branch, commit=repo_branch)

        # restore repository branch
        git.checkout(current_repo_branch)
        if 'master' != git.get_current_branch().strip():
            print("branch = {branch}, repo path = {path}".format(
                branch=git.get_current_branch(), path=repo_abs_path))

    # return to section path
    os.chdir(section_path)
    # git.checkout(current_section_branch)


def get_git_naver_anon(proj_id):
    '''
    argument : proj_id : project id
    return : git repository address using the project id

    >>> get_git_naver_anon("aaa")
    https://nobody:nobody@dev.naver.com/git/aaa.git
    '''
    return "https://nobody:nobody@dev.naver.com/git/%s.git" % proj_id


def read_txt(fname, encoding='utf-8'):
    """
    Read a file with encoding
    """
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            txt = f.read()
    except UnicodeDecodeError as e:
        print(f'read_txt({fname}, {encoding})')
        raise e

    return txt


def read_utf_or_cp(filename):
    """
    Try to read a file first with utf and then cp encodings
    """
    try:
        txt = read_txt(filename, encoding='utf-8')
    except UnicodeError:
        txt = read_txt(filename, encoding='cp949')

    return txt


def clone_naver_to(proj_id, path=""):
    '''
    git clone project (to a path if given)
    >>> clone_naver_to ("aaa", 'a')
    '''
    full_anon_path_naver = get_git_naver_anon(proj_id)
    cmd = "clone %s %s" % (full_anon_path_naver, path)
    git.git(cmd)


def submodule_naver_to(proj_id, path=""):
    '''
    git submodule add project (to a path if given)
    >>> submodule_naver_to ("aaa", 'a')
    '''
    full_anon_path_naver = get_git_naver_anon(proj_id)

    path_replaced = path.replace('\\', '/')

    # A/student_repository/tool
    cmd = "submodule add -f %s %s" % (full_anon_path_naver, path_replaced)
    git.git(cmd)


def paths_under_data(repository_local_path):
    '''
    return all subfolders under data/ folder
    '''
    raw = os.listdir(repository_local_path)
    result_list = [path_item for path_item in raw if os.path.isdir(path_item)]
    del raw
    return result_list


def pull_path(repository_path, b_verbose=False):
    """
    cd to repository_path
    git pull
    return to original path
    """

    org_path = repo_path.cd(repository_path)

    clean_repo_before_update(b_verbose=b_verbose, caller_name='pull_path')

    git.checkout('master', b_verbose=False)
    stdout, stderr = git.pull(b_verbose=False)

    # if there was an error during pull
    clean_repo_after_error(stdout, stderr, 'pull_path', b_verbose=False,)

    os.chdir(org_path)


def clean_repo_before_update(b_verbose=False, caller_name='',):
    if b_verbose:
        print(f"{caller_name}() : reset --hard HEAD")
    git.reset_hard_head()

    if b_verbose:
        print(f'{caller_name}() : clean -x -d -f')
    git.clean_xdf(b_verbose=False)


def clean_repo_after_error(stdout, stderr, caller_name, b_verbose=False,):

    # if there was an error during fetch
    if any((
        (stdout.startswith('CONFLICT')),
        ('fatal' in stderr),
        ('error' in stderr),
    )):
        # present error message
        print(f'{caller_name}() : Possible error while updating')
        print(os.getcwd())
        print(f'{caller_name}() : stdout :')
        print(stdout)
        print(f'{caller_name}() : stderr :')
        print(stderr)

        # cleanup
        print(f'{caller_name}() : clean -x -d -f')
        git.clean_xdf(b_verbose=True)
        # revert
        print(f"{caller_name}() : reset --hard HEAD")
        git.reset_hard_head()
    if b_verbose:
        print(f'{caller_name}() :', stdout)


def fetch_and_reset(repository_path, b_verbose=False, revision='origin/master', remote='origin'):
    """
    cd to repository_path
    git fetch
    git reset origin/master
    return to original path
    """

    org_path = repo_path.cd(repository_path)

    clean_repo_before_update(
        b_verbose=b_verbose, caller_name='fetch_and_reset')

    git.checkout('master', b_verbose=b_verbose)

    stdout, stderr = git.fetch(remote)

    clean_repo_after_error(
        stdout, stderr, 'fetch_and_reset__fetch', b_verbose=b_verbose,)

    stdout, stderr = git.reset_hard_revision(revision)

    clean_repo_after_error(
        stdout, stderr, 'fetch_and_reset__reset', b_verbose=b_verbose,)

    os.chdir(org_path)


if "__main__" == __name__:
    # read file
    found = get_proj_id_list(config['repository']['listFile'])
    print(("len(found) =", len(found)))
    clone_or_pull_repo_list(found)
