"""Check the status of my library books.
"""

import yaml

from docopt import docopt
from robobrowser import RoboBrowser


def read_config(filename):
    with open('config.yaml', 'r') as in_conf:
        return yaml.load(in_conf)

def main(config_filename='config.yaml'):
    # Browse to a page with an upload form
    config = read_config(config_filename)

    browser = RoboBrowser()
    browser.open(config['base_url'])



if __name__ == '__main__':
    # args = docopt(__doc__)
    main()
