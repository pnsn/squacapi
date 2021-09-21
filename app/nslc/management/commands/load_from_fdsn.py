"""
Command run without any options will give default URL
    http://service.iris.edu/irisws/fedcatalog/1/
        query?datacenter=IRISDMC,NCEDC,SCEDC
        &targetservice=station
        &level=channel
        &net=AK,AV,AZ,BC,BK,CC,CE,CI,CN,ET,HV,IU,IW,MB,NC,NN,NP,NV,OK,OO,PB,PR,SN,TX,UM,UO,US,UU,UW
        &sta=*
        &cha=EN?,HN?,?H?
        &loc=*
        &minlat=12.
        &maxlat=72.
        &minlon=-183.
        &maxlon=-62.
        &starttime=2019-01-01
        &format=text

load channels from fdsn webservice run in docker-compose like:
$:docker-compose run --rm app sh -c "LOADER_EMAIL=email@pnsn.org \
                    python manage.py load_from_fdsn
                    [optional args]
                    --path='.'
                    --datacenter='IRISDMC,...'
                    --sta='BEER,...'
                    --cha='HN?,ENN,...'
                    --loc=*
                    --minlat=12.
                    --maxlat=72.
                    --minlon=-183.
                    --maxlon=-62.
                    --starttime='YYYY-mm-dd'"

 text response from fdsn has following schema:
 Network | Station | Location | Channel | Latitude | Longitude |
 Elevation | Depth | Azimuth | Dip | SensorDescription | Scale |
 ScaleFreq | ScaleUnits | SampleRate | StartTime | EndTime
"""
import csv
import requests
import sys
import os
from datetime import datetime
import pytz
import django
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from nslc.models import Network, Channel


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default='.',
            help="path to app root dir"
        )
        parser.add_argument(
            '--datacenter',
            default="IRISDMC,NCEDC,SCEDC",
            help="Comma separated list of datacenters"
        )
        parser.add_argument(
            '--sta',
            default="*",
            help="Comma separated regex for stations, * default"
        )
        parser.add_argument(
            '--cha',
            default="EN?,HN?,?H?",
            help="Comma separated regex for channel code, ? wildcard, \
                EN?,HN?,?H? default"
        )
        parser.add_argument(
            '--loc',
            default="*",
            help="Comma separated regex for locations, * default"
        )
        parser.add_argument(
            '--minlat',
            default=12,
            help="Lower latitude for search box, 12 default"
        )
        parser.add_argument(
            '--maxlat',
            default=72,
            help="Upper latitude for search box, 72 default"
        )
        parser.add_argument(
            '--minlon',
            default=-183.,
            help="Left latitude for search box, -183. default"
        )
        parser.add_argument(
            '--maxlon',
            default=-113,
            help="Right latitude for search box, -62 default"
        )
        parser.add_argument(
            '--starttime',
            default="2019-01-01",
            help="filter for channels with metadata listed on or after the \
                specified time"
        )

    def build_url(self, params, level):
        ''' create url based on params
            documentation at https://service.iris.edu/irisws/fedcatalog/1/
        '''
        url = (
            f"http://service.iris.edu/irisws/fedcatalog/1/query?"
            f"datacenter={params['datacenter']}"
            f"&targetservice=station"
            f"&level={level}"
            f"&net={params['net']}"
            f"&starttime={params['starttime']}"
            "&format=text"
        )
        if (level != "network"):
            url += (
                f"&sta={params['sta']}"
                f"&cha={params['cha']}"
                f"&loc={params['loc']}"
                f"&minlat={params['minlat']}"
                f"&maxlat={params['maxlat']}"
                f"&minlon={params['minlon']}"
                f"&maxlon={params['maxlon']}"
            )
        return url

    '''Django command to check network and channel tables with FDSN service'''
    def handle(self, *args, **options):
        ALLOWED_NETWORKS = [
            "AK", "AV", "AZ", "BC", "BK", "CC", "CE", "CI", "CN", "ET", "HV",
            "IU", "IW", "MB", "NC", "NN", "NP", "NV", "OK", "OO", "PB", "PR",
            "SN", "TX", "UM", "UO", "US", "UU", "UW"
        ]
        options["net"] = ','.join(ALLOWED_NETWORKS)
        LOADER_EMAIL = os.environ.get('LOADER_EMAIL')
        if not LOADER_EMAIL:
            print(
                "You must provide a valid email by setting the LOADER_EMAIL "
                "environmental variable."
            )
            sys.exit(1)
        project_path = options['path']
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
        sys.path.append(project_path)
        django.setup()
        try:
            user = get_user_model().objects.get(email=LOADER_EMAIL)
        except ObjectDoesNotExist:
            print(
                f"Loader email {LOADER_EMAIL} does not exist.\n"
                "You must provide a valid email by setting the LOADER_EMAIL "
                "environmental variable."
            )
            sys.exit(1)

        network_url = self.build_url(options, "network")
        with requests.Session() as s:
            download = s.get(network_url)
            decoded_content = download.content.decode('utf-8')
            content = csv.reader(decoded_content.splitlines(), delimiter='|')
            row_list = list(content)
            # skip header rows in metadata
            for row in row_list[1:]:
                # extract data from row
                if len(row) > 1:
                    net_code = row[0]
                    net_name = row[1]

                    # Get or create the channel using data
                    Network.objects.get_or_create(
                        code=net_code.lower(),
                        defaults={
                            'name': net_name,
                            'user': user
                        }
                    )

        station_url = self.build_url(options, 'station')
        stations = {}
        with requests.Session() as s:
            download = s.get(station_url)
            decoded_content = download.content.decode('utf-8')
            content = csv.reader(decoded_content.splitlines(), delimiter='|')
            row_list = list(content)
            # skip header rows of metadata
            for row in row_list[1:]:
                if len(row) > 1:
                    sta_code = row[1].lower()
                    sta_name = row[5]
                    stations[sta_code] = sta_name

        channel_url = self.build_url(options, 'channel')
        channels = {}
        with requests.Session() as s:
            download = s.get(channel_url)
            decoded_content = download.content.decode('utf-8')
            content = csv.reader(
                decoded_content.splitlines(), delimiter='|')
            row_list = list(content)
            # skip header rows in metadata
            for row in row_list[1:]:
                # extract data from row
                if len(row) > 1:
                    net, sta, loc, cha, lat, lon, elev, *rem = row
                    depth, azimuth, dip, sensor_descr, scale, *rem = rem
                    freq, units, rate, start, end = rem
                    nslc_code = f'{net}.{sta}.{loc}.{cha}'.lower()
                    start_datetime = pytz.utc.localize(
                        datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
                    )
                    if end:
                        end_datetime = pytz.utc.localize(
                            datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
                        )
                    else:
                        # If end time is null set to 2599 dummy date
                        end_datetime = datetime(
                            year=2599, month=12, day=31, tzinfo=pytz.UTC)

                    if nslc_code in channels:
                        if start_datetime < channels[nslc_code]['start']:
                            channels[nslc_code]['start'] = start_datetime
                        if end_datetime > channels[nslc_code]['end']:
                            channels[nslc_code]['end'] = end_datetime
                    else:
                        channels[nslc_code] = {'start': start_datetime,
                                               'end': end_datetime}
                    try:
                        # Update or create the channel using data
                        Channel.objects.update_or_create(
                            network=Network.objects.get(code=net.lower()),
                            station_code=sta.lower(),
                            loc='--' if not loc else loc.lower(),
                            code=cha.lower(),
                            defaults={
                                'lat': float(lat),
                                'lon': float(lon),
                                'elev': float(elev),
                                'depth': float(depth),
                                'name': stations[sta.lower()],
                                'azimuth': 0.0 if not azimuth else float(
                                    azimuth),
                                'dip': 0.0 if not dip else float(dip),
                                'sensor_description': sensor_descr,
                                'scale': 0.0 if not scale else float(scale),
                                'scale_freq': 0.0 if not freq else float(freq),
                                'scale_units': units,
                                'sample_rate': 0.0 if not rate else float(
                                    rate),
                                'starttime': channels[nslc_code]['start'],
                                'endtime': channels[nslc_code]['end'],
                                'user': user,
                            }
                        )
                    except KeyError as e:
                        print(f'Key error occured: {e}')
