from rest_framework import viewsets
from squac.mixins import SetUserMixin, OrganizationPermissionsMixin
from django_filters import rest_framework as filters
from organization.models import Organization
from organization.serializers import OrganizationSerializer
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from user.serializers import UserSerializer
import secrets


class OrganizationUserFilter(filters.FilterSet):
    order = filters.OrderingFilter(
        fields=(('firstname', 'firstname'),
                ('lastname', 'lastname'),
                ('organization_name', 'organization'),
                ('email', 'email'),
                ('last_login', 'last_login'),
                ('is_active', 'is_active'),
                ('is_org_admin', 'is_org_admin'),
                ),

    )

    class Meta:
        model = get_user_model()
        fields = ('organization', )


class OrganizationFilter(filters.FilterSet):
    order = filters.OrderingFilter(
        fields=(('name', 'name'),
                ('description', 'description')),
    )

    class Meta:
        model = Organization
        fields = ('name',)


class OrganizationBase(SetUserMixin, OrganizationPermissionsMixin,
                       viewsets.ModelViewSet):
    pass


class OrganizationViewSet(OrganizationBase):
    filter_class = OrganizationFilter
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.all()


class OrganizationUserViewSet(OrganizationBase):
    filter_class = OrganizationUserFilter
    serializer_class = UserSerializer

    def get_queryset(self):
        return get_user_model().objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        _data = request.data

        try:
            email = _data['email']
            get_user_model().objects.get(email=email)
            message = f"A user with {email} exists "
            return Response(message, status=400)
        except get_user_model().DoesNotExist:
            pass
        '''data object is immutable, so we need to change that'''
        _mutable = False
        try:
            '''if object is passed in as json it is dict
               otherwise is is QueryDict, which is immutable
            '''
            _mutable = _data._mutable
            # set to mutable
            _data._mutable = True

        except AttributeError:
            pass
        # set temp password
        _data['password'] = secrets.token_hex(16)
        try:
            _data._mutable = _mutable
        except AttributeError:
            pass

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)
