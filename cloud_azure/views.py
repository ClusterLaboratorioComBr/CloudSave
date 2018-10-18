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
def getDeallocatedInstances(request):
    mongocollection = "vms"
    client = MongoClient(mongoserver)
    db = client[mongodb]
    collection = db[mongocollection]
    vms = collection.find({ "displayStatus": {"$ne": "VM running"}})
    vmsdealoc = vms.count()
    vmstotal = collection.find().count()
    return  render(request, 'instances.html',{"active":"vms","menu": menu,'title':title, 'vms':vms,"statistic":{"vmsdealoc":vmsdealoc, "vmstotal":vmstotal}})
def collectVmsFromAzure(request):
    # print("thread")
    t = threading.Thread(target=collectVmsFromAzureThread2)
    t.start()
    # while t.is_alive():
    #     print("Thread rodando")
    #     time.sleep(5)
    return render(request, 'index.html', {"active": "collect", "menu": menu, 'title': title})
def collectVmsFromAzureThread():
    print("thread Start")
    nuvem = az(az_appid, az_dn, az_name, az_passwd, az_tenant, az_subscription)
    client = MongoClient(mongoserver)
    db = client[mongodb]
    collection = db['vms']
    print("Drop collection vms in " + mongodb + " database")
    collection.drop()
    retorno = nuvem.getVmsList()
    for data in retorno:
        try:
            print("Collecting vms in " + mongodb + " database")
            LOG_id = collection.insert_one(data)
        except ValueError:
            print("Fail to write data to database.")
        else:
            print(LOG_id)
def collectVmsFromAzureThread2():
    print("thread Start")
    azure = azsdk(az_appid,az_dn,az_name,az_passwd,az_tenant,az_subscription)
    client = MongoClient(mongoserver)
    db = client[mongodb]
    collection = db['vms']
    print("Drop collection vms in " + mongodb + " database")
    # collection.drop()
    # data=azure.getVmDetail("vmname","rgname",now)
    #
    # return False
    vmlist = azure.getAllVms()
    for vm in vmlist:
        data = azure.getVmDetail(vm['vmname'], vm['rgname'],now)
        if data is not False:
            try:
                print("Pushing VMS to " + mongodb + " database")
                LOG_id = collection.insert_one(data)
            except ValueError:
                print("Fail to write data to database.")
            else:
                print(LOG_id)
    return False

def getTags(request):
    nuvem = az(az_appid, az_dn, az_name,az_passwd,az_tenant,az_subscription)
    nuvem.getVmsList()
    return render(request, 'azure_tags.html',{})
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