import os
import shutil
import subprocess
import sys
import urllib.parse as up


def add_if_missing(add_this, path_list_str):
    """
    if a path is missing in a path list separated by ';',
    append it
    """
    path_list = path_list_str.split(';')

    if add_this in path_list:
        pass
    else:
        path_list.append(add_this)
    return ';'.join(path_list)


def gen_git_path_dict_list(file_path='git_path.cfg'):
    """
    Generate line by line
    """
    # open a file
    with open(file_path, 'rt') as f:
        # iterate line by line
        for line in f:
            # generate each line
            yield line.strip()


def which_git():
    """
    run `which git`

    >>> os.path.exists(which_git())
    True
    """
    # python 3.3 or higher
    which_git = shutil.which('git')
    result = None
    if os.path.exists(which_git):
        if os.access(which_git, os.X_OK):
            result = which_git
        else:
            raise PermissionError(f"{which_git} is not executable")
    else:
        raise FileNotFoundError(f"{which_git} does not exist")
    return result


def find_git_in_path():
    """
    search for `git` in PATH environment variable
    """
    PATH = 'PATH'
    result = []
    if PATH in os.environ:
        for path in os.environ[PATH].split(os.pathsep):
            if os.path.exists(path):
                if 'git' in os.listdir(path):
                    print(f"{path} has git")
                    result.append(path)
            else:
                print(f"{path} does not exist")

    return result


# begin set git path
git_exe_path = which_git()

# end set git path


def run_command(cmd, b_verbose=True, in_txt=None, b_show_cmd=False):
    """
    execute git command & print

    :param str cmd: git command
    :param bool b_verbose:
    :param bytes in_txt: standard input (None by default)
    :return: messages through stdout and stderr

    >>> run_command("git status") # == git status
    """

    # https://docs.python.org/3/library/subprocess.html#replacing-os-popen-os-popen2-os-popen3
    # On windows FileNotFoundError may occur: https://stackoverflow.com/questions/25794941/python-subprocess-not-working-on-windows-7

    # TODO : Consider adding timeout feature
    # https://docs.python.org/3/library/subprocess.html#using-the-subprocess-module

    if b_show_cmd:
        print(f'run_command({repr(cmd)})')

    # ideasman42, How to set sys.stdout encoding in Python 3?, Stackoverflow, 2011 10 23, https://stackoverflow.com/a/7865013
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    assert isinstance(cmd, (tuple, list, str)), type(cmd)
    if isinstance(cmd, (tuple, list)):
        for cmd_element in cmd:
            assert isinstance(cmd_element, str), cmd

    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        env=env,
    )

    # https://stackoverflow.com/questions/163542/python-how-do-i-pass-a-string-into-subprocess-popen-using-the-stdin-argument
    msgo, msge = p.communicate(input=in_txt)

    if b_verbose:
        if msgo:
            print(msgo)
        if msge:
            print(msge)

    # to save memory
    del p

    return msgo, msge


def git_common(cmd, b_verbose=True):
    """
    execute git command & print

    :param str cmd: git command
    :param bool b_verbose:
    :return: messages through stdout and stderr

    >>> git_common("status") # == git status
    """

    return run_command((git_exe_path,) + tuple(cmd), b_verbose)


def git(cmd, bVerbose=True):
    """
    execute git command & print

    :param str cmd: git command
    :param bool bVerbose:
    :return:

    >>> git("status") # == git status
    """

    msgo, msge = git_common(cmd, bVerbose)

    if msgo:
        if not msge:
            msg = msgo
        else:
            msg = msgo + '''
''' + msge
    else:
        msg = msge

    del msgo, msge
    return msg


def checkout(commit=False, repo_path=False, b_verbose=False):
    if repo_path:
        # change working folder
        cwd_backup = os.getcwd()
        os.chdir(repo_path)

    # checkout specific commit
    checkout_cmd_list = [git_exe_path,
                         'checkout',
                         ]

    if commit:
        checkout_cmd_list.append(commit)
    else:
        checkout_cmd_list.append('HEAD')

    # run git command
    stdout, stderr = run_command(checkout_cmd_list, b_verbose=b_verbose)

    # even if b_verbose is false, print stderr
    if stderr:

        b_stderr_already_on = starts_with_already_on(stderr)
        b_stderr_detached_head = "You are in 'detached HEAD' state." in stderr
        b_switch_success = "Switched to branch '{branch}'".format(
            branch=commit) in stderr
        b_previous_now = (stderr.startswith('Previous HEAD position was')) and (
            'HEAD is now at' in stderr)

        if all([not b_stderr_already_on, not b_stderr_detached_head, not b_switch_success, not b_previous_now]):
            print(os.getcwd())
            print(stderr)

    else:
        if b_verbose:
            print(stdout)

    if repo_path:
        # return to original path
        os.chdir(cwd_backup)

    return stdout, stderr


def starts_with_already_on(stderr):
    b_stderr_already_on = stderr.startswith('Already on ')
    return b_stderr_already_on


def log_last_commit():
    msgo, msge = run_command(
        (git_exe_path, 'log', '-1'),
        b_verbose=False
    )

    # output error check
    if msgo and not msge:
        msgo_split = msgo.split()
        result = msgo_split[0]
    else:
        result = 'N/A'

    return result


def get_last_sha(b_full=False, path='', branch=''):
    # sometimes full SHA is necessary
    if b_full:
        format_string = '%H'
    else:
        format_string = '%h'

    command_list = [git_exe_path, 'log',
                    '--pretty=format:{h}'.format(h=format_string), '-1']

    if branch and path:
        command_list += [branch, '--', path]
    elif path:
        command_list.append(path)
    elif branch:
        command_list.append(branch)

    # get the last sha from git log of the latest commit
    msgo, msge = run_command(
        tuple(command_list),
        b_verbose=False
    )

    # output error check
    if msgo and not msge:
        msgo_split = msgo.split()
        result = msgo_split[0]
    else:
        result = 'N/A'

    return result


def tag(tag_string, revision=''):

    git_cmd = [git_exe_path, 'tag', tag_string]

    if revision:
        git_cmd.append(str(revision))

    msgo, msge = run_command(
        git_cmd,
        b_verbose=False,
    )

    if msgo or msge:
        print('tag({tag}) failed.\nmsgo:\n{msgo}\nmsge:\n{msge}'.format(
            tag=tag_string, msgo=msgo, msge=msge))

    return not (msgo or msge)


def delete_tag(tag_string):
    git_cmd = [git_exe_path, 'tag', '--delete', tag_string]

    msgo, msge = run_command(
        git_cmd,
        b_verbose=False,
    )

    return msgo.startswith('Deleted tag') and not msge


def get_tags():

    git_cmd = [git_exe_path, 'tag']

    msgo, msge = run_command(
        git_cmd,
        b_verbose=False,
    )

    return [tag.strip() for tag in msgo.splitlines()]


def get_refs_tag_deref():
    """
    Obtain list of (sha, tag) of the current repository
    SHAs show up on the `git log`
    """

    # Obtain sha's and tags
    # dereference may include sha's in `git log`
    git_cmd = [git_exe_path, 'show-ref', '--tags', '--dereference']

    msgo, msge = run_command(
        git_cmd,
        b_verbose=False,
    )

    if msge:
        raise SystemError(msge)

    # Obtain SHA's from the log
    stdout_log, stderr_log = run_command(
        (git_exe_path, 'log', '--pretty=%H'),
        b_verbose=False,
    )
    if stderr_log:
        raise SystemError(stderr_log)

    sha_tuple = tuple(stdout_log.splitlines())

    # collect tags and sha's from the dereference
    result_list = []

    # line loop
    for tag_line in msgo.splitlines():
        sha, ref_tag = tag_line.split()

        if sha in sha_tuple or ref_tag.endswith('^{}'):
            tag = ref_tag.strip('^{}')[10:]
            result_list.append((tag, sha))

    return result_list


def status():
    git_cmd = [git_exe_path, 'status']

    return run_command(
        git_cmd,
        b_verbose=False,
    )


def pull(b_verbose=False):
    git_cmd = (git_exe_path, 'pull')

    return run_command(git_cmd, b_verbose=b_verbose)


def reset_hard_head(b_verbose=False):
    git_cmd = (git_exe_path, 'reset', '--hard', 'HEAD')

    return run_command(git_cmd, b_verbose=b_verbose)


def ls_remote_tag(remote='origin', b_verbose=False):
    git_cmd = (git_exe_path, 'ls-remote', '--tags', remote)

    stdout, stderr = run_command(git_cmd, b_verbose=b_verbose)
    if stderr:
        raise SystemError(stderr)

    result_list = []

    for line in stdout.splitlines():
        # dereference
        if line.endswith('^{}'):
            sha, ref = line.split()
            tag = ref.replace('^{}', '').replace('refs/tags/', '')
            result_list.append((sha, tag))

    return result_list


def has_a_tag(commit=None):
    if commit is None:
        commit = get_last_sha(b_full=True)

    result = False

    # tag__sha loop
    for _, sha in get_refs_tag_deref():
        if sha == commit:
            result = True
            break

    return result


def clean_xdf(b_verbose=False):
    if b_verbose:
        print('clean_xdf(): cwd =', os.getcwd())

    run_command((git_exe_path, 'clean', '-x', '-d', '-f'), b_verbose=b_verbose)


def get_current_branch(b_verbose=False):
    # https://stackoverflow.com/questions/1417957/show-just-the-current-branch-in-git/1418022
    return run_command((git_exe_path, 'rev-parse', '--abbrev-ref', 'HEAD'), b_verbose=b_verbose)[0].strip()


def get_remote_branch_list(b_verbose=False):
    """
    Get a list of remote branches of current repository
    """
    stdout, _ = run_command(
        (git_exe_path, 'branch', '--remote'), b_verbose=b_verbose)

    result = []

    for branch in stdout.splitlines():
        if '/HEAD ->' not in branch:
            result.append(branch.strip())

    return result


def clone(repo_url, path="", id=""):
    """
    git clone repo_url

    :param str repo_url:
    :param str path:
    :return:
    """
    # TODO : consider moving this to git module
    if id:
        repo_url = set_id_to_url(repo_url, id)

    cmd_list = [git_exe_path, 'clone', repo_url]

    if path:
        cmd_list.append(path)

    # for Linux
    msg = run_command(cmd_list)

    return msg


def set_id_to_url(url, id):
    """
    add id to or replace in url
    :param str url:
    :param str id:
    :return:
    """

    # id needs to go into the netloc part
    p = up.urlparse(url)

    # netloc may or may not already include an id
    if '@' not in p.netloc:
        # add
        netloc = id + '@' + p.netloc
    else:
        # replace
        i = p.netloc.index('@')
        netloc = id + p.netloc[i:]
    # make the new url
    new_url = up.urlunparse(
        (p.scheme, netloc, p.path, p.params, p.query, p.fragment))

    return new_url


def git_common_list(git_cmd_list, b_verbose=False):
    """
    execute git command & print

    :param list git_cmd_list: list of git command
    :param bool b_verbose:
    :return: messages through stdout and stderr

    >>> git_common_list(["status"]) # == git status
    """

    assert isinstance(git_cmd_list, (list, tuple))

    # Make a copy not to leave influences in the git_cmd_list
    cmd_list = list(git_cmd_list)

    # Put the path at the beginning of the cmd_list
    cmd_list.insert(0, git_exe_path)

    # Run command
    return run_command(cmd_list, b_verbose)


def fetch(repo=''):
    """
    >>> fetch()
    or 
    >>> fetch('origin')
    """

    cmd_list = ['fetch']

    if repo:
        cmd_list.append(repo)

    return git_common_list(['fetch', repo])


def reset_hard_revision(revision):
    return git_common_list(['reset', '--hard', revision])


if "__main__" == __name__:
    # check if git works fine
    git("status")
