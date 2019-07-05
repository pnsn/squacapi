from rest_framework import serializers
from .models import DataSource, Metric, Group


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:group-detail")

    class Meta:
        model = Group
        fields = (
            'id', 'name', 'url', 'description', 'is_public', 'created_at',
            'updated_at'
        )
        read_only_fields = ('id',)


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    datasource = serializers.PrimaryKeyRelatedField(
        queryset=DataSource.objects.all())
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail")

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'url', 'description', 'datasource', 'unit',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class DataSourceSerializer(serializers.HyperlinkedModelSerializer):
    metrics = MetricSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:datasource-detail")

    class Meta:
        model = DataSource
        fields = (
            'id', 'name', 'url', 'description',
            'created_at', 'updated_at', 'metrics'
        )
        read_only_fields = ('id',)
