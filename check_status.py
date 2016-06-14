"""Check the status of my library books.
"""

import json
import pprint
import time

import yaml

from docopt import docopt
from robobrowser import RoboBrowser


def read_config(filename):
    with open('config.yaml', 'r') as in_conf:
        return yaml.load(in_conf)

class StatusChecker(object):
    def __init__(self, config):
        self.browser = RoboBrowser()
        self.config = config

    def post(self, url, data):
        full_url = self.base_url + url
        data_json = json.dumps(data)
        print "POSTing to {} with data {}".format(full_url, data_json)
        return self.session.post(full_url, data=data_json)

    def get(self, url):
        full_url = self.base_url + url
        return self.session.get(full_url)

    def status(self, username, password):
        self.browser.open(self.base_url)
        r = self.post("/login", dict(
            username=username,
            lastName=password,
            password=password,
            rememberMe=False))
        pprint.pprint(r.json())
        rr = self.get('/account/summary')
        fees = rr.json()['accountSummary']['fees']
        if fees > 0:
            print "You have ${} in fees.".format(fees/100.0)
        status = self.get('/loans/0/20/Status')
        for loan in status.json()['loans']:
            author = loan['author']
            dueDateEpoch = loan['dueDate'] / 1000
            dueDateString = loan['dueDateString']
            title = loan['title']
            print "{} by {} is due on {}".format(title, author, dueDateString)
            if time.time() > dueDateEpoch:
                print "*** OVERDUE ***"

    @property
    def session(self):
        return self.browser.session

    @property
    def base_url(self):
        return self.config['library']['base_url']

def main(config_filename='config.yaml'):
    # Browse to a page with an upload form
    config = read_config(config_filename)

    pprint.pprint(config)

    sc = StatusChecker(config)

    for account in config['accounts']:
        status = sc.status(account['username'], account['password'])
        print status

if __name__ == '__main__':
    # args = docopt(__doc__)
    main()
