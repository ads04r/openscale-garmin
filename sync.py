#!/usr/bin/env python
# -*- coding: utf-8 -*-

from openscalecsv import OpenScaleCSV
from fit import FitEncoder_Weight
from garmin_uploader.workflow import Workflow # pip install garmin-uploader
from tempfile import mkstemp

from optparse import OptionParser
from optparse import Option
from optparse import OptionValueError
from datetime import date
from datetime import datetime
import time
import sys
import os


GARMIN_USERNAME = ''
GARMIN_PASSWORD = ''
CSV_FILE = ''


class DateOption(Option):
    def check_date(option, opt, value):
        valid_formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d']
        for f in valid_formats:
            try:
                dt = datetime.strptime(value, f)
                return dt.date()
            except ValueError:
                pass
        raise OptionValueError('option %s: invalid date or format: %s. use following format: %s'
                                 % (opt, value, ','.join(valid_formats)))
    TYPES = Option.TYPES + ('date',)
    TYPE_CHECKER = Option.TYPE_CHECKER.copy()
    TYPE_CHECKER['date'] = check_date


def main():
    usage = 'usage: sync.py [options]'
    p = OptionParser(usage=usage, option_class=DateOption)
    p.add_option('--csv-file', '--csv',
                 default=CSV_FILE, metavar='<file>', help='csv file exported from openScale.')
    p.add_option('--garmin-username', '--gu',
                 default=GARMIN_USERNAME, metavar='<user>', help='username to login Garmin Connect.')
    p.add_option('--garmin-password', '--gp',
                 default=GARMIN_PASSWORD, metavar='<pass>', help='password to login Garmin Connect.')
    p.add_option('-f', '--fromdate', type='date', default=date.today(), metavar='<date>')
    p.add_option('-t', '--todate', type='date', default=date.today(), metavar='<date>')
    p.add_option('--no-upload', action='store_true', help="Won't upload to Garmin Connect and output binary-strings to stdout.")
    p.add_option('-v', '--verbose', action='store_true', help='Run verbosely')
    opts, args = p.parse_args()

    sync(**opts.__dict__)


def sync(csv_file, garmin_username, garmin_password,
         fromdate, todate, no_upload, verbose):

    def verbose_print(s):
        if verbose:
            if no_upload:
                sys.stderr.write(s)
            else:
                sys.stdout.write(s)

    if csv_file == '':
        verbose_print("--csv_file is required\n")
        exit(1)
    if not(os.path.isfile(csv_file)):
        verbose_print("File " + csv_file + " not found\n")
        exit(1)

    # OpenScale CSV
    osc = OpenScaleCSV()
    osc.load(csv_file)
    startdate = int(time.mktime(fromdate.timetuple()))
    enddate = int(time.mktime(todate.timetuple())) + 86399
    groups = []
    for ix in range(0, osc.records()):
        item = osc.record(ix)
        dt = int(time.mktime(item['dateTime'].timetuple()))
        if dt < startdate:
            continue
        if dt > enddate:
            continue
        groups.append(item)

    # create fit file
    verbose_print('generating fit file...\n')
    fit = FitEncoder_Weight()
    fit.write_file_info()
    fit.write_file_creator()

    for group in groups:
        dt = group['dateTime']
        weight = group['weight']
        fat_ratio = group['fat']
        fit.write_device_info(timestamp=dt)
        fit.write_weight_scale(timestamp=dt, weight=weight, percent_fat=fat_ratio)
        verbose_print('appending weight scale record... %s %skg %s%%\n' % (dt, weight, fat_ratio))
    fit.finish()

    if no_upload:
        sys.stdout.write(fit.getvalue())
        return

    # create temporary file
    fi, fn = mkstemp()
    fn = fn + '.fit'
    fp = open(fn, 'w')
    fp.write(fit.getvalue())
    fp.close()

    # garmin connect
    verbose_print('attempting to upload fit file...\n')
    workflow = Workflow(paths=[fn], username=garmin_username, password=garmin_password)
    workflow.run()


if __name__ == '__main__':
    main()
