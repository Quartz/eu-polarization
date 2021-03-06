#!/usr/bin/env python

import statistics

from agate import csv
import sqlite3 as sqlite

EU = [
    'Austria',
    'Belgium',
    'Bulgaria',
    'Croatia',
    'Cyprus',
    'Czech Republic',
    'Denmark',
    'Estonia',
    'Finland',
    'France',
    'Germany',
    'Greece',
    'Hungary',
    'Ireland',
    'Italy',
    'Latvia',
    'Lithuania',
    'Luxembourg',
    'Malta',
    'Netherlands',
    'Poland',
    'Portugal',
    'Romania',
    'Slovakia',
    'Slovenia',
    'Spain',
    'Sweden',
    'United Kingdom'
]

ELECTION_TYPES = [
    'parliament',
    'ep'
]

EU_ELECTIONS_YEARS = [
    1979, 1984, 1989, 1994, 1999, 2004, 2009, 2014
]

START_YEAR = 1980
END_YEAR = 2015

FAR_LEFT = 2.5
CENTER_LEFT = 4
CENTER_RIGHT = 6
FAR_RIGHT = 7.5


def eu_wide(db, election_type):
    """
    Aggregate data for EU parliamentary elections.
    """
    summary_rows = []
    detail_rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        left_right_list = []
        far_left = 0
        far_right = 0
        center = 0
        total_seats = 0

        print(year)

        for country in EU:
            results = db.execute('''
                SELECT DISTINCT election_date
                FROM view_election
                WHERE country_name=? AND CAST(SUBSTR(election_date, 0, 5) AS INTEGER) < ? AND election_type=?
                ORDER BY election_date DESC
                ''',
                (country, year, election_type)
            )

            try:
                election_date = results.fetchone()[0]
            except TypeError:
                continue

            print(country, election_date)

            results = db.execute('''
                SELECT view_election.party_name_english, family_name, seats, view_election.left_right
                FROM view_election
                LEFT JOIN view_party
                ON view_election.party_id == view_party.party_id
                WHERE view_election.country_name=? AND election_date=? AND election_type=?
                ''',
                (country, election_date, election_type)
            )

            for row in results:
                party_name, family_name, seats, left_right = row

                if not seats:
                    continue

                total_seats += seats

                if not left_right:
                    continue

                left_right_list.extend([left_right] * seats)

                if left_right < FAR_LEFT:
                    far_left += seats
                elif CENTER_LEFT < left_right < CENTER_RIGHT:
                    center += seats
                elif left_right > FAR_RIGHT:
                    far_right += seats

                for i in range(seats):
                    detail_rows.append([year, country, party_name, family_name, left_right])

        seats_with_score = len(left_right_list)
        mean_score = statistics.mean(left_right_list)
        median_score = statistics.median(left_right_list)
        stdev_score = statistics.stdev(left_right_list)

        summary_rows.append([year, seats_with_score, total_seats, mean_score, median_score, stdev_score, far_left, center, far_right])

    with open('output/eu_wide_%s.csv' % election_type, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['year', 'seats_with_score', 'total_seats', 'mean', 'median', 'stdev', 'far_left', 'center', 'far_right'])
        writer.writerows(summary_rows)

    with open('output/eu_details_%s.csv' % election_type, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['year', 'country', 'party_name', 'family_name', 'left_right'])
        writer.writerows(detail_rows)


def eu_wide_cabinet(db):
    """
    Aggregate data for EU governments.
    """
    summary_rows = []
    detail_rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        left_right_list = []
        total_seats = 0

        print(year)

        for country in EU:
            results = db.execute('''
                SELECT DISTINCT start_date
                FROM view_cabinet
                WHERE country_name=? AND CAST(SUBSTR(start_date, 0, 5) AS INTEGER) < ?
                ORDER BY start_date DESC
                ''',
                (country, year)
            )

            try:
                start_date = results.fetchone()[0]
            except TypeError:
                continue

            print(country, start_date)

            results = db.execute('''
                SELECT party_name_english, family_name, seats, left_right
                FROM view_cabinet
                WHERE country_name=? AND start_date=?
                ''',
                (country, start_date)
            )

            for row in results:
                party_name, seats, left_right = row

                print(party_name, seats, left_right)

                if not seats:
                    continue

                total_seats += seats

                if not left_right:
                    continue

                left_right_list.extend([left_right] * seats)

                for i in range(seats):
                    detail_rows.append([year, country, party_name, family_name, left_right])

        seats_with_score = len(left_right_list)
        mean_score = statistics.mean(left_right_list)
        median_score = statistics.median(left_right_list)
        stdev_score = statistics.stdev(left_right_list)

        summary_rows.append([year, seats_with_score, total_seats, mean_score, median_score, stdev_score])

    with open('output/eu_wide_cabinet.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['year', 'seats_with_score', 'total_seats', 'mean', 'median', 'stdev'])
        writer.writerows(summary_rows)

    with open('output/eu_details_cabinet.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['year', 'country', 'party_name', 'family_name', 'left_right'])
        writer.writerows(detail_rows)


def eu_countries(db, election_type):
    """
    Aggregate data for individual EU member-country national parliaments.
    """
    out_rows = []

    for country in EU:
        print(country)

        for year in range(START_YEAR, END_YEAR + 1):
            results = db.execute('''
                SELECT DISTINCT election_date
                FROM view_election
                WHERE country_name=? AND CAST(SUBSTR(election_date, 0, 5) AS INTEGER) < ? AND election_type=?
                ORDER BY election_date DESC
                ''',
                (country, year, election_type)
            )

            try:
                election_date = results.fetchone()[0]
            except TypeError:
                continue

            results = db.execute('''
                SELECT party_name_english, seats, seats_total, left_right
                FROM view_election
                WHERE country_name=? AND election_date=? AND election_type=?
                ''',
                (country, election_date, election_type)
            )

            left_right_list = []
            far_left = 0
            far_right = 0
            center = 0

            for row in results:
                name, seats, seats_total, left_right = row

                if not seats:
                    continue

                if not left_right:
                    continue

                left_right_list.extend([left_right] * seats)

                if left_right < FAR_LEFT:
                    far_left += seats
                elif CENTER_LEFT < left_right < CENTER_RIGHT:
                    center += seats
                elif left_right > FAR_RIGHT:
                    far_right += seats

            seats_with_score = len(left_right_list)
            mean_score = statistics.mean(left_right_list)
            median_score = statistics.median(left_right_list)
            stdev_score = statistics.stdev(left_right_list)

            out_rows.append([country, year, seats_with_score, seats_total, mean_score, median_score, stdev_score, far_left, center, far_right])

    with open('output/eu_countries_%s.csv' % election_type, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['country', 'year', 'seats_with_score', 'seats_total', 'mean', 'median', 'stdev', 'far_left', 'center', 'far_right'])
        writer.writerows(out_rows)


def eu_countries_cabinet(db):
    """
    Aggregate data for individual EU member-country governments.
    """
    out_rows = []

    for country in EU:
        print(country)

        for year in range(START_YEAR, END_YEAR + 1):
            results = db.execute('''
                SELECT DISTINCT start_date
                FROM view_cabinet
                WHERE country_name=? AND CAST(SUBSTR(start_date, 0, 5) AS INTEGER) < ?
                ORDER BY start_date DESC
                ''',
                (country, year)
            )

            try:
                start_date = results.fetchone()[0]
            except TypeError:
                continue

            results = db.execute('''
                SELECT party_name_english, seats, left_right
                FROM view_cabinet
                WHERE country_name=? AND start_date=?
                ''',
                (country, start_date)
            )

            left_right_list = []

            for row in results:
                name, seats, left_right = row

                if not seats:
                    continue

                if not left_right:
                    continue

                left_right_list.extend([left_right] * seats)

            seats_with_score = len(left_right_list)
            mean_score = statistics.mean(left_right_list)
            median_score = statistics.median(left_right_list)
            stdev_score = statistics.stdev(left_right_list)

            out_rows.append([country, year, seats_with_score, mean_score, median_score, stdev_score])

    with open('output/eu_countries_cabinet.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['country', 'year', 'seats_with_score', 'mean', 'median', 'stdev'])
        writer.writerows(out_rows)


def main():
    db = sqlite.connect('file:data/parlgov-stable.db?mode=ro')

    eu_wide(db, 'parliament')
    # eu_wide(db, 'ep')
    # eu_wide_cabinet(db)
    # eu_countries_cabinet(db)
    eu_countries(db, 'parliament')
    # eu_countries(db, 'ep')

if __name__ == '__main__':
    main()
