import os
import traceback
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from msrestazure.azure_exceptions import CloudError



#https://github.com/Azure-Samples/virtual-machines-python-manage/blob/master/example.py
#https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-samples-list-images?view=azure-python
#https://github.com/Azure/azure-sdk-for-python
#https://github.com/Azure-Samples/virtual-machines-python-manage


class AzureSdk:
    def __init__(self,appid, dn, name, passwd, tenant, subscription):
        self.appid = appid
        self.dn = dn
        self.name = name
        self.passwd = passwd
        self.tenant = tenant
        self.subscription = subscription
        self.credentials = ServicePrincipalCredentials(
            client_id=self.appid,
            secret=self.passwd,
            tenant=self.tenant
        )
        self.resource_client = ResourceManagementClient(self.credentials, self.subscription)
        self.compute_client = ComputeManagementClient(self.credentials, self.subscription)
        self.network_client = NetworkManagementClient(self.credentials, self.subscription)
    def getRgList(self):
        array = []
        for rg in self.resource_client.resource_groups.list():
            array.append(rg.name)
        return array
    def getVmList(self,rgname):
        array = []
        for vm in self.compute_client.virtual_machines.list(rgname):
            array.append(vm.name)
        return  array
    def getAllVms(self):
        array = []
        for rg in self.getRgList():
            for vm in self.getVmList(rg):
                # print(vm)
                array.append({"vmname":vm, "rgname":rg})
        return array
    def getVmTags(self,vmname,rgname):
        for vm in self.compute_client.virtual_machines.list(rgname):
            if vm.name == vmname:
                if vm.tags == None:
                    return False
                else:
                    return vm.tags
    def getVmIp(self,vmname,rgname):
        for vm in self.compute_client.virtual_machines.list(rgname):
            if vm.name == vmname:
                for interface in vm.network_profile.network_interfaces:
                    name = " ".join(interface.id.split('/')[-1:])
                    sub = "".join(interface.id.split('/')[4])
                    try:
                        thing = self.network_client.network_interfaces.get(sub, name).ip_configurations

                        for x in thing:
                            return x.private_ip_address

                    except:
                        return False
    def stopVm(self,vmname,rgname):
        try:
            dealloc = self.compute_client.virtual_machines.deallocate(rgname, vmname)
            dealloc.wait()
            return True
        except CloudError as e:
            print('Fail to stop ' + str(e))
            return False

    def startVm(self,vmname,rgname):
        try:
            start = self.compute_client.virtual_machines.start(rgname,vmname)
            # start.wait()
            print(start.wait())
            return True
        except CloudError as e:
            print("Fail to start " + str(e))
            return False
    def getVmId(self,vmname,rgname):
        for vm in self.compute_client.virtual_machines.list(rgname):
            if vm.name == vmname:
                return vm.id

    #
    # def getComnputeUsage(self):
    #     import azurerm
    #     import json
    #     access_token = azurerm.get_access_token_from_cli()
    #     subscription_id = azurerm.get_subscription_from_cli()
    #     location = 'westus'
    #     compute_usage = azurerm.get_compute_usage(access_token, subscription_id, location)
    #     print(json.dumps(compute_usage, sort_keys=False, indent=2, separators=(',', ': ')))
