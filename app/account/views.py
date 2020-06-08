from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated
# from django_filters import rest_framework as filters
# from squac.permissions import IsAdminOwnerOrPublicReadOnly
# from squac.filters import CharInFilter
# from squac.mixins import SetUserMixin, PermissionsMixin
from account.models import Account, AccountUser
from account.serializers import AccountSerializer, AccountUserSerializer


class AccountViewSet(viewsets.ModelViewSet):
    # filter_class = ChannelFilter
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class AccountUserViewSet(viewsets.ModelViewSet):
    queryset = AccountUser.objects.all()
    serializer_class = AccountUserSerializer
