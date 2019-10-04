from urllib.request import urlopen
import urllib.error
import xml.etree.ElementTree as etree
import django
import sys
import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model

"""load channels from fdsn webservice
 run in docker-compose like
 docker-compose run --rm app sh -c 'python import/load/load_nslc_fdsn.py'

"""


def main():
    from nslc.models import Network, Channel

    try:
        user = get_user_model().objects.get(email=LOADER_EMAIL)
    except ObjectDoesNotExist:
        print(f"{LOADER_EMAIL} does not exist."
              f"You must provide a valid email by setting the LOADER_EMAIL"
              f"environmental variable.")
        sys.exit(1)
    for row in netReader:
        net = Network.objects.get_or_create(
            code=row[0].lower(),
            user=user,
            defaults={'name': row[1]}
        )

    for row in nslcReader:
        # print(row)
        net = Network.objects.get(code=row[0].lower())
        # sta = Station.objects.get_or_create(
        #     code=row[1].lower(),
        #     network=net,
        #     user=user,
        #     defaults={'name': row[8]}
        # )
        if not row[3]:
            row[3] = "--"
        if not row[7]:
            row[7] = -1
        Channel.objects.get_or_create(
            code=row[2].lower(),
            network=net,
            station_code=row[1].lower(),
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
            description=f"All {n.code.upper()} channels",
            user=user
        )
        n_channels = Channel.objects.filter(network__code=n.code)
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
print(DJANGO_SETTINGS_MODULE)
django.setup()
print("herefadsfjdskfjdkfj")

if __name__ == '__main__':
    main()
