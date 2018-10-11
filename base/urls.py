from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from . import views
app_name = "instances"
urlpatterns = [
    # path("", views.index, name='index'),
    path("", views.index, name='home' ),
]
