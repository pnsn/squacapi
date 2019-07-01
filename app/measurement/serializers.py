from rest_framework import serializers
from .models import DataSource, Metric


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    datasource = serializers.StringRelatedField()
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail")

    class Meta:
        model = Metric
        fields = ('id', 'name', 'url', 'description', 'unit', 'datasource',
                  'created_at', 'updated_at', 'datasource')


class DataSourceSerializer(serializers.HyperlinkedModelSerializer):
    metric = MetricSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:datasource-detail")

    class Meta:
        model = DataSource
        fields = ('id', 'name', 'url', 'description',
                  'created_at', 'updated_at', 'metric')
