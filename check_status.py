"""Check the status of my library books.
"""

import json
import pprint
from datetime import datetime
import urllib

import yaml

from docopt import docopt
from robobrowser import RoboBrowser
from tabulate import tabulate

from six.moves import html_parser

def read_config(filename):
    with open('config.yaml', 'r') as in_conf:
        return yaml.load(in_conf)

class Status(object):
    def __init__(self, name):
        self.fees_cents = 0
        self.name = name
        self.time = datetime.now()
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
        return datetime.fromtimestamp(self.due_date)

    @property
    def is_overdue(self):
        return datetime.today() > self.due_at

    @property
    def days_left(self):
        return (self.due_at - datetime.today()).days

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

    def status(self, username, password, name=None):
        status = Status(name or username)

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

def to_rows(status):
    h = html_parser.HTMLParser()
    return [[
        loan.days_left,
        loan.dueDateString,
        loan.is_overdue and "*" * len("Overdue") or "",
        h.unescape(loan.title).decode('utf8'),
        h.unescape(loan.author).decode('utf8'),
        ] for loan in status.loans_by_due_date]

def main(config_filename='config.yaml'):
    # Browse to a page with an upload form
    config = read_config(config_filename)

    sc = StatusChecker(config)

    for account in config['accounts']:
        status = sc.status(account['username'], account['password'], account.get('name', None))
        print "Status for {}:".format(status.name)
        if len(status.loans) == 0:
            print "No loans."
        else:
            print tabulate(to_rows(status),
                    headers=("Days Left", "Due", "Overdue", "Title", "Author"))
        if status.fees_cents > 0:
            print "You have ${:0.2f} in fees.".format(status.fees_cents/100.0)
        print


if __name__ == '__main__':
    # args = docopt(__doc__)
    main()
