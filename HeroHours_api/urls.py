from django.urls import path
from .views import SheetPullAPI, MeetingPullAPI

urlpatterns = [
    path('sheet/users/', SheetPullAPI.as_view(), name='sheet'),
    path('sheet/<int:year>/<int:month>/<int:day>/', MeetingPullAPI.as_view(), name='sheet meeting'),
]