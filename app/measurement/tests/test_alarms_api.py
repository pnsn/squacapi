from unittest.mock import patch
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from measurement.models import (Monitor, Trigger, Alert, Measurement,
                                Metric)
from nslc.models import Channel, Group, Network
from organization.models import Organization

from rest_framework.test import APIClient
from rest_framework import status

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
from squac.test_mixins import sample_user


'''Tests for alarms models:
to run only measurement tests:
    ./mg.sh "test measurement && flake8"
to run only this file
    ./mg.sh "test measurement.tests.test_alarms_api && flake8"

'''


class PrivateAlarmAPITests(TestCase):
    '''For authenticated tests in alarms API

        Authenticate and make user admin so we are only testing
        routes and methods
    '''
    # More data to test filtering for alarm calculations
    fixtures = ['alarms.json']

    def getTestChannel(self, station_code):
        return Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code=station_code,
            station_name='Test Name',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )

    def getTestMonitor(self, interval_type=Monitor.IntervalType.MINUTE,
                       interval_count=2):
        return Monitor.objects.create(
            name="Test Monitor",
            channel_group=self.grp,
            metric=self.metric,
            interval_type=interval_type,
            interval_count=interval_count,
            stat=Monitor.Stat.SUM,
            user=self.user
        )

    def getTestMeasurement(self, metric, channel, val, delta):
        basetime = datetime(2019, 5, 5, 8, 8, 7, 0, tzinfo=pytz.UTC)
        return Measurement.objects.create(
            metric=metric,
            channel=channel,
            value=val,
            starttime=basetime + delta,
            endtime=basetime + delta,
            user=self.user
        )

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.user.is_staff = True
        self.client.force_authenticate(self.user)
        timezone.now()
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.chan1 = self.getTestChannel('CH1')
        self.chan2 = self.getTestChannel('CH2')
        # self.chan3 = self.getTestChannel('CH3')
        self.grp = Group.objects.create(
            name='Test group',
            user=self.user,
            organization=self.organization,
        )
        self.grp.channels.set([self.chan1.id, self.chan2.id])
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            code="someotherthing",
            default_minval=1,
            default_maxval=10.0,
            user=self.user,
            reference_url='pnsn.org'
        )
        self.monitor = Monitor.objects.create(
            name="Self Monitor",
            channel_group=self.grp,
            metric=self.metric,
            interval_type=Monitor.IntervalType.DAY,
            interval_count=1,
            stat=Monitor.Stat.SUM,
            user=self.user
        )
        self.trigger = Trigger.objects.create(
            monitor=self.monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[self.user.email]
        )
        self.alert = Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            in_alarm=True,
            user=self.user
        )

    def test_get_alert(self):
        url = reverse(
            'measurement:alert-detail',
            kwargs={'pk': self.alert.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['trigger'], self.trigger.id)

    def test_create_alert(self):
        url = reverse('measurement:alert-list')
        payload = {
            'trigger': self.trigger.id,
            'timestamp': datetime(1999, 12, 31, tzinfo=pytz.UTC),
            'in_alarm': False,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alert = Alert.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'trigger':
                self.assertEqual(payload[key], alert.trigger.id)
            else:
                self.assertEqual(payload[key], getattr(alert, key))

    """
    These next evaluate_alert(in_alarm) tests depend on three main inputs.
    - The previous alert can be in_alarm=false, in_alarm=true, or none
    - The in_alarm argument can be false ("no") or true ("in")
    - breaching_channels is only needed if num_channels_operator=any
    """
    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_no_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=1)

        alert = trigger.evaluate_alert(False)
        self.assertEqual(1, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_in_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=1)

        alert = trigger.evaluate_alert(True)
        self.assertNotEqual(1, alert.id)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_no_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=2)

        alert = trigger.evaluate_alert(False)
        self.assertNotEqual(2, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_no_alarm2(self, send_alert):
        """
        Same as above except set alert_on_out_of_alarm to true
        """
        trigger = Trigger.objects.get(pk=2)
        trigger.alert_on_out_of_alarm = True
        trigger.save()

        # saving the trigger created a new alert with in_alarm=False
        # so make another with in_alarm=True
        old_alert = trigger.create_alert(True)
        alert = trigger.evaluate_alert(False)
        self.assertNotEqual(old_alert.id, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_in_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=2)

        alert = trigger.evaluate_alert(True)

        self.assertTrue(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_no_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=4)

        alert = trigger.evaluate_alert(False)
        self.assertIsNone(alert)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_in_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=4)

        alert = trigger.evaluate_alert(True)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_not_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=7)

        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        self.assertIsNone(alert)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=7)
        breaching_channels = [{
            "avg": 5,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }]

        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_not_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=8)

        n_alerts1 = trigger.alerts.count()
        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        n_alerts2 = trigger.alerts.count()
        self.assertEqual(n_alerts1, n_alerts2)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_breaching2(self, send_alert):
        trigger = Trigger.objects.get(pk=8)
        breaching_channels = [{
            "avg": 5,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }]

        n_alerts1 = trigger.alerts.count()
        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        n_alerts2 = trigger.alerts.count()
        self.assertNotEqual(n_alerts1, n_alerts2)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_not_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=9)

        n_alerts1 = trigger.alerts.count()
        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        n_alerts2 = trigger.alerts.count()
        self.assertNotEqual(n_alerts1, n_alerts2)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_not_breaching2(self, send_alert):
        """
        Same as above except set alert_on_out_of_alarm to true
        """
        trigger = Trigger.objects.get(pk=10)

        n_alerts1 = trigger.alerts.count()
        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        n_alerts2 = trigger.alerts.count()
        self.assertNotEqual(n_alerts1, n_alerts2)
        self.assertFalse(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=9)
        breaching_channels = [{
            "avg": 5,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }]

        n_alerts1 = trigger.alerts.count()
        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        n_alerts2 = trigger.alerts.count()
        self.assertNotEqual(n_alerts1, n_alerts2)
        self.assertTrue(alert.in_alarm)
        # trigger with num_channels_operator == ANY should send alert when
        # the channels have changed even if still in alarm
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_breaching2(self, send_alert):
        """
        Same as above except the same channel is breaching as the previous
        alert
        """
        trigger = Trigger.objects.get(pk=9)
        breaching_channels = [{
            "avg": 6,
            "channel": "UW:STA1:--:HNN",
            "channel_id": 1
        }]

        n_alerts1 = trigger.alerts.count()
        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        n_alerts2 = trigger.alerts.count()
        self.assertNotEqual(n_alerts1, n_alerts2)
        self.assertTrue(alert.in_alarm)
        # no alert sent if same channels are breaching as previous alert
        self.assertFalse(send_alert.called)

    def test_evaluate_alarm(self):
        '''This is more like an integration test at the moment'''
        monitor = Monitor.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 35, 0, 0, tzinfo=pytz.UTC)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 10)

        monitor.evaluate_alarm(endtime=endtime)

        # trigger 1 is breached
        # had previous alert with in_alarm = False,
        # check that a new one is created
        trigger = Trigger.objects.get(pk=1)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 2)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # trigger 2 is breached
        # already had an active alert, check that in_alarm is still True
        trigger = Trigger.objects.get(pk=2)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 2)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # trigger 3 is not breached
        # already had an active alert, check that there is a new one with
        # in_alarm = True
        trigger = Trigger.objects.get(pk=3)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 4)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertFalse(alert.in_alarm)

        # trigger 4 is breached
        # did not have an alert, check that new one is created
        trigger = Trigger.objects.get(pk=4)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 1)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # trigger 5 is not breached
        # did not have an alert, check that there is no new one
        trigger = Trigger.objects.get(pk=5)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 0)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 14)

    def test_evaluate_alarms(self):
        '''Test evaluate_alarm command'''
        n_monitors = len(Monitor.objects.all())
        with patch('measurement.models.Monitor.evaluate_alarm') as ea:
            call_command('evaluate_alarms')
            self.assertEqual(n_monitors, ea.call_count)

    def test_send_alert(self):
        self.alert.send_alert()

        self.assertEqual(len(mail.outbox), 1)

        for email in self.alert.trigger.emails:
            self.assertTrue(email in mail.outbox[0].recipients())

    def test_evaluate_alarms_filter_metric(self):
        '''Test evaluate_alarm command'''
        n_monitors = len(Monitor.objects.all())
        n_test2_monitors = len(Monitor.objects.filter(metric__name='test2'))
        with patch('measurement.models.Monitor.evaluate_alarm') as ea:
            call_command('evaluate_alarms', '--metric=test2')
            self.assertEqual(n_test2_monitors, ea.call_count)
            self.assertTrue(n_test2_monitors < n_monitors)

    def test_alert_queryset_sorted_by_timestamp(self):
        # Add two alerts out of (reverse) timestamp order
        Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1975, 1, 1, tzinfo=pytz.UTC),
            in_alarm=True,
            user=self.user
        )
        Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1980, 1, 1, tzinfo=pytz.UTC),
            in_alarm=True,
            user=self.user
        )

        url = reverse('measurement:alert-list')
        res = self.client.get(url)

        # Verify results are reverse sorted by timestamps
        timestamps = [alert['timestamp'] for alert in res.data]
        self.assertTrue(sorted(timestamps, reverse=True) == timestamps)

    def test_alert_filter(self):
        '''Test filtering alerts'''
        url = reverse('measurement:alert-list')

        stime, etime = '2018-02-01T03:00:00Z', '2018-02-01T04:15:00Z'
        url1 = url + f'?timestamp_gte={stime}&timestamp_lt={etime}'
        res = self.client.get(url1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)

        url2 = url + '?trigger=3'
        res = self.client.get(url2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

        url3 = url + '?trigger=3&in_alarm=True'
        res = self.client.get(url3)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_reset_alert_on_monitor_change(self):
        n_alerts1 = 0
        for trigger in self.monitor.triggers.all():
            n_alerts1 += trigger.alerts.count()

        self.monitor.interval_count = 5
        self.monitor.save()

        n_alerts2 = 0
        for trigger in self.monitor.triggers.all():
            n_alerts2 += trigger.alerts.count()

        self.assertNotEqual(n_alerts1, n_alerts2)

    def test_reset_alert_on_trigger_change(self):
        n_alerts1 = self.trigger.alerts.count()

        self.trigger.val2 = 7
        self.trigger.save()

        n_alerts2 = self.trigger.alerts.count()
        self.assertNotEqual(n_alerts1, n_alerts2)

    def test_check_daily_digest_no_alerts(self):
        self.monitor.check_daily_digest()

        # was an email sent? If no alerts then it shouldn't be
        self.assertEqual(len(mail.outbox), 0)

    def test_check_daily_digest_with_alerts(self):
        # Create a couple alerts for this monitor
        reftime = datetime(2020, 1, 2, 3, 0, 0, 0, tzinfo=pytz.UTC)

        ch1 = {
            "sum": 5,
            "channel": "UW:STA1:--:HNN",
            "channel_id": 1
        }
        ch2 = {
            "sum": 10,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }
        ch3 = {
            "sum": 15,
            "channel": "UW:STA3:--:HNN",
            "channel_id": 3
        }

        self.trigger.create_alert(
            True,
            breaching_channels=[ch1, ch2, ch3],
            timestamp=reftime + relativedelta(hours=1))
        self.trigger.create_alert(
            False,
            breaching_channels=[ch1],
            timestamp=reftime + relativedelta(hours=4))
        self.trigger.create_alert(
            True,
            breaching_channels=[ch1, ch2],
            timestamp=reftime + relativedelta(hours=6))

        self.monitor.check_daily_digest(
            digesttime=reftime + relativedelta(days=1))

        # was an email sent?
        self.assertEqual(len(mail.outbox), 1)
        for email in self.trigger.emails:
            self.assertTrue(email in mail.outbox[0].recipients())
