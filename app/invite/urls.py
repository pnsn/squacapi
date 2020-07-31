from django.urls import path

from invite import views
app_name = 'invite'
urlpatterns = [
    path('invite/', views.InviteView.as_view(), name='user-invite'),
    path('register/', views.RegisterView.as_view(), name='user-register')
]
