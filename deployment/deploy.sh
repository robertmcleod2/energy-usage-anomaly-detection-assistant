# retrieve variables from .env file
export $(egrep -v '^#' .env | xargs)

LOCATION=westeurope

# log in to Azure with service principal
az login --service-principal --username ${AZURE_CLIENT_ID} --password ${AZURE_CLIENT_CERTIFICATE_PATH} --tenant ${AZURE_TENANT_ID}
az account set --subscription ${AZURE_SUBSCRIPTION_ID}
az config set defaults.group=${AZURE_RESOURCE_GROUP} defaults.location=${LOCATION}

# create container registry
az acr login --name ${AZURE_RESOURCE_GROUP}

# get container registry admin username and password, used for creating function app
username=$(az acr credential show -n ${AZURE_RESOURCE_GROUP} --query username | xargs) 
password=$(az acr credential show -n ${AZURE_RESOURCE_GROUP} --query passwords[0].value | xargs) 

# build and push docker image
docker build -t streamlit .
docker image tag streamlit ${AZURE_RESOURCE_GROUP}.azurecr.io/dashboard:latest
docker push ${AZURE_RESOURCE_GROUP}.azurecr.io/dashboard:latest

# create web app
az webapp create --name ${AZURE_RESOURCE_GROUP}app --plan ${AZURE_RESOURCE_GROUP} --resource-group  ${AZURE_RESOURCE_GROUP} \
 --container-image-name ${AZURE_RESOURCE_GROUP}.azurecr.io/dashboard:latest \
 --container-registry-user ${username} --container-registry-password ${password} --https-only true

# set env variables
az webapp config appsettings set --resource-group  ${AZURE_RESOURCE_GROUP} --name ${AZURE_RESOURCE_GROUP}app \
 --settings OPENAI_API_KEY=${OPENAI_API_KEY} LANGCHAIN_TRACING_V2="true" LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}  \
 STREAMLIT_PASSWORD=${STREAMLIT_PASSWORD}
    
az webapp restart --resource-group  ${AZURE_RESOURCE_GROUP} --name ${AZURE_RESOURCE_GROUP}app

