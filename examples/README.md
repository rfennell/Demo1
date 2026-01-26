# Example Data Files

This directory contains sample data files in different formats that can be used to test the upload functionality.

## Files

- `sample_data.json` - Sample user data in JSON format
- `sample_data.csv` - Sample user data in CSV format
- `sample_data.xml` - Sample user data in XML format

## Usage

### Testing Locally

If you're running the Azure Function locally:

```bash
# JSON upload
curl -X POST \
  -F "file=@examples/sample_data.json" \
  http://localhost:7071/api/upload

# CSV upload
curl -X POST \
  -F "file=@examples/sample_data.csv" \
  http://localhost:7071/api/upload

# XML upload
curl -X POST \
  -F "file=@examples/sample_data.xml" \
  http://localhost:7071/api/upload
```

### Testing in Production

Replace the URL with your Azure Function URL and add the function key:

```bash
# JSON upload
curl -X POST \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -F "file=@examples/sample_data.json" \
  https://your-function-app.azurewebsites.net/api/upload

# CSV upload
curl -X POST \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -F "file=@examples/sample_data.csv" \
  https://your-function-app.azurewebsites.net/api/upload

# XML upload
curl -X POST \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -F "file=@examples/sample_data.xml" \
  https://your-function-app.azurewebsites.net/api/upload
```

### Using Python

```python
import requests

url = "https://your-function-app.azurewebsites.net/api/upload"
headers = {"x-functions-key": "YOUR_FUNCTION_KEY"}

# Upload JSON
with open("examples/sample_data.json", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())

# Upload CSV
with open("examples/sample_data.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())

# Upload XML
with open("examples/sample_data.xml", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())
```
