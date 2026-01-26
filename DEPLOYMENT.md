# Azure Deployment Guide

This guide walks through deploying the Data Upload Service to Azure.

## Prerequisites

- Azure subscription
- Azure CLI installed
- GitHub account with repository access
- Git installed locally

## Step 1: Azure Resource Creation

### Option A: Using Azure Portal (GUI)

1. **Create Resource Group**
   - Navigate to Azure Portal
   - Click "Resource groups" → "Create"
   - Name: `data-upload-rg`
   - Region: Choose closest to your users
   - Click "Review + create"

2. **Create Storage Account**
   - Navigate to "Storage accounts" → "Create"
   - Resource group: `data-upload-rg`
   - Storage account name: `datauploadstorage123` (must be globally unique)
   - Region: Same as resource group
   - Performance: Standard
   - Redundancy: LRS (or your preference)
   - Click "Review + create"

3. **Create Function App**
   - Navigate to "Function App" → "Create"
   - Resource group: `data-upload-rg`
   - Function App name: `data-upload-func-app` (must be globally unique)
   - Publish: Code
   - Runtime stack: Python
   - Version: 3.10
   - Region: Same as resource group
   - Operating System: Linux
   - Plan type: Consumption (Serverless)
   - Click "Review + create"

### Option B: Using Azure CLI (Command Line)

```bash
# Login to Azure
az login

# Set variables (customize these)
RESOURCE_GROUP="data-upload-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="datauploadstorage123"
FUNCTION_APP="data-upload-func-app"

# Create Resource Group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Storage Account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux
```

## Step 2: Configure Function App Settings

The Function App needs the storage connection string:

### Via Azure Portal
1. Go to your Function App
2. Settings → Configuration
3. The `AzureWebJobsStorage` should already be configured
4. Click "Save"

### Via Azure CLI
```bash
# Get storage connection string
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv)

# Update Function App settings
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "AzureWebJobsStorage=$STORAGE_CONNECTION"
```

## Step 3: Configure GitHub for CI/CD

### Create Azure Service Principal

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)

# Create service principal
az ad sp create-for-rbac \
  --name "github-actions-data-upload" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth
```

This outputs JSON credentials. Copy the entire JSON output.

### Get Function App Publish Profile

1. Go to Azure Portal → Your Function App
2. Click "Get publish profile" in the Overview page
3. Download the `.PublishSettings` file
4. Open it and copy the entire contents

### Configure GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `AZURE_CREDENTIALS`: Paste the JSON from service principal
   - `AZURE_FUNCTIONAPP_NAME`: Your function app name (e.g., `data-upload-func-app`)
   - `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`: Paste the publish profile content

## Step 4: Deploy

### Automatic Deployment via GitHub Actions

1. Push code to `main` branch:
   ```bash
   git push origin main
   ```

2. GitHub Actions will automatically:
   - Run tests
   - Deploy to Azure Functions

3. Monitor deployment:
   - Go to GitHub repository → Actions tab
   - Watch the workflow run

### Manual Deployment

If you prefer manual deployment:

```bash
# Install Azure Functions Core Tools (if not installed)
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4

# Ubuntu/Debian
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Windows (via npm)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Deploy
func azure functionapp publish $FUNCTION_APP
```

## Step 5: Verify Deployment

### Test the Function

1. Get the function URL and key:
   ```bash
   # Get function URL
   FUNCTION_URL=$(az functionapp function show \
     --name $FUNCTION_APP \
     --resource-group $RESOURCE_GROUP \
     --function-name UploadFunction \
     --query invokeUrlTemplate \
     --output tsv)
   
   # Get function key
   FUNCTION_KEY=$(az functionapp function keys list \
     --name $FUNCTION_APP \
     --resource-group $RESOURCE_GROUP \
     --function-name UploadFunction \
     --query default \
     --output tsv)
   
   echo "Function URL: $FUNCTION_URL"
   echo "Function Key: $FUNCTION_KEY"
   ```

2. Test with a sample file:
   ```bash
   # Create test JSON file
   echo '{"test": "data"}' > test.json
   
   # Upload
   curl -X POST \
     -H "x-functions-key: $FUNCTION_KEY" \
     -F "file=@test.json" \
     $FUNCTION_URL
   ```

### Verify Storage

1. **Check Blob Storage**:
   ```bash
   az storage blob list \
     --account-name $STORAGE_ACCOUNT \
     --container-name uploads \
     --output table
   ```

2. **Check Table Storage**:
   ```bash
   az storage entity query \
     --account-name $STORAGE_ACCOUNT \
     --table-name uploadmetadata \
     --output table
   ```

## Step 6: Monitor and Manage

### View Logs

```bash
# Stream logs
az webapp log tail \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP
```

### Enable Application Insights (Recommended)

1. In Azure Portal, go to your Function App
2. Application Insights → "Turn on Application Insights"
3. Create new or use existing
4. This enables detailed monitoring and analytics

## Cost Estimation

Using Azure Consumption Plan (Serverless):
- **Function App**: Free for first 1M executions/month, then $0.20 per million
- **Storage Account**: 
  - Blob: ~$0.018 per GB/month
  - Table: ~$0.07 per 10K transactions
- **Bandwidth**: First 5 GB/month free, then $0.087 per GB

**Example**: For 10,000 uploads/month with 1MB avg file size:
- Functions: Free (under 1M)
- Blob Storage: ~$0.18
- Table Storage: ~$0.007
- **Total**: ~$0.20/month

## Security Best Practices

1. **Enable HTTPS only**:
   ```bash
   az functionapp update \
     --name $FUNCTION_APP \
     --resource-group $RESOURCE_GROUP \
     --set httpsOnly=true
   ```

2. **Configure CORS** (if needed for web apps):
   ```bash
   az functionapp cors add \
     --name $FUNCTION_APP \
     --resource-group $RESOURCE_GROUP \
     --allowed-origins https://yourdomain.com
   ```

3. **Rotate function keys regularly**
4. **Use managed identities** for production
5. **Enable diagnostic logging**

## Troubleshooting

### Deployment fails
- Check GitHub Actions logs for errors
- Verify Azure credentials in GitHub Secrets
- Ensure Function App name is correct

### Function returns 500 error
- Check Function App logs in Azure Portal
- Verify `AzureWebJobsStorage` is configured
- Check Application Insights for detailed errors

### Cannot upload files
- Verify function key is correct
- Check CORS settings if calling from browser
- Ensure file format is supported (JSON/CSV/XML)

## Cleanup

To delete all resources:

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

## Next Steps

- Set up custom domain
- Configure authentication (Azure AD)
- Add notification system (Azure Logic Apps)
- Implement data processing pipeline
- Set up alerts and monitoring

## Support

For issues, check:
1. Azure Portal → Function App → Monitor
2. Application Insights (if configured)
3. GitHub repository issues
