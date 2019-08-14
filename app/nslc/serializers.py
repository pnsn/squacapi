from rest_framework import serializers
from .models import Network, Station, Channel, Group, ChannelGroup


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
    station = serializers.PrimaryKeyRelatedField(
        queryset=Station.objects.all()
    )
    channelgroup = ChannelGroupSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="nslc:channel-detail")

    class Meta:
        model = Channel
        fields = ('class_name', 'code', 'name', 'id', 'url', 'description',
                  'channelgroup', 'sample_rate', 'station', 'loc', 'lat',
                  'lon', 'elev', 'created_at', 'updated_at')
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('station')
        return queryset


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
