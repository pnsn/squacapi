from rest_framework.decorators import api_view, authentication_classes, \
    permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import IsAuthenticated


@api_view()
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def home_v1(request, format=None):

    nslc = reverse('nslc:api-root', request=request,
                   format=format)
    measurement = reverse('measurement:api-root', request=request,
                          format=format)
    dashboard = reverse('dashboard:api-root', request=request,
                        format=format)

    return Response({"Dashboards": dashboard,
                     "Measurements": measurement,
                     "Networks and Channels": nslc})
