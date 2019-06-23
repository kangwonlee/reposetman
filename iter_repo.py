import ast


def get_section_list(config):
    # https://stackoverflow.com/questions/335695/lists-in-configparser
    return ast.literal_eval(config['operation']['sections'])


def gen_section(config):
    """
    Iterate over sections of the config file:

    """

    for section in get_section_list(config):
        yield section
