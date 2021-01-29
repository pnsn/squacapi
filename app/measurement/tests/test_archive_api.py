from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric, ArchiveDay
from nslc.models import Network, Channel

from rest_framework.test import APIClient
from rest_framework import status

from datetime import datetime
import pytz

from squac.test_mixins import sample_user

'''Tests for all measurement models:
    *

to run only these tests:
    ./mg.sh "test measurement && flake8"
'''


class UnauthenticatedArchiveApiTests(TestCase):
    '''Test the measurement api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all requests
        self.client.force_authenticate(user=None)
        timezone.now()
        metric = Metric.objects.create(
            name='Metric test',
            code='123',
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
        )
        chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code='RCM',
            station_name='Camp Muir',
            loc="--",
            network=net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )
        self.archive = ArchiveDay.objects.create(
            channel=chan,
            metric=metric,
            min=0, max=0, mean=0, median=0, stdev=0, num_samps=1,
            starttime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            endtime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC)
        )

    def test_unauthenticated_archive(self):
        url = reverse(
            'measurement:archive-day-detail',
            kwargs={'pk': self.archive.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_archive_res_and_str(self):
        url = reverse(
            'measurement:archive-day-detail',
            kwargs={'pk': self.archive.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ArchiveApiTests(TestCase):
    '''Test the measurement api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        self.user.is_staff = True
        # unauthenticate all requests
        self.client.force_authenticate(user=self.user)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Metric test',
            code='123',
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code='RCM',
            station_name='Camp Muir',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )
        self.archive = ArchiveDay.objects.create(
            channel=self.chan,
            metric=self.metric,
            min=0, max=0, mean=0, median=0, stdev=0, num_samps=1,
            starttime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            endtime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC)
        )

    def test_get_archive(self):
        url = reverse(
            'measurement:archive-day-list',
        )
        data = {
            "metric": self.metric.id,
            "channel": self.chan.id,
            "starttime":
                str(datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC)),
            "endtime":
                str(datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC))
        }
        res = self.client.get(url, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(reverse(
            'measurement:archive-day-detail',
            kwargs={'pk': self.archive.id}
        ) in res.data[0]["id"])

    def test_get_archive_missing_params(self):
        url = reverse(
            'measurement:archive-day-list',
            kwargs={}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_archive_fail(self):
        url = reverse('measurement:archive-day-list')
        payload = {}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_archive_fail(self):
        url = reverse('measurement:archive-day-list')
        payload = {}
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_archive_fail(self):
        url = reverse('measurement:archive-day-list')
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
