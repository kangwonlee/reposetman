import argparse
import sys

import git
import progress


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='checkout date')

    if argv[1:]:

        namespace = parser.parse_args(argv[1:])

    else:

        parser.parse_args(['--help'])


if "__main__" == __name__:
    main(sys.argv)
