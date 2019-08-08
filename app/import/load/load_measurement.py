'''load station and networks from csv
 run in docker-compose like:
    docker-compose run --rm app sh -c 'python import/load/load_measurement.py'
 use default arg with get_or_create to select on unique together keys
 deault keys are ignored on get, but used in create/save. Without using default
 on non unique columns IntegrityError might be thown
INPUT CSV:
 measurements:
    metric_name,metric_description,metric_unit,ds_name,ds_description,net,sta,\
    loc,chan,value,starttime,endtime,lat,lon,elev

    "snr10_0p01cm","Number of spikes with SNR > 10 and amplitude exceeding\
    0.01 cm/s^2 using filterd acceleration data.

    ","integer","IRIS","IRIS DMC","BK","YBH  ","00","BHE","1","2018-02-01\
    00:00:00","2018-02-01 01:00:00","41.73204","-122.710388","1059.7"

    "snr20_0p05cm","Number of spikes with SNR > 20 and amplitude exceeding\
    0.05 cm/s^2 using filterd acceleration data.

    ","integer","IRIS","IRIS DMC","BK","YBH  ","00","BHE","0","2018-02-01\
    00:00:00","2018-02-01 01:00:00","41.73204","-122.710388","1059.7"
 ....
 datasource
    id,name,description
    "1","IRIS","IRIS DMC"
    "2","NCEDC","NCEDC"
    "3","SCEDC","SCEDC"
 metric:
    id,metric,unit,description,created_at,updated_at
    "77","pctavailable","percent","Percentage of data returned of data\
    requested.
    ","2018-01-03 15:19:10","2018-01-03 15:19:10"
    "78","ngaps","integer","Number of gaps.
    ","2018-01-03 15:19:10","2018-01-03 15:19:10"
'''

# SQL
import csv
import django
import sys
import os
from django.utils import timezone, dateparse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model


def main():
    from nslc.models import Channel
    from measurement.models import DataSource, Metric, MetricGroup, Group,\
        Threshold, Alarm, Trigger, Measurement

    csv_path = project_path + "/import/csv/"

    # For quick test uncomment next line and comment out following line
    # measurements_csv = csv_path + "measurement_short.csv"
    measurements_csv = csv_path + "measurement_all.csv"
    metricgroup_csv = csv_path + "measurement_group.csv"
    # spectacle_csv = csv_path + "measurement_spectacle.csv"

    measurementReader = csv.reader(
        open(measurements_csv), delimiter=',', quotechar='"'
    )
    # spectacleReader = csv.reader(open(spectacle_csv), delimiter=',',\
    # quotechar='"')
    metricgroupReader = csv.reader(
        open(metricgroup_csv), delimiter=',', quotechar='"'
    )
    # skip the headers
    Metric.objects.all().delete()
    MetricGroup.objects.all().delete()
    Group.objects.all().delete()
    Measurement.objects.all().delete()
    DataSource.objects.all().delete()
    Threshold.objects.all().delete()
    Alarm.objects.all().delete()
    Trigger.objects.all().delete()
    # Spectacle.objects.all().delete()
    try:
        user = get_user_model().objects.get(email='loader@pnsn.org')
    except ObjectDoesNotExist:
        user = get_user_model().objects.create_user(
            'loader@pnsn.org',
            'secret'
        )

    """
        attr, index
        metric_name, 0
        metric_description,1
        metric_unit, 2
        ds_name, 3
        ds_description,4
        net,5
        sta,6
        loc,7
        chan,8
        value,9
        starttime,10
        endtime,11
        lat,12
        lon,13
        elev,14
        metric_name,metric_description,metric_unit,ds_name,ds_description,net,\
        sta,loc,chan,value,starttime,endtime,lat,lon,elev
    """
    # skip header
    next(measurementReader, None)
    for row in measurementReader:
        ds = DataSource.objects.get_or_create(
            name=row[3],
            description=row[4],
            user=user
        )
        metric = Metric.objects.get_or_create(
            name=row[0],
            description=row[1],
            unit=row[2],
            datasource=ds[0],
            user=user
        )

        try:
            # chan=Channel.objects.filter(code=row[8].lower(),\
            # location__code=row[7].lower())
            chan = Channel.objects.get(
                code=row[8].strip().lower(),
                location__code=row[7].strip().lower(),
                location__station__code=row[6].strip().lower(),
                location__station__network__code=row[5].strip().lower(),
                user=user
            )
            Measurement.objects.create(
                metric=metric[0],
                channel=chan,
                value=row[9],
                starttime=timezone.make_aware(
                    dateparse.parse_datetime(row[10])
                ),
                endtime=timezone.make_aware(dateparse.parse_datetime(row[11])),
                user=user
            )
        except Channel.DoesNotExist:
            print("404 code:{} location:{} station:{} network:{}".format(
                row[8].lower(),
                row[7].lower(),
                row[6].lower(),
                row[5].lower()
            ))

    next(metricgroupReader, None)
    for row in metricgroupReader:
        try:
            group = Group.objects.get(name=row[0].strip())
        except Group.DoesNotExist:
            Group.objects.create(name=row[0].strip(), user=user)
            group = Group.objects.get(name=row[0].strip())
        try:
            metric = Metric.objects.get(name=row[1].strip())
            MetricGroup.objects.create(group=group, metric=metric, user=user)
        except Metric.DoesNotExist:
            print("Metric {} 404".format(row[1]))

    '''next(spectacleReader, None)
    for row in spectacleReader:
        sp=Spectacle(name=row[0], user_id=1)
        print(ChannelGroup.objects.all())
        print(MetricGroup.objects.all())
        try:
            channelgroup=ChannelGroup.objects.get(name=row[1])
            metricgroup=MetricGroup.objects.get(name=row[2])

        except (ChannelGroup.DoesNotExist):
            print("MetricGroup or Channel Group Fail: {}, {}".format(
                row[1],
                row[2]
            ))
        else:
            sp.channelgroup=channelgroup
            sp.metricgroup=metricgroup
            sp.save()'''


project_path = './'
sys.path.append(project_path)
# if not os.environment['DJANGO_SETTINGS_MODULE']:
#     os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
django.setup()

if __name__ == '__main__':
    main()
