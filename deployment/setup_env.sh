# retrieve variables from .env file
export $(egrep -v '^#' .env | xargs)

LOCATION=westeurope

# log in to Azure with service principal
az login --service-principal --username ${AZURE_CLIENT_ID} --password ${AZURE_CLIENT_CERT_NAME} --tenant ${AZURE_TENANT_ID}
az account set --subscription ${AZURE_SUBSCRIPTION_ID}
az config set defaults.group=${AZURE_RESOURCE_GROUP} defaults.location=${LOCATION}

# create resource group
az group create -n ${AZURE_RESOURCE_GROUP}

# create container registry
az acr create --name ${AZURE_RESOURCE_GROUP} --sku Standard --admin-enabled true

# create app service plan
az appservice plan create --name ${AZURE_RESOURCE_GROUP} --resource-group ${AZURE_RESOURCE_GROUP} --location westeurope \
 --number-of-workers 1 --sku S1 --is-linux