from django.urls import path
from . import views

urlpatterns = [
    path('polls/', views.PollList.as_view(), name='poll-list'),
    path('polls/<int:pk>/', views.PollDetail.as_view(), name ='poll-detail'),
    path('process/', views.Process.as_view(), name ='process-poll'),
    path('user/<int:user_pk>/', views.Process.as_view(), name ='process-poll-user'),
]

