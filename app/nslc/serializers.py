from rest_framework import serializers
from .models import Network, Station, Channel, Group
from dashboard.serializers import DashboardSerializer


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
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class ChannelSerializer(serializers.HyperlinkedModelSerializer):
    station = serializers.PrimaryKeyRelatedField(
        queryset=Station.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(view_name="nslc:channel-detail")

    class Meta:
        model = Channel
        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'sample_rate', 'station', 'loc', 'lat',
                  'lon', 'elev', 'created_at', 'updated_at')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('station')
        return queryset


class GroupDetailSerializer(GroupSerializer):
    # Serializer when viewing details of specific group
    dashboards = DashboardSerializer(many=True, read_only=True)
    channels = ChannelSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = (
            'name', 'id', 'url', 'description', 'dashboards', 'channels',
            'is_public', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class StationSerializer(serializers.HyperlinkedModelSerializer):
    network = serializers.PrimaryKeyRelatedField(
        queryset=Network.objects.all()
    )
    channels = ChannelSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="nslc:station-detail")

    class Meta:
        model = Station

        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'created_at', 'updated_at', 'network', 'channels')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        # prefetch eagerloads to-many: stations have many channels
        queryset = queryset.prefetch_related('channels')
        queryset = queryset.select_related('network')
        return queryset


class NetworkSerializer(serializers.HyperlinkedModelSerializer):
    stations = StationSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="nslc:network-detail")

    class Meta:
        model = Network
        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'created_at', 'updated_at', 'stations')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('stations')
        queryset = queryset.prefetch_related('stations__channels')
        return queryset
