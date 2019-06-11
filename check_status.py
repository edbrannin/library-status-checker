"""Check the status of my library books.
"""

import json
import urllib
import pprint

import arrow
import yaml
import pyaml
import click
import requests

from robobrowser import RoboBrowser
from tabulate import tabulate

from six.moves import html_parser

html_parser = html_parser.HTMLParser()

def read_config(filename):
    with open('config.yaml', 'r') as in_conf:
        return yaml.load(in_conf)

class Status(object):
    def __init__(self, name):
        self.fees_cents = 0
        self.name = name
        self.time = arrow.now()
        self.loans = list()

    def add_loan(self, loan):
        self.loans.append(Loan(loan))

    @property
    def loans_by_due_date(self):
        return sorted(self.loans, key=lambda x: x.due_date)

def today():
    return arrow.now().floor('day')


class Loan(object):
    def __init__(self, data):
        self.data = data
        self.due_date = self.data['dueDate'] / 1000
        self.due_at_string = self.due_at.format('ddd, YYYY-MM-DD')
        self.renewalCountString = "{1}{0}{1}".format(self.renewalCount, self.renewalCount == 2 and '*' or '')

    def __getattr__(self, key):
        return self.data[key]

    @property
    def due_at(self):
        return arrow.get(self.due_date).ceil('day')

    @property
    def is_overdue(self):
        return today() > self.due_at

    @property
    def days_left(self):
        return (self.due_at - today()).days

    @property
    def author(self):
        return html_parser.unescape(self.data['author']).decode('utf8')

    @property
    def title(self):
        return html_parser.unescape(self.data['title']).decode('utf8')

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
        login = self.post("/login", dict(
            username=username,
            lastName=password,
            password=password,
            rememberMe=False))
        login_json = login.json()
        if not login_json['success']:
            print "Unable to log in: {}".format(login_json['error'])
            print login.text
            return status
        isAuthenticated = self.get('/isAuthenticated')
        if not isAuthenticated.json():
            print('isAuthenticated is not true!: {}'.format(isAuthenricated))
            return status
        account_summary = self.get('/account/summary')
        try:
            account_summary.json()
        except:
            print "Account summary text:"
            print account_summary.text
            raise
        account_summary_json = account_summary.json()['accountSummary']
        status.fees_cents = account_summary_json['fees']
        try:
            for loan in account_summary_json['chargeItems']:
                status.add_loan(loan)
        except:
            print 'Error getting charge items: {}'.format(pprint.pformat(account_summary_json))
            raise

        return status

    @property
    def session(self):
        return self.browser.session

    @property
    def base_url(self):
        return self.config['library']['base_url']

def to_row(loan):
    try:
        return [
            loan.days_left,
            loan.due_at_string,
            loan.renewalCountString,
            loan.is_overdue and "*" * len("Overdue") or "",
            loan.title,
            loan.author,
        ]
    except:
        print('Error formatting loan:')
        pprint.pprint(loan.data)
        raise

def to_rows(status):
    return [to_row(loan) for loan in status.loans_by_due_date]

def push(title, url, message, API_KEY):
    r = requests.post("https://api.pushbullet.com/v2/pushes",
            data=dict(title=title, url=url, body=message, type="link"),
            auth=(API_KEY, None))
    # print r.text

def alert_loans(owner_name, loans, base_url, api_key, alert_days=0):
    due_loans = [loan for loan in loans if loan.days_left < int(alert_days)]
    print "Found {} loans due in {} days or sooner.".format(len(due_loans), alert_days)

    if due_loans:
        print tabulate([(loan.days_left, loan.title, loan.author) for loan in due_loans],
                headers=("Days Left", "Renewals", "Title", "Author"))

        title = "{} has loans due {}".format(
                owner_name, due_loans[0].due_at.humanize())
        body = "; ".join([
                "'{}'".format(loan.title)
                for loan in due_loans]),
        push(title,
            base_url,
            body,
            api_key
            )


@click.command()
@click.option("-d", "--debug", default=False, type=bool, is_flag=True)
@click.option("-a", "--alert-days", default=None)
def main(config_filename='config.yaml', debug=False, alert_days=None):
    # Browse to a page with an upload form
    config = read_config(config_filename)

    # TODO Search each account in parallel, then show results at the end
    sc = StatusChecker(config)

    for account in config['accounts']:
        status = sc.status(account['username'], account['password'], account.get('name', None))
        print "Status for {}:".format(status.name)
        if len(status.loans) == 0:
            print "No loans."
        else:
            print tabulate(to_rows(status),
                    headers=("Days Left", "Due", "Renewals", "Overdue", "Title", "Author"))
            if alert_days is not None:
                alert_loans(account.get('name', 'Someone'),
                        status.loans,
                        sc.base_url,
                        config['pushbullet']['api_key'],
                        alert_days)

        if status.fees_cents > 0:
            print "You have ${:0.2f} in fees.".format(status.fees_cents/100.0)
        print
        if debug:
            pyaml.p([l.data for l in status.loans_by_due_date])


if __name__ == '__main__':
    main()
