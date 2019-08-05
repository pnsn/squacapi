from rest_framework import serializers
from .models import Network, Station, Location, Channel, Group, ChannelGroup
# from rest_framework.relations import HyperlinkedIdentityField


class ChannelGroupSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="nslc:channelgroup-detail"
    )

    class Meta:
        model = ChannelGroup
        fields = ('id', 'group', 'channel', 'url', 'created_at', 'updated_at')
        read_only_fields = ('id',)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    channelgroup = ChannelGroupSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='nslc:group-detail')

    class Meta:
        model = Group
        fields = ('name', 'id', 'url', 'description', 'is_public',
                  'channelgroup', 'created_at', 'updated_at')
        read_only_fields = ('id',)


class ChannelSerializer(serializers.HyperlinkedModelSerializer):
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all()
    )
    channelgroup = ChannelGroupSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="nslc:channel-detail")

    class Meta:
        model = Channel
        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'channelgroup', 'sample_rate', 'location', 'created_at',
                  'updated_at')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('location')
        return queryset


class LocationSerializer(serializers.HyperlinkedModelSerializer):
    station = serializers.PrimaryKeyRelatedField(
        queryset=Station.objects.all()
    )
    channels = ChannelSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="nslc:location-detail")

    class Meta:
        model = Location
        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'lat', 'lon', 'elev', 'station', 'created_at', 'updated_at',
                  'channels')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('channels')
        queryset = queryset.select_related('station')
        return queryset


class StationSerializer(serializers.HyperlinkedModelSerializer):
    network = serializers.PrimaryKeyRelatedField(
        queryset=Network.objects.all()
    )
    locations = LocationSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="nslc:station-detail")

    class Meta:
        model = Station

        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'created_at', 'updated_at', 'network', 'locations')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        # prefetch eagerloads to-many: stations have many locations
        queryset = queryset.prefetch_related('locations')
        # select_related eager loads to-one: stations have one network
        queryset = queryset.select_related('network')
        queryset = queryset.prefetch_related('locations__channels')
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
        queryset = queryset.prefetch_related('stations__locations')
        queryset = queryset.prefetch_related('stations__locations__channels')
        return queryset
