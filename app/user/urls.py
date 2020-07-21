from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
    # FIXME new inviation model goes here
    # path('activate/', views.ActivateUserByTokenView.as_view(),
    #     name='activate_user')
]
