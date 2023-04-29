import json
import pandas as pd
from sqlgsheet import database as db
from sqlgsheet import gdrive as gd
import boto3
import events as bt

S3_BUCKET = 'pcl-hours'
EVENT_DATA_KEY = 'event_data/events.csv'
USER_DATA_DIR = '/opt/user_data'
user_data = {
    'gsheet_config': USER_DATA_DIR + '/gsheet_config.json',
    'client_secret': USER_DATA_DIR + '/client_secret.json',
    'mysql_credentials': USER_DATA_DIR + '/mysql_credentials.json'
}

s3_client = None


def lambda_handler(event, context):
    status_code = 500
    message = 'failed'

    s3_events = events_from_s3()

    bt.db.set_user_data(
        gsheet_config=user_data['gsheet_config'],
        client_secret=user_data['client_secret'],
        mysql_credentials=user_data['mysql_credentials']
    )
    bt.db.DB_SOURCE = 'remote'
    bt.load()

    bt.update(s3_events)

    refresh_event_data()

    status_code = 200
    message = 'report updated!'

    return {
        'status_code': status_code,
        'message': message
    }


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