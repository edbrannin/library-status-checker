import arrow

from check_status import Status, Loan, StatusChecker, to_rows

today = arrow.now().floor('day')
yesterday = today.shift(days=-1)
tomorrow = today.shift(days=+1)

def test_days_left_tomorrow():
    loan = Loan(dict(dueDate=tomorrow.timestamp * 1000, renewalCount=0))
    print today
    assert loan.days_left == 1
    assert not loan.is_overdue

def test_days_left_today():
    loan = Loan(dict(dueDate=today.timestamp * 1000, renewalCount=0))
    assert loan.days_left == 0
    assert not loan.is_overdue

def test_days_left_yesterday():
    loan = Loan(dict(dueDate=yesterday.timestamp * 1000, renewalCount=0))
    assert loan.days_left == -1
    assert loan.is_overdue
