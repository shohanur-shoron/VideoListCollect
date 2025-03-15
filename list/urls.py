from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_list, name="create_list"),
    path('view', views.view_table, name="view_table"),
    path('log-out', views.logOutUser, name="logOutUser"),
    path('long-video-all-links', views.video_list_by_date, name="video_list_by_date"),
    path('short-video-links', views.video_list_by_channel, name="video_list_by_channel"),
    path('login', views.login_user, name="login_user"),
    path('create-user', views.create_user, name="create_user"),
    path('short-video', views.create_short_video_list, name="create_short_video_list"),
]