#!/usr/bin/env python
#  coding=utf-8
import argparse, os, threading, datetime
from argparse import Namespace
import json
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

    def collectVmsFromAzureThread(self):
        print("thread Start")
        azure = azsdk(az_appid, az_dn, az_name, az_passwd, az_tenant, az_subscription)
        client = MongoClient(mongoserver)
        db = client[mongodb]
        collection = db['vms']
        # collection.drop()
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
        return False

    def collectVmsFromAzure(self):
        t = threading.Thread(target=self.collectVmsFromAzureThread)
        t.start()
        return False

    def updateDisksTags(self, server, base, collection):
        # timefilter = "last"
        client = MongoClient(server)
        db = client[base]
        collection = db[collection]
        try:
            col_datetimes = collection.find().distinct("datetime")
            datearray = []
            datearraycounter = 1
            for date in col_datetimes:
                array = []
                array.append(str(datetime.datetime.strptime(date, "%Y%m%d%H%M%S")))
                array.append(datearraycounter)
                array.append(date)
                datearray.append(array)
                datearraycounter = datearraycounter + 1
                print(date)
                print(str(datetime.datetime.strptime(date, "%Y%m%d%H%M%S")))
            vms = collection.find({"datetime": max(col_datetimes)})
            # col_datetime_human = datetime.datetime.strptime(max(col_datetimes), "%Y%m%d%H%M%S")
        except ValueError as err:
            print(err)
        disks = []
        disks_ok = []
        disks_nok = []
        for vm in vms:
            if vm.get("vmname"):
                if vm.get("rgname"):
                    if vm.get("disk"):
                        if vm.get("disk").get("os").get("type") == "unmanaged":
                            print(vm.get("rgname") + "/" + vm.get("vmname") + " os_disk unmanaged")
                        else:
                            if vm.get("disk").get("os").get("tags") is not None:
                                if "billing" in vm.get("disk").get("os").get("tags"):
                                    print(vm.get("rgname") + "/" + vm.get("vmname") + " os_disk OK")
                                    disks_ok.append({
                                        "vmname": vm.get("vmname"),
                                        "rgname": vm.get("rgname"),
                                        "vmid": vm.get("ID"),
                                        "diskid": vm.get("disk").get("os").get("id")
                                    })
                                else:
                                    print(vm.get("rgname") + "/" + vm.get("vmname") + " os_disk NOK")
                                    disks_nok.append({
                                        "vmname": vm.get("vmname"),
                                        "rgname": vm.get("rgname"),
                                        "vmid": vm.get("ID"),
                                        "diskid": vm.get("disk").get("os").get("id")
                                    })
                            else:
                                print(vm.get("rgname") + "/" + vm.get("vmname") + " os_tag None")
                        for datadisk in vm.get("disk").get("data"):
                            if datadisk.get("type") == "unmanaged":
                                print(vm.get("rgname") + "/" + vm.get("vmname") + " data_disk unmanaged")
                            else:
                                if datadisk.get("tags") is not None:
                                    if "billing" in datadisk.get("tags"):
                                        print(vm.get("rgname") + "/" + vm.get("vmname") + " data_disk OK")
                                        disks_ok.append({
                                            "vmname": vm.get("vmname"),
                                            "rgname": vm.get("rgname"),
                                            "vmid": vm.get("ID"),
                                            "diskid": datadisk.get("id")
                                        })
                                    else:
                                        print(
                                            vm.get("rgname") + "/" + vm.get("vmname") + " data_disk NOK")
                                        disks_nok.append({
                                            "vmname": vm.get("vmname"),
                                            "rgname": vm.get("rgname"),
                                            "vmid": vm.get("ID"),
                                            "diskid": datadisk.get("id")
                                        })
                                else:
                                    print(vm.get("rgname") + "/" + vm.get("vmname") + " data_tags None")
                    else:
                        print(vm.get("rgname") + "/" + vm.get("vmname") + " disk Error")
                else:
                    print(vm.get("rgname") + "/" + vm.get("vmname") + " rgname Error")
            else:
                print(vm.get("rgname") + "/" + vm.get("vmname") + " vmname Error")
        disks.append({
            "OK": disks_ok,
            "NOK": disks_nok
        })
        print(disks)

    def getdatafrombase(self, server, base, collection, timefilter="last"):
        client = MongoClient(server)
        db = client[base]
        collection = db[collection]
        try:
            col_datetimes = collection.find().distinct("datetime")
            datearray = []
            datearraycounter = 1
            for date in col_datetimes:
                array = []
                array.append(str(datetime.datetime.strptime(date, "%Y%m%d%H%M%S")))
                array.append(datearraycounter)
                array.append(date)
                datearray.append(array)
                datearraycounter = datearraycounter + 1
                print(date)
                print(str(datetime.datetime.strptime(date, "%Y%m%d%H%M%S")))

            if timefilter == "last":
                print("last")
                # vms = collection.find({"state": {"$ne": "PowerState/running"}, "datetime": max(col_datetimes)})
                vms = collection.find({"datetime": max(col_datetimes)})
                col_datetime_human = datetime.datetime.strptime(max(col_datetimes), "%Y%m%d%H%M%S")


            else:
                print(timefilter)
                col_datetime_human = datetime.datetime.strptime(timefilter, "%Y%m%d%H%M%S")
                vms = collection.find({"datetime": timefilter, "state": {"$ne": "PowerState/running"}})
                # vms = collection.find({"datetime": timefilter})
                # datearray = False
                # col_datetime = collection.distinct("datetime")
                # return False
        except ValueError as err:
            print(err)
        for vm in vms:
            print(vm)
        # return  False


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
            # cloud.getdatafrombase(mongoserver, mongodb, "vms")
            cloud.updateDisksTags(mongoserver, mongodb, "vms")
            # cloud.updateDisksTags
