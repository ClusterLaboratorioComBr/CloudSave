import azurerm
import json
#https://github.com/gbowerman/azurerm
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