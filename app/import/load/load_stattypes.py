"""one off to load stats
 run in docker-compose like
 $:docker-compose run --rm app sh -c 'LOADER_EMAIL=email@pnsn.org  \
                    python import/load/load_stattypes.py "."'

"""
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
from dashboard.models import StatType

LOADER_EMAIL = os.environ.get('LOADER_EMAIL')
if not LOADER_EMAIL:
    print(f"You must provide a valid email by setting the LOADER_EMAIL"
          f" environmental variable."
          )
    sys.exit(1)


def main():
    try:
        user = get_user_model().objects.get(email=LOADER_EMAIL)
    except ObjectDoesNotExist:
        print(f"Email {LOADER_EMAIL} not found")
        sys.exit(1)
    stats = [['Average', 'ave'],
             ['Median', 'med'],
             ['Minimum', 'min'],
             ['Maximum', 'max'],
             ['Sample Count', 'num_samp'],
             ['99th percentile', 'p99'],
             ['95th percentile', 'p95'],
             ['90th percentile', 'p90'],
             ['50th percentile', 'p50'],
             ['10th percentile', 'p10']]
    # use defaults for attrs not required for the lookup
    for s in stats:
        StatType.objects.get_or_create(
            name=s[0],
            type=s[1],
            defaults={'user': user}
        )


if __name__ == '__main__':
    main()
