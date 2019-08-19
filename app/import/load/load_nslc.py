"""load station and networks from csv
 run in docker-compose like
 docker-compose run --rm app sh -c 'python import/load/load_nslc.py'
 use default arg with get_or_create to select on unique together keys
 deault keys are ignored on get, but used in create/save. Without using default
 on non unique columns IntegrityError might be thown
"""
# SQL
import csv
import django
import sys
import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model


def main(csv_length=0):
    from nslc.models import Network, Station, Channel, Group

    csv_path = project_path + "/import/csv/"

    # For quick test uncomment next line and comment out following line
    if csv_length == 0:
        nslc_path = csv_path + "nslc_short.csv"
    else:
        nslc_path = csv_path + "nslc.csv"
    networks_path = csv_path + "networks.csv"

    nslcReader = csv.reader(open(nslc_path), delimiter=',', quotechar='"')
    netReader = csv.reader(open(networks_path), delimiter=',', quotechar='"')
    # skip the headers
    next(nslcReader, None)
    next(netReader, None)

    Network.objects.all().delete()
    Station.objects.all().delete()
    Channel.objects.all().delete()
    Group.objects.all().delete()
    try:
        user = get_user_model().objects.get(email='loader@pnsn.org')
    except ObjectDoesNotExist:
        user = get_user_model().objects.create_user('loader@pnsn.org',
                                                    'secret')
    for row in netReader:
        net = Network.objects.get_or_create(
            code=row[0].lower(),
            user=user,
            defaults={'name': row[1]}
        )

    for row in nslcReader:
        # print(row)
        net = Network.objects.get(code=row[0].lower())
        sta = Station.objects.get_or_create(
            code=row[1].lower(),
            network=net,
            user=user,
            defaults={'name': row[8]}
        )
        if not row[3]:
            row[3] = "--"
        if not row[7]:
            row[7] = -1
        Channel.objects.get_or_create(
            code=row[2].lower(),
            station=sta[0],
            user=user,
            defaults={
                'name': row[2],
                'sample_rate': float(row[7]),
                'loc': row[3].lower(),
                'lat': float(row[4]),
                'lon': float(row[5]),
                'elev': float(row[6])
            }
        )

    # Create groups to be linked to a channel group
    networks = Network.objects.all()
    for n in networks:
        group = Group.objects.create(
            name=f"{n.code.upper()}-All",
            description=f"All {n.code.upper()} stations",
            user=user
        )
        n_channels = Channel.objects.filter(station__network__code=n.code)
        for c in n_channels:
            group.channels.add(c)


# app is root directory where project lives
# /app/squac....
# or on production "./"
project_path = './'
sys.path.append(project_path)
# production 'config.settings.production'
# if not os.environ['DJANGO_SETTINGS_MODULE']:
#    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
django.setup()

if __name__ == '__main__':
    main()
