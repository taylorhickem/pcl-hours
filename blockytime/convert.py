""" this script

1. converts the toggle raw export into the same file format as blockytime.
2. combines the two files into a single file
"""

# -------------------------------------------------------------
# import dependencies
# -------------------------------------------------------------
import os
import shutil
import pandas as pd
import datetime as dt

# -------------------------------------------------------------
# module variables

FILENAMES = {
    'blockytime': 'blockytime_export.csv',
    'toggl': 'toggl_time_entries.csv'
}
# -------------------------------------------------------------
# main
# -------------------------------------------------------------

# 1. convert the toggle raw export into the same file format as blockytime
keep_fields = [
    'Start date',
    'Start time',
    'Duration',
    'Project',
    'Tags',
    'Description'
]

rename_fields = {
    'start_time': 'Start',
    'Project': 'Event Type',
    'Tags': 'Event Object',
    'Description': 'Comment'
}


def convert_files():
    # 1.1 import toggle csv
    tr = pd.read_csv(FILENAMES['toggl'])
    tr = tr[keep_fields].copy()

    # 1.2 convert date and time into single datetime field
    tr['start_time'] = tr.apply(lambda x: x['Start date'] + ' ' + x['Start time'], axis=1)
    del tr['Start date'], tr['Start time']

    # 1.3 convert duration into minutes as integer
    tr['Duration'] = tr['Duration'].apply(lambda x: convert_toggl_minutes(x))

    # 1.4 rename fields same as blockytime
    tr.rename(columns=rename_fields, inplace=True)

    # 2. blockytime records append extra :00 seconds to datetime field
    bt = pd.read_csv(FILENAMES['blockytime'])
    bt['Start'] = bt['Start'].apply(lambda x: x + ':00')

    # 3. combine the two files into a single file
    df = pd.concat([bt, tr], axis=0)
    df.to_csv('events.csv', index=False)

# -------------------------------------------------------------
# helper functions
# -------------------------------------------------------------


def convert_toggl_minutes(min_str):
    min_int = 0
    min_sec = [int(x) for x in min_str.replace(' min', '').split(':')]
    min_int = round(min_sec[0] + min_sec[1] / 60)
    return min_int


if __name__ == "__main__":
    convert_files()


# -------------------------------------------------------------
# END
# -------------------------------------------------------------