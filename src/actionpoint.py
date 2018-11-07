#!/usr/bin/env python
#  coding=utf-8
from crontab import CronTab
from src.azuresdk import AzureSdk as az
from src.config import Config as configjson
import paramiko, argparse, os, datetime
# now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
from time import sleep

pk = "/path/id_rsa"
cloud_available = ['azure']
action_available = ['stop', 'start']
tags_available = ['ActionPointStart', 'ActionPoint', 'ActionPointStop', 'ActionPointCustom', 'ActionPointUser']
az_ap_credentials = {
    "az_appid": os.environ['AZ_APPID'],
    "az_dn": os.environ['AZ_DISPLAYNAME'],
    "az_name": os.environ['AZ_NAME'],
    "az_passwd": os.environ['AZ_PASSWD'],
    "az_tenant": os.environ['AZ_TENANT'],
    "az_subscription": os.environ['AZ_SUBSCRIPTION']
}
mongoserver = os.environ['MONGOSERVER']
mongodb = os.environ['MONGODB']
cronupdate_data = {
    "tabfile": "/path/tabfile",
    "interpreter": "/path/bin/python",
    "procedure": "/path/actionpoint.py"
}


# configurations = configjson(jsonpath)
# configurations.atualizaJson("chave","valor")
# configurations.delData("chave")
# exit(1)

class ActionPoint:
    def __init__(self, azure, pk):
        self.azure = azure
        self.pk = pk

    def updateCron(self, tabfile, python, command):
        # https://pypi.org/project/python-crontab/
        cron = CronTab(tabfile=tabfile)
        cron.remove_all()
        cronline = " root " + python + " " + command + " --updatecron"
        job = cron.new(command=cronline)
        job.setall("0 16 * * *")
        # job.user = "root"
        for vm in self.azure.getAllVms():
            # if vm['vmname'] == "az-us2-ActionPoint":
            tags = self.checkTags(vm['vmname'], vm['rgname'])
            if tags is not False:
                self.azure.getVmId(vm['vmname'], vm['rgname'])
                if str(tags['ActionPoint']).lower() == "True".lower():
                    if (str(tags['ActionPointStart']).lower() != "False".lower()):
                        cronline = " root " + python + " " + command + " --cloud azure --action start --id " + self.azure.getVmId(
                            vm['vmname'], vm['rgname'])
                        job = cron.new(command=cronline)
                        job.setall(tags['ActionPointStart'])
                        # job.user="root"
                    if (str(tags['ActionPointStop']).lower() != "False".lower()):
                        cronline = " root " + python + " " + command + " --cloud azure --action stop --id " + self.azure.getVmId(
                            vm['vmname'], vm['rgname'])
                        job = cron.new(command=cronline)
                        job.setall(tags['ActionPointStop'])
                        # job.user = "root"
        cron.write()

    def stopAzure(self, vmname, rgname):
        return self.azure.stopVm(vmname, rgname)

    def startAzure(self, vmname, rgname):
        return self.azure.startVm(vmname, rgname)

    def runCustom(self, custom, user, vmname, rgname, action):
        k = paramiko.RSAKey.from_private_key_file(self.pk)
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        vmip = self.getVmIp(vmname, rgname)
        if vmip is not False:
            c.connect(hostname=vmip, username=user, pkey=k)
            commands = [custom + " " + action]
            for command in commands:
                stdin, stdout, stderr = c.exec_command(command)
                outcode = stdout.read()
                errcode = stderr.read()
                exitcode = stdout.channel.recv_exit_status()
                # print(str(outcode).replace("\\n","\n"))
                self.log()
                if exitcode != 0:
                    self.log("STDOUT")
                    self.log(rgname + "/" + vmname + " " + user + ":" + custom + " " + str(outcode).replace("\\n",
                                                                                                            "\n").replace(
                        "\\t", "\t"))
                    self.log("STDERR")
                    self.log(rgname + "/" + vmname + " " + user + ":" + custom + " " + str(errcode).replace("\\n",
                                                                                                            "\n").replace(
                        "\\t", "\t"))
                    c.close()
                    return False
            c.close()
            if exitcode == 0:
                return True
            else:
                return False

    def testShhIsAlive(self, user, vmname, rgname, counter):
        countdown = 0
        key = paramiko.RSAKey.from_private_key(self.pk)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        vmip = self.getVmIp(vmname, rgname)
        if vmip is not False:
            while True:
                client.connect(hostname=vmip, username=user, pkey=key, auth_timeout=5, timeout=7)
                commands = ["uptime"]
                for command in commands:
                    stdin, stdout, stderr = client.exec_command(command)
                    if stdout.channel.recv_exit_status() == 0:
                        client.close()
                        return True
                if countdown == counter:
                    client.close()
                    return False
                self.log("counter=" + counter + " countdown=" + countdown + " command=" + command)
                sleep(1)
                countdown = countdown + 1

    def checkTags(self, vmname, rgname):
        tags = self.azure.getVmTags(vmname, rgname)
        if tags == False:
            return False
        else:
            for tag in tags_available:
                if tag not in tags:
                    return False
                else:
                    return tags

    def getVmIp(self, vmname, rgname):
        vmip = self.azure.getVmIp(vmname, rgname)
        if vmip is not False:
            return vmip
        else:
            return False

    def log(self, message):
        print(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " " + str(message))


parser = argparse.ArgumentParser(description='ActionPoint')
parser.add_argument('--id', action='store', help='Id of the instance in the cloud.')
parser.add_argument('--updatecron', action='store_true', help='Update cron with data fro mthe cloud.')
parser.add_argument('--cloud', action='store', help='Name of the cloud provider, azure/aws/gcp.')
parser.add_argument('--action', action='store', help='Action to stop or start virtual machine')
parser.parse_args([])
args = parser.parse_args()
# setting options availability
if args.id is not None:
    args_id = True
else:
    args_id = False
if args.action is not None:
    args_action = True
else:
    args_action = False
if args.cloud is not None:
    args_cloud = True
else:
    args_cloud = False
if args.updatecron:
    args_cron = True
else:
    args_cron = False
azure = az(
    az_ap_credentials['az_appid'],
    az_ap_credentials['az_dn'],
    az_ap_credentials['az_name'],
    az_ap_credentials['az_passwd'],
    az_ap_credentials['az_tenant'],
    az_ap_credentials['az_subscription'])
ap = ActionPoint(azure, pk)
# Testing if id or cloud is setted at the same time as updatecron
if (args_cloud == True or args_id == True) and args_cron == True:
    # print("Cannot use id or cloud with updatecron option")
    ap.log("Cannot use id or cloud with updatecron option")
    exit(1)
if args_cron:
    ap.updateCron(
        cronupdate_data['tabfile'],
        cronupdate_data['interpreter'],
        cronupdate_data['procedure']
    )
else:
    # Testing if an argument is missing
    if (args_cloud is not True or args_id is not True or args_action is not True):
        # print("Id, action and cloud must be present")
        ap.log("Id, action and cloud must be present")
        exit(1)
    else:
        # Split vmid into vmname, resource group and subscription
        data = args.id.split("/")
        vmdata = {
            "subscription": str(data[2]),
            "resourcegroup": data[4],
            "vmname": data[8]
        }
        # Test and get the tags from the VM
        tags = ap.checkTags(vmdata['vmname'], vmdata['resourcegroup'])
        if tags == False:
            # print("tag missing")
            ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " tag missing.")
            exit(1)
        else:
            # print(tags)
            ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " " + str(tags))
        # Check if the cloud option is available
        if args.cloud in cloud_available:
            # Testing if action is available
            if args.action in action_available:
                # Start method for azure
                if (args.cloud == "azure" and args.action == "start"):
                    # check if the ActionPoint is enabled for the virtual machine
                    if (str(tags['ActionPoint']).lower() == "True".lower() and str(
                            tags['ActionPointStart']).lower() != "False".lower()):
                        # Check if custom command is enabled
                        # custom = ap.getCustomAzure(tags['ActionPointCustom'])
                        # if custom is not False:
                        if str(tags['ActionPointCustom']).lower() != "False".lower():
                            # Run start for VM
                            if ap.startAzure(vmdata['vmname'], vmdata['resourcegroup']):
                                sleep(600)
                                # Run custom script and wait for return
                                if ap.runCustom(tags['ActionPointCustom'], tags['ActionPointUser'], vmdata['vmname'],
                                                vmdata['resourcegroup'], "start"):
                                    # print("Custom script executed with success")
                                    ap.log(vmdata['resourcegroup'] + "/" + vmdata[
                                        'vmname'] + " Custom script executed with success.")
                                else:
                                    # print("Custom script failed")
                                    ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " Custom script failed.")
                                    exit(1)
                            else:
                                # print("Fail to start")
                                ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " Fail to start.")
                                exit(1)
                        else:
                            # Run start method without custom script
                            # print(args.id + " has no custom method")
                            ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " has no custom method.")
                            if not ap.startAzure(vmdata['vmname'], vmdata['resourcegroup']):
                                # print("fail to start")
                                ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " fail to start.")
                                exit(1)
                    else:
                        # Do nothig because ActionPoint is disabled
                        # print(args.id + " is disable for action")
                        ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " is disable for action.")
                        exit(1)
                # stop method for azure
                if (args.cloud == "azure" and args.action == "stop"):
                    # check if the ActionPoint is enabled for the virtual machine
                    if (str(tags['ActionPoint']).lower() == "True".lower() and str(
                            tags['ActionPointStop']).lower() != "False".lower()):
                        # Check if custom command is enabled
                        if str(tags['ActionPointCustom']).lower() != "False".lower():
                            # Run custom script and wait for return
                            if ap.runCustom(tags['ActionPointCustom'], tags['ActionPointUser'], vmdata['vmname'],
                                            vmdata['resourcegroup'], "stop"):
                                # print("Custom script executed with success")
                                ap.log(vmdata['resourcegroup'] + "/" + vmdata[
                                    'vmname'] + " Custom script executed with success.")
                                # Stop vm if custom script exited with success
                                ap.stopAzure(vmdata['vmname'], vmdata['resourcegroup'])
                            else:
                                # Log error if custom script do not exit with success
                                # print("Custom script failed")
                                ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " Custom script failed.")
                                exit(1)
                        else:
                            # Run stop on azure without run custom script
                            # print(args.id + " has no custom method")
                            ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " has no custom method.")
                            ap.stopAzure(vmdata['vmname'], vmdata['resourcegroup'])
                    else:
                        # print(args.id + " is disabled for action")
                        ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " is disabled for action.")
                        exit(1)
            else:
                # print("Action \"" + args.action + "\" is not available.")
                ap.log(vmdata['resourcegroup'] + "/" + vmdata[
                    'vmname'] + " Action \"" + args.action + "\" is not available.")
                exit(1)
        else:
            # print("cloud \"" + args.cloud + "\" is not available.")
            ap.log(vmdata['resourcegroup'] + "/" + vmdata['vmname'] + " cloud \"" + args.cloud + "\" is not available.")
            exit(1)
