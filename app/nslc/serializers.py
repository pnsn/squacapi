from rest_framework import serializers
from .models import Network, Channel, Group, MatchingRule
from organization.models import Organization


# to dump data from db into fixtures
# ./mg.sh "dumpdata nslc" > app/nslc/fixtures/nslc_tests.json

# to run only these tests
# $:./mg.sh "test nslc.tests.test_nslc_api"


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    # Group Serializer for list view, will not include channels/dashboards
    url = serializers.HyperlinkedIdentityField(
        view_name='nslc:group-detail'
    )
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

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'url', 'description', 'channels',
            'created_at', 'updated_at', 'user_id', 'organization',
            'auto_include_channels', 'auto_exclude_channels'
        )
        read_only_fields = ('id',)
        ref_name = "NslcGroup"


class ChannelSerializer(serializers.HyperlinkedModelSerializer):
    network = serializers.PrimaryKeyRelatedField(
        queryset=Network.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(view_name="nslc:channel-detail")

    class Meta:
        model = Channel
        fields = ('id', 'class_name', 'code', 'name', 'station_code',
                  'station_name', 'url', 'description',
                  'sample_rate', 'network', 'loc', 'lat',
                  'lon', 'elev', 'azimuth', 'dip', 'created_at', 'updated_at',
                  'user_id', 'starttime', 'endtime', 'nslc')
        read_only_fields = ('id', 'nslc')

    @ staticmethod
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
            'name', 'id', 'url', 'description', 'channels',
            'created_at', 'updated_at', 'user_id', 'organization',
            'auto_include_channels', 'auto_exclude_channels'
        )
        read_only_fields = ('id',)


class NetworkSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="nslc:network-detail")

    class Meta:
        model = Network
        fields = ('class_name', 'code', 'name', 'url', 'description',
                  'created_at', 'updated_at', 'user_id')
        # read_only_fields = ('id',)

    @ staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('channels')
        return queryset


class MatchingRuleSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="nslc:matching-rule-detail")
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all())

    class Meta:
        model = MatchingRule
        fields = ('id', 'network_regex', 'station_regex', 'location_regex',
                  'channel_regex', 'created_at', 'updated_at', 'user_id',
                  'group', 'is_include', 'url')
        read_only_fields = ('id',)

    def to_representation(self, instance):
        """Convert regex fields to string."""
        ret = super().to_representation(instance)
        ret['network_regex'] = self.stripRegex(ret['network_regex'])
        ret['station_regex'] = self.stripRegex(ret['station_regex'])
        ret['location_regex'] = self.stripRegex(ret['location_regex'])
        ret['channel_regex'] = self.stripRegex(ret['channel_regex'])
        return ret

    def stripRegex(self, instance):
        return instance.strip(
            "re.compile('").strip("', re.IGNORE_CASE)")
