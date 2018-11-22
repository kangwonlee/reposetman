"""
Collect repositories of the chapters into a submodule
"""
import configparser
import sys
import urllib.parse as up


def main(argv):
    config = configparser.ConfigParser()
    config.read(argv[0])
    print(config['operation']['sections'])


if "__main__" == __name__:
    main(sys.argv[1:])
