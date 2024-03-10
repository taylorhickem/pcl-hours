import os
import json
import pandas as pd
from sqlgsheet import database as db
from sqlgsheet import gdrive as gd
import dynamodb
import boto3
import events as bt

#hello world

S3_BUCKET = ''
EVENT_DATA_KEY = 'events/events.csv'
EVENT_DATA_FILE = '/opt/events.csv'
USER_DATA_DIR = '/opt'
USER_DATA = {
    'gsheet_config': USER_DATA_DIR + '/gsheet_config.json',
    'client_secret': USER_DATA_DIR + '/client_secret.json',
    'db_config': USER_DATA_DIR + '/dynamodb_config.json',
    'mysql_credentials': USER_DATA_DIR + '/mysql_credentials.json'
}
ACTION_TYPE = 'report_update'

s3_client = None


def lambda_handler(event, context):
    global S3_BUCKET, ACTION_TYPE
    status_code = 500
    message = 'failed'

    messages = []
    S3_BUCKET = os.environ['S3_BUCKET']
    if 'ACTION_TYPE' in event:
        ACTION_TYPE = event['ACTION_TYPE']

    print(f'\n ACTION_TYPE {ACTION_TYPE} \n')
    messages.append(f'\n ACTION_TYPE {ACTION_TYPE} \n')
    if ACTION_TYPE == 'events_delete':
        event_delete_date = event['DELETE_DATE']
        messages.append('deleting events ...')
        events_delete(event_delete_date, messages)

    elif ACTION_TYPE == 'report_update':
        report_update()

    status_code = 200
    messages.append('script executed successfully without exception')

    return {
        'status_code': status_code,
        'message': messages
    }


def events_delete(date_str, messages):
    messages.append('loading DynamoDBAPI to sqlgsheet database.py ...')
    db_load()
    messages.append(f'deleting events for date {date_str} ... ')
    delete_date(date_str, messages)


def report_update():
    with open(USER_DATA['db_config'], 'r') as f:
        db_config = json.load(f)
        f.close()

    print('loading events from S3 ...')
    s3_events = events_from_s3()

    print('loading DynamoDBAPI to sqlgsheet database.py ...')
    db_load()
    bt.load(db_load=False)
    print('loading table using sqlgsheet db ... ')
    all_events = bt.db.get_table('event')

    # print('first row:')
    # first_row = all_events.iloc[0].to_dict()
    # print(first_row)
    bt.update(s3_events, db_load=False)

    refresh_event_data()

    print('report updated.')


def events_from_file():
    events = pd.read_csv(EVENT_DATA_FILE)
    return events


def events_from_s3():
    load_s3_client()
    response = s3_client.get_object(
        Bucket=S3_BUCKET,
        Key=EVENT_DATA_KEY
    )
    events = pd.read_csv(response['Body'])
    return events


def load_s3_client():
    global s3_client
    if not s3_client:
        s3_client = boto3.client('s3')


def refresh_event_data():
    load_s3_client()
    s3_client.delete_object(
        Bucket=S3_BUCKET,
        Key=EVENT_DATA_KEY
    )


def db_load():
    bt.db.set_user_data(**USER_DATA)
    bt.db.DB_SOURCE = 'generic'
    bt.db.load(generic_con_class=dynamodb.DynamoDBAPI)


def delete_date(date_str, messages):
    column_name = 'start_date'
    event_table = bt.db.con.tables['event']
    keys, items = event_table.query_by_string_value_eq(column_name, date_str, is_key=False)
    messages.append(f'found {len(keys)} events now deleting ...')
    event_table._items_delete(keys)