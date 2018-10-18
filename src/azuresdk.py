import os
import traceback
import azurerm
import json
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
                array.append({"vmname":vm, "rgname":rg})
        return array
    def getVmDetail(self,vmname,rgname,datetime):
        print(rgname + "/" + vmname)
        try:
            vm = self.compute_client.virtual_machines.get(resource_group_name=rgname, vm_name=vmname)
        except CloudError as err:
            print("Fail to get virtual machine details")
            print(err)
            return False
        try:
            vmi = self.compute_client.virtual_machines.instance_view(resource_group_name=rgname, vm_name=vmname)
        except CloudError as err:
            print("Fail to get virtual machine instance")
            print(err)
            return False
        for interface in vm.network_profile.network_interfaces:
            name = " ".join(interface.id.split('/')[-1:])
            sub = "".join(interface.id.split('/')[4])
            vmnet=self.network_client.network_interfaces.get(sub, name)
            for ip in vmnet.ip_configurations:
                nicip=ip.private_ip_address
                nicvnet=str(ip.subnet.id.split('/')[8])
                nicsubnet=str(ip.subnet.id.split('/')[10])
                nicname=vmnet.name
                nicmac=vmnet.mac_address
                if vmnet.network_security_group is not None:
                    nicnsg = vmnet.network_security_group.id
                else:
                    nicnsg = vmnet.network_security_group
                niclocation=vmnet.location
                nicpublic=ip.public_ip_address
        location = vm.location
        size = vm.hardware_profile.vm_size
        if vm.availability_set is not None:
            avset = vm.availability_set.id
        else:
            avset = vm.availability_set
        state = vmi.statuses[1].code
        statetime = vmi.statuses[0].time
        if vm.storage_profile.image_reference is not None:
            vmimage = vm.storage_profile.image_reference.id
        else:
            vmimage = None
        osdiskname=vm.storage_profile.os_disk.name
        osdisksize=vm.storage_profile.os_disk.disk_size_gb
        osdiskcache = vm.storage_profile.os_disk.caching
        if vm.storage_profile.os_disk.managed_disk is not None:
            osdisktype=vm.storage_profile.os_disk.managed_disk.storage_account_type
            datadisks = []
            for datadisk in vm.storage_profile.data_disks:
                datadisks.append({
                    "name": datadisk.name,
                    "size": datadisk.disk_size_gb,
                    "type": datadisk.managed_disk.storage_account_type,
                    "cache": datadisk.caching,
                    "lun": datadisk.lun
                })
        else:
            osdisktype="windows"
            # osdisktype=vm.storage_profile.os_disk.managed_disk
            datadisks = []
            for datadisk in vm.storage_profile.data_disks:
                datadisks.append({
                    "name": datadisk.name,
                    "size": datadisk.disk_size_gb,
                    "type": "windows",
                    # "type": datadisk.managed_disk.storage_account_type,
                    "cache": datadisk.caching,
                    "lun": datadisk.lun
                })


        network = {
                "name":nicname,
                "subnet":nicsubnet,
                "ip":nicip,
                "vnet":nicvnet,
                "location":niclocation,
                "public":nicpublic,
                "mac":nicmac,
                "sg":nicnsg
            }
        disk = {
                "os":{
                    "name":osdiskname,
                    "size":osdisksize,
                    "type":osdisktype,
                    "cache":osdiskcache
                },
                "data": datadisks
            }
        tags = vm.tags
        data = {
            "vmname":vmname,
            "rgname":rgname,
            "location":location,
            "size":size,
            "avset":avset,
            "state":state,
            "statetime":statetime,
            "vmimage":vmimage,
            "network":network,
            "disk":disk,
            "tags":tags,
            "datetime":datetime
        }
        print(data)
        return data

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





class Azclass:
    def __init__(self,appid, dn, name, passwd, tenant, subscription):
        # self.appid = config.getDados("AZ_APPID")
        # self.dn = config.getDados("AZ_DISPLAYNAME")
        # self.name = config.getDados("AZ_NAME")
        # self.passwd = config.getDados("AZ_PASSWD")
        # self.tenant = config.getDados("AZ_TENANT")
        # self.subscription = config.getDados("AZ_SUBSCRIPTION")
        self.appid = appid
        self.dn = dn
        self.name = name
        self.passwd = passwd
        self.tenant = tenant
        self.subscription = subscription
        try:
            self.access_token = azurerm.get_access_token(self.tenant, self.appid, self.passwd)
            # return True

        except ValueError:
            print("Azure login error")
            # return False
    def getRegion(self):
        try:
            location = azurerm.list_locations(self.access_token, self.subscription)
            array = []
            for locale in location['value']:
                array2 = []
                array2.append(locale['displayName'])
                array2.append(locale['name'])
                array.append(array2)
            return array
        except ValueError:
            print("Fail to get Locations list")
            return  False

    def getResourceGroup(self):
        try:
            resource_groups = azurerm.list_resource_groups(self.access_token, self.subscription)
            array = []
            for rg in resource_groups['value']:
                #print(rg["name"] + ', ' + rg['location'] + ', ' + rg['properties']['provisioningState'])
                array2 = []
                array2.append(rg["name"])
                array2.append(rg['location'])
                array2.append(rg['properties']['provisioningState'])
                array.append(array2)
            return array

        except ValueError:
            print("Fail to get list of resource groups")
            return False

    def getVnet(self,region):
        try:
            vnets = azurerm.list_vnets(self.access_token, self.subscription)
            array = []
            for vnet in vnets['value']:
                if vnet['location'] != region:
                    continue
                else:
                    for subnet in vnet['properties']['subnets']:
                        #print(subnet['name'] + ', ' + vnet['name'] + ', vnetLocation=' + vnet['location'] + ', ' +
                        #      subnet['properties']['addressPrefix'] + ', ' + subnet['properties']['provisioningState'])
                        array2 = []
                        array2.append(subnet['name'])
                        array2.append(vnet['name'])
                        array2.append(vnet['location'])
                        array2.append(subnet['properties']['addressPrefix'])
                        array2.append(subnet['properties']['provisioningState'])
                        array2.append(subnet['id'])
                        array.append(array2)
            return array

        except ValueError:
            print("Fail to get Vnet list")
            return False
    def getImage(self,region):
        try:
            images = azurerm.list_vm_images_sub(self.access_token, self.subscription)
            array = []

            for image in images['value']:
                if image['location'] != region:
                    continue
                else:
                    #print(image['name'] + ', ' + image['location'] + ', ' + str(
                    #    image['properties']['storageProfile']['osDisk']['diskSizeGB']) + ', ' +
                    #      image['properties']['storageProfile']['osDisk']['storageAccountType'])
                    array2 = []
                    array2.append(image['name'])
                    array2.append(image['location'])
                    array2.append(image['properties']['storageProfile']['osDisk']['diskSizeGB'])
                    array2.append(image['properties']['storageProfile']['osDisk']['storageAccountType'])
                    array2.append(image['id'])
                    array.append(array2)
            return array

        except ValueError:
            print("Fail to get image list")
            return False

    def getVmSize(self,region):
        try:
            # https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Compute/locations/{location}/vmSizes?api-version={apiVersion}
            vmsizes = azurerm.do_get(
                "https://management.azure.com/subscriptions/" + self.subscription + "/providers/Microsoft.Compute/locations/" + region + "/vmSizes?api-version=2015-06-15",
                self.access_token)
            array = []
            for vmsize in vmsizes['value']:
                array2 = []
                array2.append(vmsize['memoryInMB'])
                array2.append(vmsize['maxDataDiskCount'])
                array2.append(vmsize['name'])
                array2.append(vmsize['resourceDiskSizeInMB'])
                array2.append(vmsize['osDiskSizeInMB'])
                array2.append(vmsize['numberOfCores'])
                array.append(array2)
            return array
        except ValueError:
            print("Fail to get VmSize for region" + region)
            return  False
    def getDiskType(self,config):
        try:
            array = []
            disktype = config.getData('azure')
            for type in disktype['disktype']:
                array.append(type)
            return array
        except ValueError:
            print("Fail to get list of diskTypes")
            return False
    def getTags(self,config):
        try:
            array = []
            tags = config.getData('azure')
            for tag in tags['tags']:
                array.append(tag)
            return array
        except ValueError:
            print("Fail to get list of diskTypes")
            return False
    def login(self):
        try:
            self.access_token = azurerm.get_access_token(self.tenant, self.appid, self.passwd)
            return True

        except ValueError:
            print("Azure login error")
            return False
    def getOsType(self,config):
        try:
            array = []
            ostypes = config.getData('azure')
            for ostype in ostypes['ostype']:
                array.append(ostype)
            return array
        except ValueError:
            print("Fail to get list of diskTypes")
            return False
    def getAuth(self,config):
        try:
            auth = json.loads(str(config.getData('azure')).replace('\'', '\"'))
            array = []
            array.append(auth['authentication']['user'])
            array.append(auth['authentication']['passwd'])
            return array
        except ValueError:
            print("Fail to get default credentials for virtual machine")
            return  False
    def getDiskCache(self,config):
        try:
            diskcaches = json.loads(str(config.getData('azure')).replace('\'', '\"'))
            array = []
            for diskcache in diskcaches['diskcache']:
                array.append(diskcache)
            return array
        except ValueError:
            print("Fail to get default credentials for virtual machine")
            return  False
    def getVmsListForRb(self,rgname):
        try:
            vms = azurerm.list_vms(self.access_token,self.subscription,rgname)
            array = []
            for vm in vms['value']:
                vmview = azurerm.get_vm_instance_view(self.access_token,self.subscription,rgname,vm['name'])
                # print(vm['name'])
                for statuses in vmview['statuses']:
                    if 'time' in statuses:
                        time = statuses['time']
                    else:
                        code = statuses['code']
                        displayStatus = statuses['displayStatus']
                array.append({
                    "time": time,
                    "code": code,
                    "displayStatus": displayStatus,
                    "vmId": vm['properties']['vmId'],
                    "vmSize": vm['properties']['hardwareProfile']['vmSize'],
                    "id": vm['id'],
                    "resource": rgname,
                    "location": vm['location'],
                    "name": vm['name'],
                })
                print(vm['id'])
            return array
        except ValueError:
            print("Fail to get list of vms")
            return False

    def getVmsList(self):
        rgs = self.getResourceGroup()
        array = []
        for rg in rgs:
            try:
                vms = self.getVmsListForRb(rg[0])
                for vm in vms:
                    # print(vm)
                    array.append(vm)
            except ValueError:
                print("Fail to get vms from recource group " + rg)
        return array