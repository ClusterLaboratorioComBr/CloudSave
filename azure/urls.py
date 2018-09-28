from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from . import views
app_name = "instances"
urlpatterns = [
    # path("", views.index, name='index'),
    path("home/", views.index, name='home' ),
    path("vms/", views.getDeallocatedInstances,name='vms'),
    path("disks/", views.index,name='disks'),
    path("blob/", views.index,name='blob'),
    path("collect/", views.collectVmsFromAzure,name='collect')
]
