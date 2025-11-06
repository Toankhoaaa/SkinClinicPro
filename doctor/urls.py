from django.urls import path
from . import views

urlpatterns = [
    path("my_profile/", views.myProfileView, name="my_profile"),
    # path("update_profile/", views.updateProfileView, name="profile"),
    # path("delete_profile/", views.deleteProfileView, name="delete_profile"),
]

urlpatterns += [
    # path("my_schedule/", views.myScheduleView, name="my_schedule"),
    # path("update_schedule/", views.updateScheduleView, name="schedule"),
    # path("delete_schedule/", views.deleteScheduleView, name="delete_schedule"),
]