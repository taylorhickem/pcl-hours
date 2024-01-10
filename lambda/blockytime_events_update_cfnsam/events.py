""" this script imports the export file from BlockyTime app
converts the raw file into two hours reports

1. main categories
2. sub categories

each report has rows of the categories (or subcategories)
and columns for each month in the year

this version is compatible for use in AWS lambda

"""
#-----------------------------------------------------------------------------
#import dependencies
#-----------------------------------------------------------------------------
import sys
from sqlgsheet import database as db
import datetime as dt
import pandas as pd


#-----------------------------------------------------------------------------
#Variables
#-----------------------------------------------------------------------------
TABLES = {
    'events': []
}
SQL_EVENT_TABLENAME = 'event'
DATE_FORMAT = '%Y-%m-%d %H:%M'
CSV_FILENAME = 'events.csv'
REPORTING_YEAR = 2020
REPORTING_MONTH = 12


#-----------------------------------------------------------------------------
#main
#-----------------------------------------------------------------------------
def update(events=None, db_load=True):
    """ this function updates the gsheet report with new blockytime events
    :return: None
    """
    load(db_load=db_load)
    transform_events(events)
    update_db()

    create_report_tables()
    post_to_gsheet()


#-----------------------------------------------------------------------------
#setup
#-----------------------------------------------------------------------------
def load(db_load=True):
    if db_load:
        db.load()
    update_config()


def update_config():
    global REPORTING_YEAR, REPORTING_MONTH
    config = db.get_sheet('hours', 'config')
    parameters = config[config['group'] == 'reporting'][
        ['parameter', 'value']].set_index('parameter')['value']
    REPORTING_YEAR = int(parameters['reporting_year'])
    REPORTING_MONTH = int(parameters['reporting_month'])


#-----------------------------------------------------------------------------
# Database
#-----------------------------------------------------------------------------


def update_db(new_events=None, has_duplicates=True):
    """ this function updates the sqlite database
    and checks for duplicates to add only the unique new events
    """
    global TABLES
    if new_events is None:
        new_events = TABLES['events']

    if len(new_events) > 0:
        if db.table_exists(SQL_EVENT_TABLENAME): #db has existing events
            if has_duplicates:
                #compare and remove duplicates that are already in the db
                not_in_db = remove_db_events(new_events)

                # recursive call no duplicates
                update_db(not_in_db, has_duplicates=False)
            else:
                # only the incremental events
                db.rows_insert(new_events, 'event', con=db.con)

        else: #first update
            has_duplicates = False
            db.update_table(new_events, 'event', append=False)

    if not has_duplicates:
        db_events = db.get_table('event')
        report_year = db_events[db_events.year == REPORTING_YEAR]
        TABLES['events'] = report_year


def remove_db_events(new_events):
    # get the events from the db
    db_events = db.get_table(SQL_EVENT_TABLENAME)

    # add a datetime field to use as the unique field to both tables
    for t in [db_events, new_events]:
        t['start_datetime'] = t['Start'].apply(
            lambda x: dt.datetime.strptime(x, DATE_FORMAT))

    # add only the new events not already in the database
    not_in_db = pd.concat([db_events, db_events, new_events])
    not_in_db.drop_duplicates(
        subset=['start_datetime'],
        keep=False,
        inplace=True
    )
    # drop the temporary datetime field
    del not_in_db['start_datetime']

    return not_in_db


#-----------------------------------------------------------------------------
#subfunctions
#-----------------------------------------------------------------------------
def transform_events(events=None):
    global TABLES
    if events is None:
        events = pd.read_csv(CSV_FILENAME, encoding='iso-8859-1')

    events['start_date'] = events['Start'].apply(
        lambda x: dt.datetime.strptime(x, DATE_FORMAT).date())
    events['day'] = events['start_date'].apply(lambda x: x.day)
    events['month'] = events['start_date'].apply(lambda x: x.month)
    events['year'] = events['start_date'].apply(lambda x: x.year)
    events['start_date'] = events['start_date'].apply(
        lambda x: str(x))

    #convert duration in minutes to hours
    events['duration_hrs'] = events['Duration']/60

    events = events[events['year'] == REPORTING_YEAR].copy()
    events = events[events['month'] <= REPORTING_MONTH].copy()

    #fill blank categories
    events['Event Type'].fillna('', inplace=True)
    events['Event Object'].fillna('', inplace=True)
    events['Comment'].fillna('', inplace=True)
    events['Tag'].fillna(0, inplace=True)

    #trim
    events['Event Type'] = events['Event Type'].apply(lambda x: x.strip())
    events['Event Object'] = events['Event Object'].apply(lambda x: x.strip())

    TABLES['events'] = events


def create_report_tables():
    #01 main category report
    events = TABLES['events']
    main_cat_pvt = pd.pivot_table(events, index='Event Type', columns='month',
                             values='duration_hrs', aggfunc='sum')
    main_cat_pvt.fillna(0, inplace=True)
    #events_pvt = events_pvt/events_pvt.sum()*24
    TABLES['main_category_report'] = main_cat_pvt

    #02 subcategory report
    sub_cat_pvt = pd.pivot_table(events, index=['Event Type', 'Event Object'], columns='month',
                             values='duration_hrs', aggfunc='sum')
    sub_cat_pvt.fillna(0, inplace=True)
    sub_cat_pvt = sub_cat_pvt/sub_cat_pvt.sum()*24
    TABLES['subcategory_report'] = sub_cat_pvt


def post_to_gsheet():
    #01 main category
    main_category_report = TABLES['main_category_report']
    #data fields
    db.post_to_gsheet(main_category_report, 'hours', 'main_category_report',
                      input_option='USER_ENTERED')
    #category field
    db.post_to_gsheet(main_category_report.reset_index()[['Event Type']],
                      'hours', 'main_categories',
                      input_option='USER_ENTERED')

    #02 subcategories
    subcategory_report = TABLES['subcategory_report']
    #data fields
    db.post_to_gsheet(subcategory_report, 'hours', 'subcategory_report',
                      input_option='USER_ENTERED')
    #category field
    db.post_to_gsheet(subcategory_report.reset_index()[['Event Type', 'Event Object']],
                      'hours', 'subcategories',
                      input_option='USER_ENTERED')


def timestamp_rm_seconds(datetime_str):
    has_sec = False
    ts_no_sec = datetime_str
    if ':' in datetime_str:
        dt_split = datetime_str.split(':')
        if len(dt_split) == 3:
            has_sec = True
    if has_sec:
        ts_no_sec = datetime_str[:-3]
    return ts_no_sec


# -----------------------------------------------------
# Command line interface
# -----------------------------------------------------
def autorun():
    if len(sys.argv) > 1:
        process_name = sys.argv[1]
        if process_name == 'pink_floyd':
            print('dont take a slice of my pie')
    else:
        update()


if __name__ == "__main__":
    autorun()
# -----------------------------------------------------
# Reference code
# -----------------------------------------------------

#-----------------------------------------------------------------------------
#main
#-----------------------------------------------------------------------------