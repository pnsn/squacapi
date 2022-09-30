
from django.db import models
from django.conf import settings
from datetime import datetime
import pytz
from organization.models import Organization
from regex_field.fields import RegexField
from django.db.models import Q
import re
from django.db.models.signals import m2m_changed


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
    name = models.CharField(max_length=255, blank=True)
    station = models.CharField(max_length=5)
    station_name = models.CharField(max_length=255, blank=True)
    sample_rate = models.FloatField(null=True, blank=True)
    location = models.CharField(max_length=2, default='--')
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField()
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
    nslc = models.CharField(max_length=255, null=True)

    class Meta:
        unique_together = (("code", "network", 'station', 'location'),)
        indexes = [
            models.Index(fields=['station']),
            models.Index(fields=['station_name']),
            models.Index(fields=['location']),
            models.Index(fields=['latitude']),
            models.Index(fields=['longitude']),
            models.Index(fields=['-starttime']),
            models.Index(fields=['-endtime']),
            models.Index(fields=['nslc'])
        ]

    def __str__(self):
        return str(self.network_id.upper()) + "." + \
            self.station.upper() + "." + \
            self.location.upper() + "." + self.code.upper()

    def save(self, *args, **kwargs):
        if not self.nslc:
            self.nslc = self.to_nslc()
        super().save(*args, **kwargs)

    def to_nslc(self):
        return str(self.network_id) + "." + \
            self.station + "." + \
            self.location + "." + self.code


class Group(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nslcgroups'
    )
    channels = models.ManyToManyField('Channel')
    auto_include_channels = models.ManyToManyField(
        'Channel', related_name='+')
    auto_exclude_channels = models.ManyToManyField(
        'Channel', related_name='+')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='channel_groups'
    )
    share_all = models.BooleanField(default=False)
    share_org = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_auto_update(self):
        """
        Determines whether this group has the necessary information to
        auto-update
        """
        return any([self.matching_rules.count() > 0,
                    self.auto_include_channels.count() > 0,
                    self.auto_exclude_channels.count() > 0])

    def update_channels(self):
        if not self.can_auto_update():
            return

        # 1. Construct query to add channels
        include_query = Q()

        # First add channels based on matching rules
        for matching_rule in self.matching_rules.all():
            if not matching_rule.is_include:
                continue
            include_query = include_query | Q(
                network__code__iregex=matching_rule.network_regex.pattern,
                station__iregex=matching_rule.station_regex.pattern,
                location__iregex=matching_rule.location_regex.pattern,
                code__iregex=matching_rule.channel_regex.pattern
            )

        # Now add channels in auto_include_channels
        if self.auto_include_channels.count() > 0:
            include_query = include_query | Q(
                id__in=self.auto_include_channels.all()
            )
        channels = Channel.objects.filter(include_query)

        # 2. Construct query to exclude channels
        exclude_query = Q()

        # First add channels based on matching rules
        for matching_rule in self.matching_rules.all():
            if matching_rule.is_include:
                continue
            exclude_query = exclude_query | Q(
                network__code__iregex=matching_rule.network_regex.pattern,
                station__iregex=matching_rule.station_regex.pattern,
                location__iregex=matching_rule.location_regex.pattern,
                code__iregex=matching_rule.channel_regex.pattern
            )

        # Now add channels in auto_exclude_channels
        if self.auto_exclude_channels.count() > 0:
            exclude_query = exclude_query | Q(
                id__in=self.auto_exclude_channels.all()
            )

        channels = channels.exclude(exclude_query)

        # 3. Finish
        # Now actually add channels
        self.channels.set(channels)
        self.save()

    def __str__(self):
        return self.name


def channels_changed(instance, action, **kwargs):

    # after m2m change is saved
    if action in ['post_add', 'post_clear', 'post_remove']:
        p = Group.objects.get(id=instance.id)
        # update the channels
        p.update_channels()


# update channels after auto_include or auto_exclude are changed
m2m_changed.connect(
    channels_changed, sender=Group.auto_include_channels.through)
m2m_changed.connect(
    channels_changed, sender=Group.auto_exclude_channels.through)


class MatchingRule(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    network_regex = RegexField(
        max_length=128, default="", blank=True, re_flags=re.IGNORECASE)
    station_regex = RegexField(
        max_length=128, default="", blank=True, re_flags=re.IGNORECASE)
    location_regex = RegexField(
        max_length=128, default="", blank=True, re_flags=re.IGNORECASE)
    channel_regex = RegexField(
        max_length=128, default="", blank=True, re_flags=re.IGNORECASE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='matching_rules'
    )
    is_include = models.BooleanField(default=True)

    def __str__(self):
        in_ex = 'include' if self.is_include else 'exclude'
        return (f'{in_ex}: '
                f'"{self.network_regex.pattern}".'
                f'"{self.station_regex.pattern}".'
                f'"{self.location_regex.pattern}".'
                f'"{self.channel_regex.pattern}"')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.group.update_channels()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.group.update_channels()
