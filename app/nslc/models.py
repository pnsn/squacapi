from django.db import models
from django.conf import settings
from datetime import datetime
import pytz
from organizations.models import Organization


class Nslc(models.Model):
    '''abstract base class used by all nslc models'''
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name'])
        ]

    '''force lowercase on code to provide for consistent url slug lookups'''
    def clean(self):
        self.code = self.code.lower()

    def __str__(self):
        return self.code.upper()

    def class_name(self):
        return self.__class__.__name__.lower()


class Network(Nslc):
    code = models.CharField(max_length=2, unique=True, primary_key=True)


class Channel(Nslc):
    code = models.CharField(max_length=3)
    station_code = models.CharField(max_length=5)
    station_name = models.CharField(max_length=255, blank=True)
    sample_rate = models.FloatField(null=True, blank=True)
    loc = models.CharField(max_length=2, default='--')
    lat = models.FloatField()
    lon = models.FloatField()
    elev = models.FloatField()
    depth = models.FloatField(default=0.0)
    azimuth = models.FloatField(default=0.0)
    dip = models.FloatField(default=0.0)
    sensor_description = models.CharField(max_length=255, default="",
                                          blank=True)
    scale = models.FloatField(default=0.0)
    scale_freq = models.FloatField(default=1.0)
    scale_units = models.CharField(max_length=32, default='M/S')
    starttime = models.DateTimeField(
        default=datetime(1970, 1, 1, tzinfo=pytz.UTC))
    endtime = models.DateTimeField(
        default=datetime(2599, 12, 31, tzinfo=pytz.UTC))
    network = models.ForeignKey(Network, on_delete=models.CASCADE,
                                related_name='channels')

    class Meta:
        unique_together = (("code", "network", 'station_code', 'loc'),)
        indexes = [
            models.Index(fields=['station_code']),
            models.Index(fields=['station_name']),
            models.Index(fields=['loc']),
            models.Index(fields=['lat']),
            models.Index(fields=['lon']),
            models.Index(fields=['-starttime']),
            models.Index(fields=['-endtime']),
        ]

    def __str__(self):
        return str(self.network_id.upper()) + ":" + \
            self.station_code.upper() + ":" + \
            self.loc.upper() + ":" + self.code.upper()


class Group(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nslcgroups'
    )
    channels = models.ManyToManyField('Channel')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    share_all = models.BooleanField(default=False)
    share_org = models.BooleanField(default=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='channel_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['share_all']),
            models.Index(fields=['share_org'])
        ]

    def __str__(self):
        return self.name
