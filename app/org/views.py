from rest_framework import viewsets
# from squac.permissions import IsAdminOwnerOrShared
# from squac.mixins import SetUserMixin, PermissionsMixin
from django_filters import rest_framework as filters
from organizations.models import (Organization, OrganizationUser)
# from org.models import Org, OrgUser
from org.serializers import OrganizationSerializer,\
    OrganizationUserSerializer, OrganizationUserDetailSerializer
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from organizations.backends import invitation_backend


class OrganizationUserFilter(filters.FilterSet):
    class Meta:
        model = OrganizationUser
        fields = ('organization', 'user')


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class OrganizationUserViewSet(viewsets.ModelViewSet):
    queryset = OrganizationUser.objects.all()
    filter_class = OrganizationUserFilter
    serializer_class = OrganizationUserSerializer

    '''overriding for two reasons
        1) Need to hook into invitation
        2) Nested serializers suck.
            *pop user off of request.data
            *invite user
            *update request.data with user_id
    '''

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        user_param = request.data.pop('user')
        try:
            existing_user = get_user_model().objects.get(
                email=user_param['email'])
            firstname = existing_user.firstname
            lastname = existing_user.lastname
        except get_user_model().DoesNotExist:
            firstname = 'firstname'
            lastname = 'lastname'

        user = invitation_backend().invite_by_email(
            user_param['email'],
            **{'firstname': firstname,
                'lastname': lastname,
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

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrganizationUserDetailSerializer
        return self.serializer_class
