from django_rest_passwordreset.serializers import TokenSerializer
from django.utils.decorators import method_decorator
from django.contrib.auth.models import Group
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import UserWriteSerializer, UserMeSerializer, \
    AuthTokenSerializer, UserGroupSerializer, NotificationSerializer, \
    ContactSerializer
from drf_yasg.utils import swagger_auto_schema
from core.models import Contact, Notification
from squac.mixins import SetUserMixin
from squac.permissions import IsAdminOrOwner


class CreateUserView(generics.CreateAPIView):
    '''create a new user in the system'''
    serializer_class = UserWriteSerializer
    permission_classes = (IsAuthenticated,)


@method_decorator(name="post", decorator=swagger_auto_schema(
    request_body=AuthTokenSerializer,
    responses={200: TokenSerializer}
))
class CreateTokenView(ObtainAuthToken):
    '''create a new auth token for user'''
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserMeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class GroupViewSet(viewsets.ModelViewSet):
    """Manage the authenticated user"""
    serializer_class = UserGroupSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Group.objects.all()


class ContactViewSet(SetUserMixin, viewsets.ModelViewSet):
    """Manage contact info"""
    serializer_class = ContactSerializer

    def get_queryset(self):
        return Contact.objects.all()


class NotificationViewSet(SetUserMixin, viewsets.ModelViewSet):
    '''Manage user notifications'''
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated, IsAdminOrOwner,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)
