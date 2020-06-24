from rest_framework import viewsets
# from squac.permissions import IsAdminOwnerOrPublicReadOnly
# from squac.mixins import SetUserMixin, PermissionsMixin
from django_filters import rest_framework as filters

from institution.models import Institution, InstitutionUser
from institution.serializers import InstitutionSerializer,\
    InstitutionUserSerializer


class InstitutionUserFilter(filters.FilterSet):
    class Meta:
        model = InstitutionUser
        fields = ('organization',)


class InstitutionViewSet(viewsets.ModelViewSet):
    # filter_class = ChannelFilter
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer


class InstitutionUserViewSet(viewsets.ModelViewSet):
    queryset = InstitutionUser.objects.all()
    filter_class = InstitutionUserFilter
    serializer_class = InstitutionUserSerializer
