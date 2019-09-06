import os
import urllib.parse as up

repository_local_path = os.curdir


def get_local_repo_path(repo_name):
    """
    get path to local repository for given project id

    :param str repo_name:
    :return:
    """
    return os.path.join(repository_local_path, repo_name)


def get_repo_name_from_url(repo_url):
    # repo_url.strip('/') : without this strip() call, if a url ends with '/', this function would return '' as repostiory name
    p = up.urlparse(repo_url.strip('/'))
    return os.path.splitext(os.path.basename(p.path))[0]


def cd_proj_repo(proj_id):
    '''
    change directory to project repository
    '''
    # store original path
    original_path = os.path.abspath(os.curdir)
    # change path to project repository
    repo_path = get_local_repo_path(proj_id)
    os.chdir(repo_path)
    return original_path


def cd(path):
    '''
    change directory & return original path
    '''
    original_path = os.path.abspath(os.curdir)

    os.chdir(path)
    return original_path
