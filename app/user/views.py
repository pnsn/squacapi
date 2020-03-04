from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from squac.mixins import PermissionsMixin
from user.serializers import UserSerializer, AuthTokenSerializer


class BaseMeasurementViewSet(PermissionsMixin):
    # TODO implement permission mixins on user
    pass


class CreateUserView(generics.CreateAPIView):
    '''create a new user in the system'''
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class CreateTokenView(ObtainAuthToken):
    '''create a new auth token for user'''
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
