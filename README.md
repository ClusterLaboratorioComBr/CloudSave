# CloudSave

Cloudsave is a web application in container which monitor orphans resources allocated on cloud.

It is helpfull to identify resources allocated which are not in use anymore.

Right now, CloudSave is compatible only with the Azure cloud. Come back in a few weeks for more compatibility.
 
If you wanna run this project you'll need an azure app account.
We recommend an account with specifics rights to access resources from the cloud.
First you'll need a role and then an account with it.
## Create a role on Azure
>ReadAllAndStorage.json
```
  {
    "Name": "ReadAllAndStorage",
    "Actions": [
      "Microsoft.Storage/storageAccounts/listKeys/action",
      "Microsoft.Storage/storageAccounts/read",
      "*/read"
    ],
    "NotActions": [],
    "AssignableScopes": [
      "/subscriptions/0000000000000000000000000000"
    ],
    "Description": "Read resources and Storage",
    "IsCustom": "true"
  }
  ```
>Caution! 
The action "Microsoft.Storage/storageAccounts/listKeys/action" will grant acces to the storage keys. If you don't want acces to the storage account do not add it.

Create the role:
```
az role definition create --role-definition @ReadAllAndStorage.json
```
## Create an app account
```
az ad sp create-for-rbac --role="ReadAllAndStorage" --name "cloudsave" --scopes="/subscriptions/SUBSCRIPTION_ID"
```

## HUB.DOCKER

[clusterlab/cloudsave/](https://hub.docker.com/r/clusterlab/cloudsave/)

## Docker Compose
>*docker-compose.yml*
```
version: '3.3'
services:
  cloudsave-db:
    image: 'bitnami/mongodb:3.6'
    restart: always
  cloudsave-web:
    image: 'clusterlab/cloudsave:latest'
    restart: always
    environment:
      -  MONGOSERVER=mongodb://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  MONGODB=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  AZ_APPID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  AZ_DISPLAYNAME=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  AZ_NAME=http://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  AZ_PASSWD=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  AZ_TENANT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      -  AZ_SUBSCRIPTION=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ports:
      - "8383:8000"
    links:
      - cloudsave-db
    depends_on:
      - cloudsave-db
```

[http://localhost:8383](http://localhost:8383)



>Contact: [devops@clusterlab.com.br](mailto:devops@clusterlab.com.br)