from django_rest_passwordreset.serializers import TokenSerializer
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import UserSerializer, UserMeSerializer, \
    AuthTokenSerializer
from drf_yasg.utils import swagger_auto_schema


class CreateUserView(generics.CreateAPIView):
    '''create a new user in the system'''
    serializer_class = UserSerializer
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

# FIXME new invitation model goes here

# class ActivateUserByTokenView(generics.UpdateAPIView):
#     ''' Update invited user'''
#     serializer_class = UserSerializer

#     def update(self, request, *args, **kwargs):
#         user_data = request.data.pop('user')
#         instance = get_user_model().objects.get(email=user_data['email'])
#         # test.data['token']
#         try:
#             user = get_user_model().objects.get(
#                 email=user_data['email'],
#                 is_active=False
#             )
#         except get_user_model().DoesNotExist:
#             return Response("Your URL may have expired", status=404)
#         # if not RegistrationTokenGenerator().check_token(user, token):
#         #     return Response("Your token is invalid or expired", status=404)
#         user_data['is_active'] = True
#         serializer = self.serializer_class(
#             instance=instance,
#             data=user_data)
#         if serializer.is_valid(raise_exception=True):
#             serializer.update(instance, user_data)
#             return Response(serializer.data)
