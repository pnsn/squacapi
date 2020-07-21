from rest_framework import viewsets
from squac.mixins import SetUserMixin, OrganizationPermissionsMixin
from django_filters import rest_framework as filters
from organization.models import Organization
from organization.serializers import OrganizationSerializer
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from user.serializers import UserSerializer, UserSimpleSerializer
import secrets

class OrganizationUserFilter(filters.FilterSet):
    class Meta:
        model = get_user_model()
        fields = ('organization', )


class OrganizationBase(SetUserMixin, viewsets.ModelViewSet):
    pass


class OrganizationViewSet(OrganizationBase):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.all()


class OrganizationUserViewSet(OrganizationBase):
    filter_class = OrganizationUserFilter
    serializer_class = UserSerializer

    '''overriding for two reasons
        1) Need to hook into invitation
        2) Nested serializers suck.
            *pop user off of request.data
            *invite user
            *update request.data with user_id
    '''
    def get_queryset(self):
        return get_user_model().objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        _data = request.data

        # user_param = request.data.pop('user')
        try:
            email = _data['email']
            get_user_model().objects.get(email=email)
            message = f"A user with {email} exists "
            return Response(message, status=400)
            # firstname = existing_user.firstname
            # lastname = existing_user.lastname
        except get_user_model().DoesNotExist:
            pass
        
        '''QueryParam object is immutable, so we need to change that'''
        # remember state
        # _mutable = _data._mutable
        # set to mutable
        # _data._mutable = True
        _data['firstname'] = 'firstname'
        _data['lastname'] = 'lastname'
        _data['password'] = secrets.token_hex(16)

        # set mutable flag back
        # _data = _mutable


        #invite  new user here
        # user = invitation_backend().invite_by_email(
        #     user_param['email'],
        #     **{'firstname': firstname,
        #         'lastname': lastname,
        #         'organization': request.data['organization'],
        #         'is_admin': request.data['is_admin']}
        # )
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserSimpleSerializer
        return self.serializer_class
