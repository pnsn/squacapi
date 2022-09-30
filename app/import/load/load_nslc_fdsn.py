"""load channel data from fdsn
 run in docker-compose:
 $:docker-compose run --rm app sh -c 'LOADER_EMAIL=email@pnsn.org  \
                    python import/load/load_nslc_fdsn.py --path="." \
                    --networks="UW,CC,UO" --endtime="YYYY-mm-dd"'

"""
import csv
import requests
import sys
import os
import django
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from datetime import datetime
import pytz
import argparse

LOADER_EMAIL = os.environ.get('LOADER_EMAIL')
if not LOADER_EMAIL:
    print("You must provide a valid email by setting the LOADER_EMAIL"
          "environmental variable."
          )
    sys.exit(1)


"""load channels from fdsn webservice
 run in docker-compose like
$:docker-compose run --rm app sh -c 'LOADER_EMAIL=email@pnsn.org  \
                    python import/load/load_nslc_fdsn.py "."
                     --networks='UW,CC,UO'
                     --endtime=[YYYY-mm-dd]



 geocsv object from fdsn has following schema:

 Network | Station | Location | Channel | Latitude | Longitude |
 Elevation | Depth | Azimuth | Dip | SensorDescription | Scale |
 ScaleFreq | ScaleUnits | SampleRate | StartTime | EndTime

"""


def build_url(nets, level, endtime):
    '''create url based on params

        documentation at https://service.iris.edu/fdsnws/station/1/
    '''
    url = (
        f'''https://service.iris.edu/fdsnws/station/1/query?'''
        f'''network={nets}'''
        f'''&level={level}'''
        f'''&format=geocsv'''
        f'''&endafter={endtime}'''
    )
    return url


def parse_datetime(datetime_str):
    '''parse datetime from string of form

        # 2599-12-31T23:59:59
        return datetime
    '''
    year, month, day_time = datetime_str.split("-")
    day, time = day_time.split("T")
    hour, minute, sec = time.split(":")
    return datetime(int(year), int(month), int(day), int(hour),
                    int(minute), int(sec[:2]), tzinfo=pytz.UTC)


def main():
    parser = argparse.ArgumentParser(
        description="Query FDSN to populate squacapi nslc_channel data",
        usage="""LOADER_EMAIL=email@pnsn.org
            python import/load/load_nslc_fdsn.py path
            --networks=CC,UW,UO
            --endtime=[YYYY-mm-dd]"""
    )
    parser.add_argument('--path', default='.',
                        help="path to app root dir")
    parser.add_argument('--networks', required=True,
                        help="Comma seperated list of networks")
    parser.add_argument('--endtime',
                        help="filter for channels with offdates greater than\
                             datetime if missing, defaults to datetime.now()")
    args = parser.parse_args()

    project_path = args.path
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
    sys.path.append(project_path)
    django.setup()
    from nslc.models import Network, Channel
    try:
        user = get_user_model().objects.get(email=LOADER_EMAIL)
    except ObjectDoesNotExist:
        print(f'''{LOADER_EMAIL} does not exist.
            You must provide a valid email by setting the LOADER_EMAIL
            environmental variable.
            ''')
        sys.exit(1)

    # create hash for lookup
    networks = {}
    for n in Network.objects.all():
        networks[n.code.lower()] = n
    # download geocsv, which is pipe deliminated

    endtime = args.endtime
    if not endtime:
        endtime = datetime.now()
        endtime = endtime.strftime("%Y-%m-%d")
    print(endtime)
    station_url = build_url(args.networks, 'station', endtime)
    # create a station hash so we can pull out station description

    stations = {}
    with requests.Session() as s:
        download = s.get(station_url)
        decoded_content = download.content.decode('utf-8')
        content = csv.reader(decoded_content.splitlines(), delimiter='|')
        row_list = list(content)
        # skip first two rows of metadata
        for row in row_list[2:]:
            stations[row[1].lower()] = row[5]
    channel_url = build_url(args.networks, 'channel', endtime)
    with requests.Session() as s:
        download = s.get(channel_url)
        decoded_content = download.content.decode('utf-8')
        content = csv.reader(decoded_content.splitlines(), delimiter='|')
        row_list = list(content)
        # skip first two rows of metadata
        for row in row_list[5:]:
            net = networks[row[0].lower()]
            Channel.objects.get_or_create(
                network=net,
                station=row[1].lower(),
                location='--' if not row[2] else row[2].lower(),
                code=row[3].lower(),
                defaults={
                    'latitude': float(row[4]),
                    'longitude': float(row[5]),
                    'elevation': float(row[6]),
                    'depth': float(row[7]),
                    'name': stations[row[1].lower()],
                    'azimuth': 0.0 if not row[8] else float(row[8]),
                    'dip': 0.0 if not row[9] else float(row[9]),
                    'sensor_description': row[10],
                    'scale': 0.0 if not row[11] else float(row[11]),
                    'scale_freq': 0.0 if not row[12] else float(row[12]),
                    'scale_units': row[13],
                    'sample_rate': 0.0 if not row[14] else float(row[14]),
                    'starttime': parse_datetime(row[15]),
                    'endtime': parse_datetime(row[16]),
                    'user': user,
                }
            )


if __name__ == '__main__':
    main()
