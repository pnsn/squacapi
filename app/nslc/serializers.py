from rest_framework import serializers
from .models import Network, Channel, Group

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

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'url', 'description', 'channels', 'is_public',
            'created_at', 'updated_at', 'user_id'
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
                  'lon', 'elev', 'created_at', 'updated_at', 'user_id')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('network')
        return queryset


class GroupDetailSerializer(GroupSerializer):
    # Serializer when viewing details of specific group
    channels = ChannelSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'url', 'description', 'channels', 'is_public',
            'created_at', 'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class NetworkSerializer(serializers.HyperlinkedModelSerializer):
    # stations = StationSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="nslc:network-detail")

    class Meta:
        model = Network
        fields = ('class_name', 'code', 'name', 'url', 'description',
                  'created_at', 'updated_at', 'user_id')
        # read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('channels')
        return queryset
