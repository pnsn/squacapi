from rest_framework import serializers
from .models import Network, Channel, Group, MatchingRule
from organization.models import Organization


# to dump data from db into fixtures
# ./mg.sh "dumpdata nslc" > app/nslc/fixtures/nslc_tests.json

# to run only these tests
# $:./mg.sh "test nslc.tests.test_nslc_api"

class GroupSerializer(serializers.ModelSerializer):

    channels_count = serializers.IntegerField(read_only=True)
    auto_include_channels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Channel.objects.all(),
        write_only=True
    )
    auto_exclude_channels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Channel.objects.all(),
        write_only=True
    )

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'description',
            'created_at', 'updated_at', 'user', 'organization',
            'share_all', 'share_org', 'channels_count',
            'auto_include_channels', 'auto_exclude_channels'
        )
        read_only_fields = ('id', 'user')
        ref_name = "NslcGroup"


class ChannelSerializer(serializers.ModelSerializer):
    net = serializers.PrimaryKeyRelatedField(
        queryset=Network.objects.all()
    )

    class Meta:
        model = Channel
        fields = ('id', 'class_name', 'code', 'name', 'sta',
                  'sta_name', 'description',
                  'sample_rate', 'net', 'loc', 'lat',
                  'lon', 'elev', 'azimuth', 'dip', 'created_at', 'updated_at',
                  'user', 'starttime', 'endtime', 'nslc')
        read_only_fields = ('id', 'nslc', 'user')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('net')
        return queryset


class ChannelSimpleSerializer(ChannelSerializer):
    network = serializers.StringRelatedField()

    class Meta:
        model = Channel
        fields = ('id', 'code', 'sta',
                  'net', 'loc', 'lat',
                  'lon', 'nslc')
        read_only_fields = ('id', 'nslc', 'user')


class GroupDetailSerializer(GroupSerializer):
    # Serializer when viewing details of specific group
    channels = ChannelSimpleSerializer(many=True, read_only=True)
    auto_include_channels = ChannelSimpleSerializer(many=True, read_only=True)
    auto_exclude_channels = ChannelSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'description', 'channels',
            'created_at', 'updated_at', 'user', 'organization',
            'share_all', 'share_org', 'channels_count',
            'auto_include_channels', 'auto_exclude_channels'
        )
        read_only_fields = ('id', 'user')


class NetworkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Network
        fields = ('class_name', 'code', 'name', 'description',
                  'created_at', 'updated_at', 'user')
        read_only_fields = ('user',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('channels')
        return queryset


class MatchingRuleSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all())

    class Meta:
        model = MatchingRule
        fields = ('id', 'network_regex', 'station_regex', 'location_regex',
                  'channel_regex', 'created_at', 'updated_at', 'user',
                  'group', 'is_include')
        read_only_fields = ('id', 'user')

    # remove regex cruft before returning
    def to_representation(self, instance):
        """Convert regex fields to string."""
        ret = super().to_representation(instance)
        ret['network_regex'] = self.stripRegex(ret['network_regex'])
        ret['station_regex'] = self.stripRegex(ret['station_regex'])
        ret['location_regex'] = self.stripRegex(ret['location_regex'])
        ret['channel_regex'] = self.stripRegex(ret['channel_regex'])
        return ret

    def stripRegex(self, instance):
        return instance.replace(
            "re.compile('", '').replace("', re.IGNORECASE)", '')
