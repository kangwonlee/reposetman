import os
import tempfile


def get_tempfile_name(suffix: str=None) -> str:
    with tempfile.NamedTemporaryFile(mode='wt', suffix=suffix, encoding='utf-8', delete=True) as fp:
        filename = fp.name

    if 'nt' == os.name:
        filename = os.path.basename(filename)

    return filename


def write_to_temp_file(content: str, mode: str='wt', suffix: str='.py', encoding: str='utf-8',):
    with tempfile.NamedTemporaryFile(mode='wt', suffix='.py', encoding='utf-8', delete=False) as argv_file:
        argv_file.write(content)
    return argv_file
