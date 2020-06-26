from rest_framework import viewsets
# from squac.permissions import IsAdminOwnerOrPublicReadOnly
# from squac.mixins import SetUserMixin, PermissionsMixin
from django_filters import rest_framework as filters

from institution.models import Institution, InstitutionUser
from institution.serializers import InstitutionSerializer,\
    InstitutionUserSerializer
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from organizations.backends import invitation_backend


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

    '''overriding for two reasons
        1) Need to hook in invitation
        2) Nested serializers suck.
            *pop user off of request.data
            *invite user
            *update request.data with user_id
    '''
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        user_param = request.data.pop('user')
        user = invitation_backend().invite_by_email(
            user_param['email'],
            **{'firstname': user_param['firstname'],
                'lastname': user_param['lastname'],
                'organization': request.data['organization'],
                'is_admin': request.data['is_admin']}
        )
        request.data['user'] = user.id
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        user_param = request.data.pop('user')
        user = get_user_model().objects.get(email=user_param['email'])
        request.data['user'] = user.id

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)
