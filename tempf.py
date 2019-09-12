import os
import tempfile


def get_tempfile_name(suffix=None, istext=True):
    _, filename = tempfile.mkstemp(suffix=suffix, text=istext)

    if 'nt' == os.name:
        filename = os.path.basename(filename)

    return filename
