from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import DataSource, Metric
from measurement.serializers import DataSourceSerializer, MetricSerializer


@api_view(['GET'])
def api_root(request, format=None):
    '''api root'''
    return Response({
        'nets': reverse('network-list', request=request, format=format),
    })


class ObjPermissionOrReadOnly(BasePermission):
    '''Object-level permission on scarey methods, read only on safe methods'''

    def has_permission(self, request, view):
        '''http permission?'''

        if request.method in SAFE_METHODS:
            return True
        # user must be authenticated
        return request.user and request.user.is_authenticated

    def has_obj_permission(self, request, view, obj):
        '''object level permissions, set by adding user to group

        Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        '''
        if request.method in SAFE_METHODS:
            return True

        # user must have permission
        return self.check_object_permissions(request, obj)


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
    # filter_class = DataSourceFilter
    queryset = DataSource.objects.all()


class MetricViewSet(BaseMeasurementViewSet):
    serializer_class = MetricSerializer
    queryset = Metric.objects.all()
