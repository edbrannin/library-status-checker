"""Check the status of my library books.
"""

import json
import pprint
import time
import urllib

import yaml

from docopt import docopt
from robobrowser import RoboBrowser

from six.moves import html_parser

def read_config(filename):
    with open('config.yaml', 'r') as in_conf:
        return yaml.load(in_conf)

class Status(object):
    def __init__(self, name):
        self.fees_cents = 0
        self.name = name
        self.time = time.time()
        self.loans = list()

    def add_loan(self, loan):
        self.loans.append(Loan(loan))

    @property
    def loans_by_due_date(self):
        return sorted(self.loans, key=lambda x: x.due_date)

class Loan(object):
    def __init__(self, data):
        self.data = data
        self.due_date = self.data['dueDate'] / 1000

    def __getattr__(self, key):
        return self.data[key]

    @property
    def due_at(self):
        return time.gmtime(self.due_date)

    @property
    def is_overdue(self):
        return time.time() > self.due_date

class StatusChecker(object):
    def __init__(self, config):
        self.browser = RoboBrowser()
        self.config = config

    def post(self, url, data):
        full_url = self.base_url + url
        data_json = json.dumps(data)
        return self.session.post(full_url, data=data_json)

    def get(self, url):
        full_url = self.base_url + url
        return self.session.get(full_url)

    def status(self, username, password, alias=None):
        status = Status(alias or username)

        self.browser.open(self.base_url)
        self.post("/login", dict(
            username=username,
            lastName=password,
            password=password,
            rememberMe=False))
        account_summery = self.get('/account/summary')
        status.fees_cents = account_summery.json()['accountSummary']['fees']
        status_response = self.get('/loans/0/20/Status')
        for loan in status_response.json()['loans']:
            status.add_loan(loan)
        return status

    @property
    def session(self):
        return self.browser.session

    @property
    def base_url(self):
        return self.config['library']['base_url']

def main(config_filename='config.yaml'):
    # Browse to a page with an upload form
    config = read_config(config_filename)

    sc = StatusChecker(config)

    h = html_parser.HTMLParser()

    for account in config['accounts']:
        status = sc.status(account['username'], account['password'], account.get('alias', None))
        print "Status for {}:".format(status.name)
        for loan in status.loans_by_due_date:
            title = h.unescape(loan.title).decode('utf8') 
            author = h.unescape(loan.author).decode('utf8') 
            if loan.is_overdue:
                print "*** OVERDUE: {} by {} was due on {} ***".format(title, author, loan.dueDateString)
            else:
                print "{} by {} is due on {}".format(title, author, loan.dueDateString)
        if len(status.loans) == 0:
            print "No loans."
        if status.fees_cents > 0:
            print "You have ${:0.2f} in fees.".format(status.fees_cents/100.0)


if __name__ == '__main__':
    # args = docopt(__doc__)
    main()
