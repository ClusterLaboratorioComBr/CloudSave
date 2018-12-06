#!/usr/bin/env python
#  coding=utf-8
import argparse, os, threading, datetime
from argparse import Namespace

from azuresdk import AzureSdk as azsdk
from pymongo import MongoClient

az_appid: str = os.environ['AZ_APPID']
az_dn: str = os.environ['AZ_DISPLAYNAME']
az_name: str = os.environ['AZ_NAME']
az_passwd: str = os.environ['AZ_PASSWD']
az_tenant: str = os.environ['AZ_TENANT']
az_subscription: str = os.environ['AZ_SUBSCRIPTION']
mongoserver: str = os.environ['MONGOSERVER']
mongodb: str = os.environ['MONGODB']

parser = argparse.ArgumentParser(description='CloudSave Maintenance Console')
parser.add_argument('--cron', action='store_true', help='Run all the scheduled tasks which are daily.')
parser.add_argument('--tags', action='store_true',
                    help='Update the disk tags of a virtual machine with all the tags from the virtual machine')
parser.parse_args([])
args: parser = parser.parse_args()


# exit(1)

class CloudSave:
    def __init__(self):
        self.now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # def collectVmsFromAzureThread(self):
    #     print("thread Start")
    #     nuvem = az(az_appid, az_dn, az_name, az_passwd, az_tenant, az_subscription)
    #     client = MongoClient(mongoserver)
    #     db = client[mongodb]
    #     collection = db['vms']
    #     print("Drop collection vms in " + mongodb + " database")
    #     collection.drop()
    #     retorno = nuvem.getVmsList()
    #     for data in retorno:
    #         try:
    #             print("Collecting vms in " + mongodb + " database")
    #             LOG_id = collection.insert_one(data)
    #         except ValueError:
    #             print("Fail to write data to database.")
    #         else:
    #             print(LOG_id)

    def collectVmsFromAzureThread(self):
        print("thread Start")
        azure = azsdk(az_appid, az_dn, az_name, az_passwd, az_tenant, az_subscription)
        client = MongoClient(mongoserver)
        db = client[mongodb]
        collection = db['vms']
        # print("Drop collection vms in " + mongodb + " database")
        # collection.drop()
        # data=azure.getVmDetail("vmname","rgname",now)
        #
        # return False
        vmlist = azure.getAllVms()
        for vm in vmlist:
            data = azure.getVmDetail(vm['vmname'], vm['rgname'], self.now)
            if data is not False:
                try:
                    print(f"Pushing VMS to {mongodb} database")
                    LOG_id = collection.insert_one(data)
                except ValueError:
                    print("Fail to write data to database.")
                else:
                    print(LOG_id)
        # print(self.now)
        return False

    def collectVmsFromAzure(self):
        # print("thread")
        t = threading.Thread(target=self.collectVmsFromAzureThread)
        t.start()
        # while t.is_alive():
        #     print("Thread rodando")
        #     time.sleep(5)
        # return render(request, 'index.html', {"active": "collect", "menu": menu, 'title': title})
        return False

    @property
    def updateDisksTags(self):
        # TODO Implement the tag pusher to disk resources at azure
        print("Update disk tags")
        azure = azsdk(az_appid, az_dn, az_name, az_passwd, az_tenant, az_subscription)
        client = MongoClient(mongoserver)
        db = client[mongodb]
        collection = db['vms']
        # print("Drop collection vms in " + mongodb + " database")
        # collection.drop()
        MOC_VMNAME="temp-oracle"
        MOC_RGNAME="az-sandbox"
        # data=azure.getVmDetail(MOC_VMNAME,MOC_RGNAME,self.now)
        # print(data)
        # print(data['disk']['os']['tags'])
        # for datadisk in data['disk']['data']:
        #     print(datadisk['tags'])
        # # print(data['disk']['data'])
        # vmid = str(azure.getvmid(MOC_VMNAME,MOC_RGNAME))
        # print(vmid)
        print(azure.getresorucedetailbyid(azure.getvmid(MOC_VMNAME,MOC_RGNAME),"vm"))






        #
        # return False
        # azure.getvmdetail3()
        #
        # return False
        # vmlist = azure.getAllVms()

        # for vm in vmlist:
        #     data = azure.getVmDetail(vm['vmname'], vm['rgname'], self.now)
        #     if data is not False:
        #         try:
        #             print(f"Pushing VMS to {mongodb} database")
        #             # print(data)
        #             # LOG_id = collection.insert_one(data)
        #         except ValueError:
        #             print("Fail to write data to database.")
                # else:
                #     print(LOG_id)
            # break
        # print(self.now)
        return False


if __name__ == '__main__':
    class main:
        cloud = CloudSave()
        if args.tags is True and args.cron is True:
            print("Tags and Cron cannot be used at the same time")
            exit(1)
        if args.cron is not None and args.cron:
            cloud.collectVmsFromAzure()
            print(cloud.now)
        if args.tags is not None and args.tags:
            cloud.updateDisksTags
