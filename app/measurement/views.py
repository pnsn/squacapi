from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import DataSource
from measurement.serializers import DataSourceSerializer
import django_filters as filters

'''Common methods for filtering classes to share'''


class BaseMeasurementViewSet(viewsets.ModelViewSet):
    '''base class for measurement viewsets:

    Permissions are IsAuthenticatedOrReadOnly
        This allows auth user full crud but unauthorized user to only view'''

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (ObjPermissionOrReadOnly, )

    # all models require an auth user, set on create
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DataSourceViewSet(BaseMeasurementViewSet):
    serializer_class = DataSourceSerializer
    filter_class = DataSourceFilter
    q = DataSource.objects.all()
    queryset = serializer_class.setup_eager_loading(q)
