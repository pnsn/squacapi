from squac.mixins import EnablePartialUpdateMixin, OverrideParamsMixin
from django_rest_passwordreset.serializers import TokenSerializer
from django.utils.decorators import method_decorator
from django.contrib.auth.models import Group
from rest_framework import generics, viewsets
from squac.permissions import IsAdminOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import UserMeSerializer, \
    AuthTokenSerializer, UserGroupSerializer, UserSerializer
from drf_yasg.utils import swagger_auto_schema


@method_decorator(name="post", decorator=swagger_auto_schema(
    request_body=AuthTokenSerializer,
    responses={200: TokenSerializer}
))
class CreateTokenView(ObtainAuthToken):
    '''create a new auth token for user'''
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class CreateUserView(generics.CreateAPIView):
    '''create a new user in the system'''
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser, )


class ManageUserView(generics.RetrieveUpdateAPIView,
                     EnablePartialUpdateMixin):
    """Manage the authenticated user"""
    serializer_class = UserMeSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user


class GroupViewSet(OverrideParamsMixin, viewsets.ModelViewSet):
    """Manage user permissions groups"""
    serializer_class = UserGroupSerializer
    permission_classes = (IsAuthenticated, IsAdminOwnerOrReadOnly, )

    def get_queryset(self):
        return Group.objects.all()
