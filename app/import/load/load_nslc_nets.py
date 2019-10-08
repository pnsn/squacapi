"""load networks from csv
 run in docker-compose like
 $:docker-compose run --rm app sh -c 'LOADER_EMAIL=email@pnsn.org  \
                    python import/load/load_nslc_nets.py "."'

"""
import csv
import django
import sys
import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model

project_path = '.'
if len(sys.argv) > 1:
    project_path = sys.argv[1]
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
sys.path.append(project_path)
django.setup()
from nslc.models import Network

LOADER_EMAIL = os.environ.get('LOADER_EMAIL')
if not LOADER_EMAIL:
    print(f"You must provide a valid email by setting the LOADER_EMAIL"
          f" environmental variable."
          )
    sys.exit(1)


def main(csv_path):
    netReader = csv.reader(open(csv_path), delimiter=',', quotechar='"')
    # skip the headers
    next(netReader, None)
    try:
        user = get_user_model().objects.get(email=LOADER_EMAIL)
    except ObjectDoesNotExist:
        print(f"Email {LOADER_EMAIL} not found")
        sys.exit(1)
    # use defaults for attrs not required for the lookup
    for row in netReader:
        print(row)
        Network.objects.get_or_create(
            code=row[0].lower(),
            defaults={'user': user, 'name': row[1]}
        )


csv_path = f"{project_path}/import/csv/networks.csv"
print(csv_path)

if __name__ == '__main__':
    main(csv_path)
