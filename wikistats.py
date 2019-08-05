#!/usr/bin/env python3

import argparse
import json
import re

import pywikibot as pwb

from datetime import datetime as dt


# Hard-coded defaults as global constants.
ALLTIME_FROM_DATE = '2017-07-01T00:00:00Z'
PERUSER_FROM_DATE = '2008-12-01T00:00:00Z'
MAXCONTRIB = 10000


def alltime(wiki, asof=dt.utcnow(), since=ALLTIME_FROM_DATE, excludes=None):
    alltime_active_users = []
    active_users = {}
    for user in wiki.allusers():
        if user['editcount'] > 0:
            alltime_active_users.append(user['name'])
    for user in alltime_active_users:
        w_user = pwb.User(wiki, user)
        for contrib in w_user.contributions(total=MAXCONTRIB, end=since, start=asof):
            if excludes and contrib[0].title() in excludes:
                continue
            try:
                active_users[user] += 1
            except KeyError:
                active_users[user] = 1
    au_list = sorted([(u, c) for (u, c) in active_users.items()], key=lambda x: x[1], reverse=True)
    for (u, c) in au_list:
        print(c, u)


def peruser(wiki, username, asof=dt.utcnow(), since=PERUSER_FROM_DATE, months_since=None,
            weeks_since=None, namespaces=(), created_only=False, include_redirects=False,
            excludes=None):
    user = pwb.User(wiki, username)
    stats = {}
    stats['years'] = {}
    stats['months'] = {}
    stats['weeks'] = {}
    for contrib in user.contributions(total=MAXCONTRIB, end=since, start=asof,
                                      namespaces=namespaces):
        if excludes and contrib[0].title() in excludes:
            continue
        if created_only and contrib[1] != contrib[0].oldest_revision['revid']:
            continue
        if not include_redirects and re.match(
                r'^\s*#(виж|redirect)\s+\[\[',
                contrib[0].getOldVersion(
                    contrib[0].oldest_revision['revid']),
                flags=re.I):
            continue
        year = contrib[2].strftime('%Y')
        month = contrib[2].strftime('%m')
        week = str(contrib[2].isocalendar()[1]).zfill(2)

        try:
            stats['years'][year] += 1
        except KeyError:
            stats['years'][year] = 1

        if months_since:
            if int(year) < int(months_since.split('-')[0]):
                continue
            if int(year) < int(months_since.split('-')[0]) and \
                    int(month) == int(months_since.split('-')[1]):
                continue
        try:
            stats['months'][year + ' ' + month] += 1
        except KeyError:
            stats['months'][year + ' ' + month] = 1

        if weeks_since:
            if int(year) < int(weeks_since.split('-')[0]):
                continue
            if int(year) < int(weeks_since.split('-')[0]) and \
                    int(week) == int(weeks_since.split('-')[1]):
                continue
        try:
            stats['weeks'][year + ' ' + week] += 1
        except KeyError:
            stats['weeks'][year + ' ' + week] = 1

    print(json.dumps(stats, sort_keys=True, indent=4))


def init_parser():
    parser = argparse.ArgumentParser(
            description='Wikimedia Foundation projects user activity statistics',
            epilog='For a practical example, visit https://meta.wikimedia.org/wiki/PCP/N:BG/STAT',
            )
    parser.add_argument(
            'wiki',
            default='en:wikipedia',
            help='wiki to get stats from in lang.family format',
            )
    stat_object = parser.add_mutually_exclusive_group(required=True)
    stat_object.add_argument(
            '-t', '--totals',
            action='store_true',
            help='show total contributions for all users',
            )
    stat_object.add_argument(
            '-u', '--user',
            help='show detailed stats for user (without "User:" prefix)',
            )
    parser.add_argument(
            '-a', '--asof',
            help='only collect data before this timestamp, e.g. 2019-07-28T00:00:00Z '
                 '(default is current time)',
            )
    parser.add_argument(
            '-s', '--since',
            help='only collect data since this timestamp (default is ' + ALLTIME_FROM_DATE +
                 ' for totals and ' + PERUSER_FROM_DATE + ' for user stats)',
            )
    parser.add_argument(
            '-m', '--month-stats-since',
            metavar='YYYY-mm',
            help='produce month stats since month YYYY-mm',
            )
    parser.add_argument(
            '-w', '--week-stats-since',
            metavar='YYYY-WW',
            help='produce week stats since week YYYY-WW',
            )
    parser.add_argument(
            '-n', '--namespace',
            action='append',
            help='for user stats, only include this namespace (may be specified multiple times)',
            )
    parser.add_argument(
            '-c', '--created-only',
            action='store_true',
            help='only include the pages created by the user',
            )
    parser.add_argument(
            '-r', '--include-redirects',
            action='store_true',
            help='also include redirect pages',
            )
    parser.add_argument(
            '-x', '--exclude-pages',
            action='append',
            metavar='FULLPAGENAME',
            help='exclude a page from the stats (may be specified multiple times)',
            )
    return parser


def main(args=None):
    parser = init_parser()
    args = parser.parse_args(args)

    wiki = pwb.Site(args.wiki.split('.')[0], fam=args.wiki.split('.')[1])

    if args.totals:
        alltime(wiki, asof=args.asof, since=args.since, excludes=args.exclude_pages)
    else:
        peruser(wiki, args.user, asof=args.asof, since=args.since,
                months_since=args.month_stats_since, weeks_since=args.week_stats_since,
                namespaces=args.namespace, created_only=args.created_only,
                include_redirects=args.include_redirects, excludes=args.exclude_pages)


if __name__ == '__main__':
    main()

# vim: set ts=4 sts=4 sw=4 tw=100 et:
