from django.shortcuts import render
import datetime
title = "Azuremon"
menu = {}
menu = {
    "home": "HOME",
    "vms": "Virtual Machines",
    "disks": "Disks",
    "blob":  "Blob",
    "collect": "Collect data"}
now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
# Create your views here.
def index(request):
    return render(request, 'index.html', {"active":"home","menu": menu,'title':title, 'data':now})