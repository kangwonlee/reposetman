import tempfile


def get_tempfile_name(suffix=None,):
    _, filename = tempfile.mkstemp(suffix=None, text=True)
    return filename
