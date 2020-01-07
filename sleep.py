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
EMPTY = ['', '', '', '', '', '', '', '']


def get_sleep_data(date):
    url = f"{BASE_URL}/1.2/user/{USER_NAME}/sleep/date/{date}.json?date{date}=&id={USER_NAME}"
    r = requests.get(url, headers=HEADER)
    content = json.loads(r.content)

    if len(content['sleep']) != 1:
        print(f"skipping {date}, wrong content length")
        return EMPTY

    sleep_data = content['sleep'][0]
    sleep_summary = content['summary']

    minutes_asleep = sleep_data['minutesAsleep']
    minutes_in_bed = sleep_data['minutesAwake'] + minutes_asleep

    sleep_ratio = round(minutes_asleep / minutes_in_bed, 2)
    if 'stages' not in sleep_summary:
        print(f"skipping {date}, stages not in summary")
        return EMPTY

    minutes_deep = sleep_summary['stages']['deep']
    minutes_rem = sleep_summary['stages']['rem']
    minutes_light = sleep_summary['stages']['light']
    minutes_wake = sleep_summary['stages']['wake']

    level_data = sleep_data['levels']['data']

    if 'levels' not in sleep_data or 'data' not in sleep_data['levels']:
        print(f"skipping {date}, levels data not provided")
        return EMPTY

    sleep_time = datetime.strptime(level_data[0]['dateTime'], FB_FORMAT).strftime(READ_FORMAT)
    wake_time = datetime.strptime(level_data[-1]['dateTime'], FB_FORMAT).strftime(READ_FORMAT)

    return [sleep_time, wake_time, sleep_ratio, minutes_asleep, minutes_deep, minutes_rem, minutes_light, minutes_wake]


if __name__ == "__main__":

    with open('sleep_data.csv', mode='w') as sleep_data:
        writer = csv.writer(sleep_data, delimiter=',', quotechar='"',
                                     quoting=csv.QUOTE_MINIMAL)

        date = datetime(2019, 11, 1)
        three_days_ago = datetime.utcnow() - timedelta(days=3)

        writer.writerow(
            ['sleep', 'wake', 'ratio', 'minutes_asleep', 'minutes_deep', 'miniutes_rem', 'minutes_light', 'minutes_wake']
        )

        while date < three_days_ago:
            date += timedelta(days=1)
            writer.writerow(get_sleep_data(date.strftime(SHORT_FORMAT)))
