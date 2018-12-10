import json, azurerm, traceback, os
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from msrestazure.azure_exceptions import CloudError
from azure.mgmt.recoveryservicesbackup import RecoveryServicesBackupClient
from azure.mgmt.recoveryservices import RecoveryServicesClient


# https://github.com/Azure-Samples/virtual-machines-python-manage/blob/master/example.py
# https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-samples-list-images?view=azure-python
# https://github.com/Azure/azure-sdk-for-python
# https://github.com/Azure-Samples/virtual-machines-python-manage


class AzureSdk:
    def __init__(self, appid, dn, name, passwd, tenant, subscription):
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
        self.recoveryservices_client_bkp = RecoveryServicesBackupClient(self.credentials, self.subscription)
        self.recoveryservices_client = RecoveryServicesClient(self.credentials, self.subscription)

    def getRgList(self):
        array = []
        for rg in self.resource_client.resource_groups.list():
            array.append(rg.name)
        return array

    def getVmList(self, rgname):
        array = []
        for vm in self.compute_client.virtual_machines.list(rgname):
            array.append(vm.name)
        return array

    def getAllVms(self):
        array = []
        for rg in self.getRgList():
            for vm in self.getVmList(rg):
                array.append({"vmname": vm, "rgname": rg})
        return array
    def getresourcedetail(self,resourceid):
        resources = self.resource_client.resources.list()
        for resource in resources:
            # print(resource)
            if resource.id is not None:
                if resource.id.lower() == resourceid.lower():
                    return resource
            else:
                return None
            # break
    def getresorucedetailbyid(self,resourceid,type):
        if type == "disk":
            return self.resource_client.resources.get_by_id(resourceid,"2018-09-30")
            # print(resource)
        if type == "vm":
            return self.resource_client.resources.get_by_id(resourceid, "2018-10-01")
            # print(resource)
    def getvmid(self,vmname,rgname):
        vmid = self.compute_client.virtual_machines.get(rgname,vmname)
        return str(vmid.id)
    # def getvmdiskids(self,vmid):
    #     resource = self.compute_client.virtual_machines.

    def getVmDetail(self, vmname, rgname, datetime):
        print(rgname + "/" + vmname)
        try:
            vm = self.compute_client.virtual_machines.get(resource_group_name=rgname, vm_name=vmname)
            # if vm.os_profile.linux_configuration is not None:
            #     print(" linux")
            # if vm.os_profile['windows_configuration'] is not None:
            #     print(vmname + " windows")
            # print(vmname)
            # print(vm.os_profile.linux_configuration)
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
        # if vm.os_profile.linux_configuration is not None:
        #     print(" linux")
        ostype = "unknown"
        if vm.os_profile is not None:
            if vm.os_profile.linux_configuration is not None:
                ostype="linux"
                print(ostype)
        if vm.os_profile is not None:
            if vm.os_profile.windows_configuration is not None:
                ostype = "windows"
                print(ostype)
        # print(vm.os_profile)
        # print(vm.os_profile.linux_configuration)
        for interface in vm.network_profile.network_interfaces:
            name = " ".join(interface.id.split('/')[-1:])
            sub = "".join(interface.id.split('/')[4])
            vmnet = self.network_client.network_interfaces.get(sub, name)
            for ip in vmnet.ip_configurations:
                nicip = ip.private_ip_address
                nicvnet = str(ip.subnet.id.split('/')[8])
                nicsubnet = str(ip.subnet.id.split('/')[10])
                nicname = vmnet.name
                nicmac = vmnet.mac_address
                if vmnet.network_security_group is not None:
                    nicnsg = vmnet.network_security_group.id
                else:
                    nicnsg = vmnet.network_security_group
                niclocation = vmnet.location
                nicpublic = ip.public_ip_address
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
        vmid = vm.id
        osdiskname = vm.storage_profile.os_disk.name
        osdisksize = vm.storage_profile.os_disk.disk_size_gb
        osdiskcache = vm.storage_profile.os_disk.caching
        # print(vm.storage_profile.os_disk.managed_disk.id )
        # print(vmname)

        if vm.storage_profile.os_disk.managed_disk is not None:
            osdiskid = str(vm.storage_profile.os_disk.managed_disk.id)
            if self.getresourcedetail(vm.storage_profile.os_disk.managed_disk.id).tags is not None:
                osdisktags = self.getresourcedetail(vm.storage_profile.os_disk.managed_disk.id).tags
            else:
                osdisktags = ""
                osdiskid = ""
        else:
            osdisktags = ""
            osdiskid = ""
        if vm.storage_profile.os_disk.managed_disk is not None:
            osdisktype = vm.storage_profile.os_disk.managed_disk.storage_account_type
            datadisks = []
            for datadisk in vm.storage_profile.data_disks:
                datadisks.append({
                    "name": datadisk.name,
                    "size": datadisk.disk_size_gb,
                    "type": datadisk.managed_disk.storage_account_type,
                    "cache": datadisk.caching,
                    "lun": datadisk.lun,
                    "tags": self.getresourcedetail(datadisk.managed_disk.id).tags,
                    "id" : str(self.getresourcedetail(datadisk.managed_disk.id).id)
                })
        else:
            osdisktype = "unmanaged"
            # osdisktype=vm.storage_profile.os_disk.managed_disk
            datadisks = []
            for datadisk in vm.storage_profile.data_disks:
                # print(datadisk.vhd.uri)
                print(datadisk)
                datadisks.append({
                    "name": datadisk.name,
                    "size": datadisk.disk_size_gb,
                    "type": osdisktype,
                    # "type": datadisk.managed_disk.storage_account_type,
                    # "tags": self.getresourcedetail(datadisk.managed_disk.id).tags,
                    "tags":"",
                    "cache": datadisk.caching,
                    "lun": datadisk.lun,
                    "id" : datadisk.vhd.uri
                })

        network = {
            "name": nicname,
            "subnet": nicsubnet,
            "ip": nicip,
            "vnet": nicvnet,
            "location": niclocation,
            "public": nicpublic,
            "mac": nicmac,
            "sg": nicnsg
        }
        disk = {
            "os": {
                "name": osdiskname,
                "size": osdisksize,
                "type": osdisktype,
                "cache": osdiskcache,
                "tags": osdisktags,
                "id" : osdiskid
            },
            "data": datadisks
        }
        if vm.tags is not None:
            tags = vm.tags
        else:
            tags = ""
        data = {
            "ID": vmid,
            "ostype": ostype,
            "vmname": vmname,
            "rgname": rgname,
            "location": location,
            "size": size,
            "avset": avset,
            "state": state,
            "statetime": statetime,
            "vmimage": vmimage,
            "network": network,
            "disk": disk,
            "tags": tags,
            "datetime": datetime
        }
        # print(data)
        return data

    def getVmTags(self, vmname, rgname):
        for vm in self.compute_client.virtual_machines.list(rgname):
            if vm.name == vmname:
                if vm.tags == None:
                    return False
                else:
                    return vm.tags

    def getVmIp(self, vmname, rgname):
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

    def stopVm(self, vmname, rgname):
        try:
            dealloc = self.compute_client.virtual_machines.deallocate(rgname, vmname)
            dealloc.wait()
            return True
        except CloudError as e:
            print('Fail to stop ' + str(e))
            return False

    def startVm(self, vmname, rgname):
        try:
            start = self.compute_client.virtual_machines.start(rgname, vmname)
            # start.wait()
            print(start.wait())
            return True
        except CloudError as e:
            print("Fail to start " + str(e))
            return False

    def getVmId(self, vmname, rgname):
        for vm in self.compute_client.virtual_machines.list(rgname):
            if vm.name == vmname:
                return vm.id

    def getBackupProtectedItems(self):
        backup_items = []
        vaults = self.recoveryservices_client.vaults.list_by_subscription_id()
        for vault in vaults:
            rg = vault.id.split('/')[4]
            protecteds = self.recoveryservices_client_bkp.backup_protected_items.list(vault.name, rg)
            for protected in protecteds:
                item = protected.id.split("/")
                protected_subscription = item[2]
                protected_rg = item[4]
                protected_vault = item[8]
                protected_protectionContainers = item[12]
                protected_protectedItems = item[14]
                backup_items.append({
                    "subscription": protected_subscription,
                    "rg": protected_rg,
                    "vault": protected_vault,
                    "protectionContainers": protected_protectionContainers,
                    "protectedItems": protected_protectedItems
                })
                # print("console" + protected)
                # print(protected)
        return backup_items


class Azclass:
    def __init__(self, appid, dn, name, passwd, tenant, subscription):
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
            return False

    def getResourceGroup(self):
        try:
            resource_groups = azurerm.list_resource_groups(self.access_token, self.subscription)
            array = []
            for rg in resource_groups['value']:
                # print(rg["name"] + ', ' + rg['location'] + ', ' + rg['properties']['provisioningState'])
                array2 = []
                array2.append(rg["name"])
                array2.append(rg['location'])
                array2.append(rg['properties']['provisioningState'])
                array.append(array2)
            return array

        except ValueError:
            print("Fail to get list of resource groups")
            return False

    def getVnet(self, region):
        try:
            vnets = azurerm.list_vnets(self.access_token, self.subscription)
            array = []
            for vnet in vnets['value']:
                if vnet['location'] != region:
                    continue
                else:
                    for subnet in vnet['properties']['subnets']:
                        # print(subnet['name'] + ', ' + vnet['name'] + ', vnetLocation=' + vnet['location'] + ', ' +
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

    def getImage(self, region):
        try:
            images = azurerm.list_vm_images_sub(self.access_token, self.subscription)
            array = []

            for image in images['value']:
                if image['location'] != region:
                    continue
                else:
                    # print(image['name'] + ', ' + image['location'] + ', ' + str(
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

    def getVmSize(self, region):
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
            return False

    def getDiskType(self, config):
        try:
            array = []
            disktype = config.getData('azure')
            for type in disktype['disktype']:
                array.append(type)
            return array
        except ValueError:
            print("Fail to get list of diskTypes")
            return False

    def getTags(self, config):
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

    def getOsType(self, config):
        try:
            array = []
            ostypes = config.getData('azure')
            for ostype in ostypes['ostype']:
                array.append(ostype)
            return array
        except ValueError:
            print("Fail to get list of diskTypes")
            return False

    def getAuth(self, config):
        try:
            auth = json.loads(str(config.getData('azure')).replace('\'', '\"'))
            array = []
            array.append(auth['authentication']['user'])
            array.append(auth['authentication']['passwd'])
            return array
        except ValueError:
            print("Fail to get default credentials for virtual machine")
            return False

    def getDiskCache(self, config):
        try:
            diskcaches = json.loads(str(config.getData('azure')).replace('\'', '\"'))
            array = []
            for diskcache in diskcaches['diskcache']:
                array.append(diskcache)
            return array
        except ValueError:
            print("Fail to get default credentials for virtual machine")
            return False

    def getVmsListForRb(self, rgname):
        try:
            vms = azurerm.list_vms(self.access_token, self.subscription, rgname)
            array = []
            for vm in vms['value']:
                vmview = azurerm.get_vm_instance_view(self.access_token, self.subscription, rgname, vm['name'])
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


if __name__ == '__main__':
    class main:
        print("begin")
        nuvem = AzureSdk(os.environ['AZ_APPID'], os.environ['AZ_DISPLAYNAME'], os.environ['AZ_NAME'],
                         os.environ['AZ_PASSWD'], os.environ['AZ_TENANT'], os.environ['AZ_SUBSCRIPTION'])
        nuvem.login()
        retorno = nuvem.getBackupProtectedItems()
        for item in retorno:
            print(item)
