def is_ignore_path(path):
    # check if ignore
    is_dot_git_path = ".git" in path
    is_xcode_path = "python.xcodeproj" in path
    is_pycharm_path = ".idea" in path
    is_vscode_path = ".vscode" in path
    is_pycache_path = "__pycache__" in path
    b_ignore = any(
        (
            is_dot_git_path,
            is_xcode_path,
            is_pycharm_path,
            is_vscode_path,
            is_pycache_path,
        )
    )
    return b_ignore


def is_python(filename):
    # check extension
    return filename.endswith(".py")
