'''load all apps from csv
run in docker-compose like:
docker-compose run --rm app sh -c 'python import/load/load_all.py'
'''
import django
import sys
import os


def main(csv_length=0):
    from load import load_nslc, load_measurement, load_dashboard

    project_path = './'
    sys.path.append(project_path)
    # if not os.environment['DJANGO_SETTINGS_MODULE']:
    #     os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
    django.setup()

    load_nslc.main(csv_length)
    load_measurement.main(csv_length)
    load_dashboard.main()


if __name__ == '__main__':
    csv_length = int(input("Short[0] or long[1] csv files: "))
    main(csv_length)
