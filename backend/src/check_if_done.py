#!/usr/bin/python3

from sys import argv
from time import gmtime, strftime
from ztdnslib import log
from os.path import isfile

lockfile = '/var/lib/0tdns/lockfile'
if isfile(lockfile):
    msg = '{} still exists, 0tdns is probably running for too long'\
          .format(lockfile)

    print(msg)

    # this script shall be run 15, 30 and 45 minutes after an hour;
    # in all cases we want to write to logs, but only at 30 or 45 minutes
    # we want to email the admin
    if int(strftime('%M', gmtime())) >= 30 and '--send-mail' in argv:
        print('Sending mail') # TODO send mail and delete this line

    log(msg)
