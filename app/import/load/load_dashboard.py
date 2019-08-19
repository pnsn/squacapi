'''load dashboards from csv
run in docker-compose like:
docker-compose run --rm app sh -c 'python import/load/load_dashboard.py'
nslc and measurement must be loaded first.
'''

import django
import sys
import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model


def main():
    from dashboard.models import Dashboard, Widget, WidgetType
    from nslc.models import Group
    from measurement.models import Metric

    Dashboard.objects.all().delete()
    WidgetType.objects.all().delete()
    Widget.objects.all().delete()

    try:
        user = get_user_model().objects.get(email='loader@pnsn.org')
    except ObjectDoesNotExist:
        user = get_user_model().objects.create_user(
            'loader@pnsn.org',
            'secret'
        )

    groups = Group.objects.all()
    for g in groups:
        Dashboard.objects.create(
            name=f"Test {g.name} dashboard",
            group=g,
            user=user
        )

    widgettypes = []
    widgettypes.append(WidgetType.objects.create(type='Tabular', user=user))
    widgettypes.append(WidgetType.objects.create(type='Map', user=user))

    dashboards = Dashboard.objects.all()

    for d in dashboards:
        tab_widget = Widget.objects.create(
            name=f"{d.name} tab widget",
            dashboard=d,
            widgettype=widgettypes[0],
            user=user
        )
        map_widget = Widget.objects.create(
            name=f"{d.name} map widget",
            dashboard=d,
            widgettype=widgettypes[1],
            user=user
        )
        tab_metrics = Metric.objects.all()
        map_metrics = Metric.objects.filter(name='rawmean')
        for m in tab_metrics:
            tab_widget.metrics.add(m)
        for m in map_metrics:
            map_widget.metrics.add(m)


project_path = './'
sys.path.append(project_path)
# if not os.environment['DJANGO_SETTINGS_MODULE']:
#     os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
django.setup()

if __name__ == '__main__':
    main()
