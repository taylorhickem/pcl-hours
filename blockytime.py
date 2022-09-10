""" this script imports the export file from BlockyTime app
converts the raw file into two hours reports

1. main categories
2. sub categories

each report has rows of the categories (or subcategories)
and columns for each month in the year

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
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
CSV_FILENAME = 'events.csv'
REPORING_YEAR = 2020
REPORING_MONTH = 12


#-----------------------------------------------------------------------------
#main
#-----------------------------------------------------------------------------
def update():
    load()
    transform_events()
    create_report_tables()
    post_to_gsheet()
    print('report updated!')


#-----------------------------------------------------------------------------
#setup
#-----------------------------------------------------------------------------
def load():
    db.load()
    update_config()


def update_config():
    global REPORING_YEAR, REPORING_MONTH
    config = db.get_sheet('hours', 'config')
    parameters = config[config['group'] == 'reporting'][
        ['parameter', 'value']].set_index('parameter')['value']
    REPORING_YEAR = int(parameters['reporting_year'])
    REPORING_MONTH = int(parameters['reporting_month'])


#-----------------------------------------------------------------------------
#subfunctions
#-----------------------------------------------------------------------------
def transform_events():
    global TABLES
    events = pd.read_csv(CSV_FILENAME, encoding='iso-8859-1')
    subfields = ['Start',
                 'Duration',
                 'Event Type',
                 'Event Object',
                 'Comment']
    events['start_date'] = events['Start'].apply(
        lambda x: dt.datetime.strptime(x, DATE_FORMAT).date())
    events['day'] = events['start_date'].apply(lambda x: x.day)
    events['month'] = events['start_date'].apply(lambda x: x.month)
    events['year'] = events['start_date'].apply(lambda x: x.year)

    #convert duration in minutes to hours
    events['duration_hrs'] = events['Duration']/60

    events = events[events['year'] == REPORING_YEAR].copy()
    events = events[events['month'] <= REPORING_MONTH].copy()

    #fill blank categories
    events['Event Type'].fillna('', inplace=True)
    events['Event Object'].fillna('', inplace=True)

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
