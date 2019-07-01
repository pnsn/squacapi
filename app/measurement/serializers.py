from rest_framework import serializers
from .models import DataSource


class DataSourceSerializer(serializers.HyperlinkedModelSerializer):
    location = serializers.StringRelatedField()
    url = serializers.HyperLinkedIdentityField(
        view_name="measurement:datasource-detail"
    )

    class Meta:
        model = DataSource
        fields = ('class_name', 'name', 'id', 'url', 'description',
                  'created_at', 'updated_at')

    @staticmethod
    def setup_eager_loading(queryset):
        # queryset = queryset.select_related('metric')
        return queryset
