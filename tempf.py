import os
import tempfile


def get_tempfile_name(suffix=None, istext=True):
    _, filename = tempfile.mkstemp(suffix=suffix, text=istext)

    if 'nt' == os.name:
        filename = os.path.basename(filename)

    return filename


def write_to_temp_file(mode='wt', suffix='.py', encoding='utf-8', content=""):
    with tempfile.NamedTemporaryFile(mode='wt', suffix='.py', encoding='utf-8', delete=False) as argv_file:
        argv_file.write(content)
    return argv_file
