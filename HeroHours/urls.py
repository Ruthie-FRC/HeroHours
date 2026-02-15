from django.conf import settings
from django.contrib.auth.views import LoginView
from django.urls import path, include
from . import views
from .admin import add_user


urlpatterns = [
    path('', views.index, name='index'),
    path("insert/", views.handle_entry, name='in-out'),
    path("send_data_to_google_sheet/",views.send_data_to_google_sheet,name='send_data_to_google_sheet'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('custom/', add_user,name='custom'),
    path('pull_sheet/',views.sheet_pull,name='pull_sheet'),
    path('live/', views.live_view, name='live_view'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]