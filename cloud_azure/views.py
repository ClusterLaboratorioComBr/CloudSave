from django.shortcuts import render
from pymongo import MongoClient
# from src.azure import Azclass as az
from src.azuresdk import Azclass as az
import threading, time, os, datetime
from src.azuresdk import AzureSdk as azsdk
title = "Azuremon"
az_appid = os.environ['AZ_APPID']
az_dn = os.environ['AZ_DISPLAYNAME']
az_name = os.environ['AZ_NAME']
az_passwd = os.environ['AZ_PASSWD']
az_tenant = os.environ['AZ_TENANT']
az_subscription = os.environ['AZ_SUBSCRIPTION']
mongoserver = os.environ['MONGOSERVER']
mongodb = os.environ['MONGODB']
menu = {}
menu = {
    "home": "HOME",
    "vms": "Virtual Machines",
    "disks": "Disks",
    "blob":  "Blob",
    "collect": "Collect data"}
now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def index(request):
    return render(request, 'index.html', {"active":"home","menu": menu,'title':title, 'data':now})
def azure(request):
    return  render(request, 'azure.html',{"active":"home","menu": menu,'title':title, 'data':now})
def tags(request):
    mongocollection = "vms"
    client = MongoClient(mongoserver)
    db = client[mongodb]
    collection = db[mongocollection]
    try:
        col_datetime = max(collection.find().distinct("datetime"))
        # col_datetime = collection.distinct("datetime")
        vms = collection.find({"datetime":col_datetime})
        # vms = collection.find({"datetime":col_datetime,"tags":{"$eq":None}})
        # vms = collection.find({"datetime":col_datetime,"tags":{"$eq":None}})
    except ValueError as err:
        print(err)
    array = []
    for vm in vms:
        if "billing" not in vm["tags"]:
            # print(vm["tags"])
            array.append(vm)
    # print(len(array))

    return render(request,'no_tags.html',{"data":array,"now":now, "COUNT":len(array), "TOTAL":vms.count()})












def getDeallocatedInstances(request):
    mongocollection = "vms"
    client = MongoClient(mongoserver)
    db = client[mongodb]
    collection = db[mongocollection]
    vms = collection.find({ "displayStatus": {"$ne": "VM running"}})
    vmsdealoc = vms.count()
    vmstotal = collection.find().count()
    return  render(request, 'instances.html',{"active":"vms","menu": menu,'title':title, 'vms':vms,"statistic":{"vmsdealoc":vmsdealoc, "vmstotal":vmstotal}})
#
# def getTags(request):
#     nuvem = az(az_appid, az_dn, az_name,az_passwd,az_tenant,az_subscription)
#     nuvem.getVmsList()
#     return render(request, 'azure_tags.html',{})
def vms2(request):
    mongocollection = "vms"
    client = MongoClient(mongoserver)
    db = client[mongodb]
    collection = db[mongocollection]
    vms = collection.find({ "displayStatus": {"$ne": "VM running"}})
    vmsdealoc = vms.count()
    vmstotal = collection.find().count()
    return  render(request, 'instances.html',{"active":"vms","menu": menu,'title':title, 'vms':vms,"statistic":{"vmsdealoc":vmsdealoc, "vmstotal":vmstotal}})
    # return render(request,'azure_vms2.html',{})