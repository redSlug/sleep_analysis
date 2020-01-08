import csv
from datetime import datetime, timedelta
import json
import requests
import os

USER_NAME = os.environ['USER_NAME']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
BASE_URL = 'https://web-api.fitbit.com'
HEADER = {'Authorization': f"Bearer {ACCESS_TOKEN}"}
FB_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
READ_FORMAT = "%Y-%m-%d %H:%M"
SHORT_FORMAT = "%Y-%m-%d"


def _get_date_time(data):
    return datetime.strptime(data['dateTime'], FB_FORMAT)


def _awake_before(data, time):
    return data['level'] == 'wake' and _get_date_time(data) < time


def awake_minutes_minus(level_data, hours=1):
    wake_time = _get_date_time(level_data[-1])
    last_hour_start = wake_time - timedelta(hours=hours)
    seconds_awake = [l['seconds'] for l in level_data if _awake_before(l, last_hour_start)]
    return round(sum(seconds_awake) / 60)


def process_sleep(data):
    sleep = data.get('sleep')
    summary = data.get('summary')

    if len(sleep) != 1 or 'stages' not in summary:
        return None

    sleep = sleep[0]
    stages = summary['stages']

    minutes_deep = stages['deep']
    minutes_rem = stages['rem']
    minutes_light = stages['light']
    minutes_wake = stages['wake']

    if not(minutes_deep or minutes_rem or minutes_light or minutes_wake):
        return None

    minutes_asleep = sleep['minutesAsleep']
    minutes_in_bed = sleep['minutesAwake'] + minutes_asleep
    sleep_ratio = round(minutes_asleep / minutes_in_bed, 2)

    level_data = sleep['levels']['data']

    minutes_awake_1 = awake_minutes_minus(level_data, hours=1)
    minutes_awake_2 = awake_minutes_minus(level_data, hours=2)

    sleep_time = datetime.strptime(level_data[0]['dateTime'], FB_FORMAT).strftime(READ_FORMAT)
    wake_time = datetime.strptime(level_data[-1]['dateTime'], FB_FORMAT).strftime(READ_FORMAT)
    efficiency = sleep['efficiency']

    return [sleep_time, wake_time, sleep_ratio, minutes_asleep, minutes_deep, minutes_rem, minutes_light, minutes_wake, efficiency, minutes_awake_1, minutes_awake_2]


def get_header():
    return ["sleep_time", "wake_time", "sleep_ratio", "minutes_asleep", "minutes_deep", "minutes_rem", "minutes_light", "minutes_wake", "efficiency", "minutes_awake_1", "minutes_awake_2"]


def get_api_data(date):
    url = f"{BASE_URL}/1.2/user/{USER_NAME}/sleep/date/{date}.json?date{date}=&id={USER_NAME}"
    r = requests.get(url, headers=HEADER)
    return json.loads(r.content)


def write_sleep_data():
    date = datetime(2019, 11, 1)
    yesterday = datetime.utcnow() - timedelta(days=1)
    lines = list()
    while date < yesterday:
        sleep_data = get_api_data(date.strftime(SHORT_FORMAT))
        lines.append(sleep_data)
        date += timedelta(days=1)
    with open('sleep.json', mode='w') as sleep_file:
        sleep_file.write(json.dumps(lines))
    return True


def read_sleep_data():
    with open('sleep.json', mode='r') as sleep_file:
        sleep_json = sleep_file.readline()
        return json.loads(sleep_json)


def write_sleep_csv(data):
    with open('sleep.csv', mode='w') as sleep_data:
        writer = csv.writer(sleep_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(get_header())

        for item in data:
            result = process_sleep(item)
            if result:
                writer.writerow(result)


if __name__ == "__main__":
    # write_sleep_data()
    data = read_sleep_data()
    write_sleep_csv(data)
