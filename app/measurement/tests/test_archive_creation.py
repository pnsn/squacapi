from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import pytz

from hypothesis import given
from hypothesis.strategies import lists
from hypothesis.extra.django import TestCase, from_model

from measurement.models import Metric, Measurement
from nslc.models import Network, Channel


class TestArchiveCreation(TestCase):
    """ Tests archive creation functionality """

    def sample_user(email='test@pnsn.org', password="secret"):
        '''create a sample user for testing'''
        return get_user_model().objects.create_user(email, password)

    def setupClass(self):
        timezone.now()
        self.user = self.sample_user()
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

    @given(lists(from_model(Measurement, metric=from_model(Metric))))
    def test_single_day_archive(self):
        pass
