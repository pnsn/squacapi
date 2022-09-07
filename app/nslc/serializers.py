from rest_framework import serializers
from .models import Network, Channel, Group, MatchingRule
from organization.models import Organization


# to dump data from db into fixtures
# ./mg.sh "dumpdata nslc" > app/nslc/fixtures/nslc_tests.json

# to run only these tests
# $:./mg.sh "test nslc.tests.test_nslc_api"


class GroupSerializer(serializers.ModelSerializer):
    # Group Serializer for list view, will not include channels/dashboards
    channels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Channel.objects.all()
    )
    auto_include_channels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Channel.objects.all()
    )
    auto_exclude_channels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Channel.objects.all()
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    user = serializers.StringRelatedField()

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'description', 'channels',
            'created_at', 'updated_at', 'user', 'organization',
            'auto_include_channels', 'auto_exclude_channels'
        )
        read_only_fields = ('id', 'user')
        ref_name = "NslcGroup"


class ChannelSerializer(serializers.ModelSerializer):
    network = serializers.PrimaryKeyRelatedField(
        queryset=Network.objects.all()
    )

    class Meta:
        model = Channel
        fields = ('id', 'class_name', 'code', 'name', 'station_code',
                  'station_name', 'description',
                  'sample_rate', 'network', 'loc', 'lat',
                  'lon', 'elev', 'azimuth', 'dip', 'created_at', 'updated_at',
                  'user', 'starttime', 'endtime', 'nslc')
        read_only_fields = ('id', 'nslc', 'user')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('network')
        return queryset


class GroupDetailSerializer(GroupSerializer):
    # Serializer when viewing details of specific group
    channels = ChannelSerializer(many=True, read_only=True)
    auto_include_channels = ChannelSerializer(many=True, read_only=True)
    auto_exclude_channels = ChannelSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'description', 'channels',
            'created_at', 'updated_at', 'user', 'organization',
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
