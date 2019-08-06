from django.urls import path
from . import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('http/main.js', views.main),
    path('http/jquery.js', views.jquery),
    path('http/chart.js', views.chart),
    path('http/mostplayed.js', views.mostjs),
    path('http/mongo_response', views.mongo_request_resp),
    path('http/mongo_most', views.mongo_request_most),
    path('response', views.resp),
    path('mostplayed', views.mostplayed),
    path('sha256.js', views.sha256),
    path('sjcl.js', views.sjcl),
    path('check_password', views.check_password),
    path('restart_token', views.restart_token)
]
