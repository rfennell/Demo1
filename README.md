# Data Upload Service

A cloud-based data upload service built with Azure Functions and Python that allows end users to upload data in JSON, CSV, or XML formats. The service stores files in Azure Blob Storage and maintains metadata in Azure Table Storage for reporting purposes.

## Features

- **Multiple Format Support**: Upload files in JSON, CSV, or XML format
- **Azure Cloud Storage**: Files stored in Azure Blob Storage
- **Metadata Tracking**: Upload metadata stored in Azure Table Storage for easy reporting
- **Serverless Architecture**: Built on Azure Functions for scalability
- **CI/CD Pipeline**: Automated testing and deployment via GitHub Actions
- **Secure**: Function-level authentication with Azure

## Architecture

```
User Upload → Azure Function → Blob Storage (file)
                            → Table Storage (metadata)
```

## Prerequisites

- Python 3.10 or higher
- Azure Account
- Azure Storage Account
- Azure Functions Core Tools (for local development)

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/rfennell/Demo1.git
   cd Demo1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure local settings**
   ```bash
   cp local.settings.json.example local.settings.json
   cp .env.example .env
   ```

4. **For local testing with Azurite (Azure Storage Emulator)**
   ```bash
   npm install -g azurite
   azurite-blob --silent --location /tmp/azurite
   ```

5. **Run the function locally**
   ```bash
   func start
   ```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run tests with coverage:
```bash
pytest tests/ -v --cov=UploadFunction --cov-report=html
```

## Deployment

### Azure Resources Setup

1. **Create Azure Resources** (via Azure Portal or Azure CLI):
   ```bash
   # Create Resource Group
   az group create --name data-upload-rg --location eastus
   
   # Create Storage Account
   az storage account create \
     --name datauploadstorage123 \
     --resource-group data-upload-rg \
     --location eastus \
     --sku Standard_LRS
   
   # Create Function App
   az functionapp create \
     --resource-group data-upload-rg \
     --consumption-plan-location eastus \
     --runtime python \
     --runtime-version 3.10 \
     --functions-version 4 \
     --name data-upload-function-app \
     --storage-account datauploadstorage123 \
     --os-type Linux
   ```

2. **Configure GitHub Secrets** (for CI/CD):
   - `AZURE_CREDENTIALS`: Service principal credentials
   - `AZURE_FUNCTIONAPP_NAME`: Your Function App name
   - `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`: Download from Azure Portal

3. **Deploy via GitHub Actions**:
   - Push to `main` branch triggers automatic deployment
   - The CI/CD pipeline runs tests and deploys if successful

### Manual Deployment

```bash
func azure functionapp publish <FUNCTION_APP_NAME>
```

## API Usage

### Upload Endpoint

**Endpoint**: `POST /api/upload`

**Headers**:
- `x-functions-key`: Your function key (get from Azure Portal)

**Body**: Form-data with file field

**Example using curl**:
```bash
# Upload JSON file
curl -X POST \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -F "file=@data.json" \
  https://your-function-app.azurewebsites.net/api/upload

# Upload CSV file
curl -X POST \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -F "file=@data.csv" \
  https://your-function-app.azurewebsites.net/api/upload

# Upload XML file
curl -X POST \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -F "file=@data.xml" \
  https://your-function-app.azurewebsites.net/api/upload
```

**Example using Python**:
```python
import requests

url = "https://your-function-app.azurewebsites.net/api/upload"
headers = {"x-functions-key": "YOUR_FUNCTION_KEY"}

with open("data.json", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())
```

**Success Response**:
```json
{
  "message": "File uploaded successfully",
  "filename": "data.json",
  "format": "JSON",
  "size": 1234,
  "blob_url": "https://storage.blob.core.windows.net/uploads/20240126_143000_data.json",
  "upload_id": "20240126143000123456"
}
```

**Error Response**:
```json
{
  "error": "Invalid file format. Supported formats: JSON, CSV, XML"
}
```

## Reporting

All upload metadata is stored in Azure Table Storage (`uploadmetadata` table) with the following schema:

| Field | Description |
|-------|-------------|
| PartitionKey | File format (JSON/CSV/XML) |
| RowKey | Upload ID (timestamp-based) |
| Filename | Original filename |
| FileFormat | File format |
| FileSize | File size in bytes |
| BlobUrl | URL to the blob in storage |
| UploadTimestamp | UTC timestamp of upload |

**Query uploads using Azure Portal, Storage Explorer, or Azure SDK**:

```python
from azure.data.tables import TableServiceClient

connection_string = "YOUR_CONNECTION_STRING"
table_service = TableServiceClient.from_connection_string(connection_string)
table_client = table_service.get_table_client("uploadmetadata")

# Get all JSON uploads
entities = table_client.query_entities("PartitionKey eq 'JSON'")
for entity in entities:
    print(f"File: {entity['Filename']}, Uploaded: {entity['UploadTimestamp']}")
```

## File Format Requirements

### JSON
- Must be valid JSON format
- File extension: `.json`

Example:
```json
{
  "name": "John Doe",
  "age": 30,
  "city": "New York"
}
```

### CSV
- Must have comma-separated values
- File extension: `.csv`

Example:
```csv
name,age,city
John Doe,30,New York
Jane Smith,25,Boston
```

### XML
- Must be well-formed XML
- File extension: `.xml`

Example:
```xml
<?xml version="1.0"?>
<root>
  <person>
    <name>John Doe</name>
    <age>30</age>
    <city>New York</city>
  </person>
</root>
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) includes:

1. **Build and Test** (runs on all pushes and PRs):
   - Sets up Python environment
   - Installs dependencies
   - Runs test suite with coverage

2. **Deploy** (runs on main branch only):
   - Deploys to Azure Functions
   - Requires Azure credentials configured in GitHub Secrets

## Project Structure

```
Demo1/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions CI/CD pipeline
├── UploadFunction/
│   ├── __init__.py            # Azure Function implementation
│   └── function.json          # Function binding configuration
├── tests/
│   ├── __init__.py
│   └── test_upload.py         # Unit tests
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── host.json                  # Azure Functions host configuration
├── local.settings.json.example # Local settings template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Security Considerations

- Function uses function-level authentication (requires API key)
- Connection strings stored in Azure App Settings (not in code)
- Files are stored in private blob containers
- Table storage requires proper authentication

## Monitoring

Monitor the function app through:
- Azure Portal → Function App → Monitor
- Application Insights (if configured)
- Azure Storage Explorer for blob and table data

## Troubleshooting

**Issue**: "No file provided" error
- Ensure you're sending the file in form-data with field name `file`

**Issue**: "Invalid file format" error
- Check that your file has the correct extension (.json, .csv, .xml)
- Ensure the file content is valid for its format

**Issue**: Local development storage errors
- Start Azurite: `azurite-blob --silent --location /tmp/azurite`
- Or use actual Azure Storage connection string

## License

MIT

## Support

For issues and questions, please open an issue in the GitHub repository.