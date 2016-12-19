# Library Status Checker

Automatically check if your books are due.

Extra annoyance if they're overdue.

## Wait what?

My local library will email me twice when a book is approaching its due date:

1. 3 dats before due
2. 7 days overdue
3. (Possibly later?  I haven't let it get to 2 weeks yet.)

Sometimes I don't notice the emails and that's bad.
This project aims to bother me more when I need it.

## Usage

1. Copy `config.yaml.SAMPLE` to `config.yaml` and replace values as needed
2. Run `python check_status.py` (preferably in a nightly cron job).

## Future work

### Email notifications?

(or just stick with Pushbullet?)

* Boilerplate templates:
    * http://emailframe.work/
    * https://github.com/seanpowell/Email-Boilerplate
* Sending email:
    * https://docs.python.org/2/library/email-examples.html
    * https://docs.python.org/2/library/email.html
