import argparse
import sys

import git
import progress


def main(argv):

    parser = get_arg_parser()

    if argv[1:]:

        namespace = parser.parse_args(argv[1:])

    else:

        parser.parse_args(['--help'])


def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='checkout date in yyyy-mm-dd')
    parser.add_argument('--time', help='checkout time in hh:mm:ss', default='00:00:00')
    parser.add_argument('--config', help='config file')
    return parser


if "__main__" == __name__:
    main(sys.argv)
