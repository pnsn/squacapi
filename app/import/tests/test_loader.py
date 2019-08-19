from django.test import TestCase

from measurement.models import Metric, Measurement
from nslc.models import Network, Station, Channel, Group
from dashboard.models import Dashboard, WidgetType, Widget

from load import load_all


class PublicImportTests(TestCase):
    '''Test the db test data loader'''

    def setUp(self):
        load_all.main(1)
        self.nets = Network.objects.all()
        self.stations = Station.objects.all()
        self.channels = Channel.objects.all()
        self.groups = Group.objects.all()
        self.measures = Measurement.objects.all()
        self.metrics = Metric.objects.all()
        self.dashboards = Dashboard.objects.all()
        self.widtypes = WidgetType.objects.all()
        self.widgets = Widget.objects.all()

    def test_nslc_load(self):
        self.assertNotEqual(len(self.nets), 0)
        self.assertNotEqual(len(self.stations), 0)
        self.assertNotEqual(len(self.channels), 0)
        self.assertNotEqual(len(self.groups), 0)

        for g in self.groups:
            net = g.name[:2].lower()
            n_channels = Channel.objects.filter(station__network__code=net)
            # Find network from a slice of group name
            g_channels = g.channels.all()
            for c in n_channels:
                self.assertIn(c, g_channels)

    def test_measurement_loader(self):
        self.assertNotEqual(len(self.measures), 0)
        self.assertNotEqual(len(self.metrics), 0)

    def test_dashboard_loader(self):
        self.assertNotEqual(len(self.dashboards), 0)
        self.assertNotEqual(len(self.widtypes), 0)
        self.assertNotEqual(len(self.widgets), 0)
        for w in self.widgets:
            self.assertIn(w.dashboard, self.dashboards)
            self.assertIn(w.widgettype, self.widtypes)
            self.assertIsNotNone(w.metrics)
