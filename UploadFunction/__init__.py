import logging
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from io import StringIO
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient, TableEntity
import os


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to handle file uploads in JSON, CSV, or XML format.
    Stores files in Azure Blob Storage and metadata in Azure Table Storage.
    """
    logging.info('Upload function triggered.')

    try:
        # Get file from request
        file_data = req.files.get('file')
        if not file_data:
            return func.HttpResponse(
                json.dumps({"error": "No file provided"}),
                status_code=400,
                mimetype="application/json"
            )

        # Read file content
        file_content = file_data.read()
        filename = file_data.filename
        content_type = file_data.content_type or 'application/octet-stream'

        # Validate file format
        file_format = validate_and_get_format(filename, file_content)
        if not file_format:
            return func.HttpResponse(
                json.dumps({"error": "Invalid file format. Supported formats: JSON, CSV, XML"}),
                status_code=400,
                mimetype="application/json"
            )

        # Get Azure connection strings from environment
        storage_connection_string = os.getenv('AzureWebJobsStorage')
        if not storage_connection_string:
            logging.warning('AzureWebJobsStorage not configured')
            # For local development, provide a helpful message
            return func.HttpResponse(
                json.dumps({
                    "message": "File would be uploaded",
                    "filename": filename,
                    "format": file_format,
                    "size": len(file_content),
                    "note": "Azure Storage not configured (development mode)"
                }),
                status_code=200,
                mimetype="application/json"
            )

        # Upload to Blob Storage
        blob_url = upload_to_blob_storage(
            storage_connection_string,
            filename,
            file_content,
            content_type
        )

        # Store metadata in Table Storage
        metadata = store_metadata(
            storage_connection_string,
            filename,
            file_format,
            len(file_content),
            blob_url
        )

        # Return success response
        return func.HttpResponse(
            json.dumps({
                "message": "File uploaded successfully",
                "filename": filename,
                "format": file_format,
                "size": len(file_content),
                "blob_url": blob_url,
                "upload_id": metadata.get('RowKey')
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error processing upload: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Upload failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


def validate_and_get_format(filename: str, content: bytes) -> str:
    """
    Validate file format and return the format type.
    Supports JSON, CSV, and XML.
    """
    # Try to determine format from extension
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.json'):
        try:
            json.loads(content.decode('utf-8'))
            return 'JSON'
        except:
            return None
    
    elif filename_lower.endswith('.csv'):
        try:
            content_str = content.decode('utf-8')
            csv.reader(StringIO(content_str))
            return 'CSV'
        except:
            return None
    
    elif filename_lower.endswith('.xml'):
        try:
            ET.fromstring(content.decode('utf-8'))
            return 'XML'
        except:
            return None
    
    return None


def upload_to_blob_storage(connection_string: str, filename: str, 
                           content: bytes, content_type: str) -> str:
    """
    Upload file to Azure Blob Storage.
    Returns the blob URL.
    """
    try:
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Container name for uploads
        container_name = "uploads"
        
        # Create container if it doesn't exist
        try:
            container_client = blob_service_client.get_container_client(container_name)
            container_client.create_container()
        except:
            # Container already exists
            pass
        
        # Create unique blob name with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        blob_name = f"{timestamp}_{filename}"
        
        # Upload blob
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        blob_client.upload_blob(content, overwrite=True, content_settings={
            'content_type': content_type
        })
        
        return blob_client.url
    
    except Exception as e:
        logging.error(f"Error uploading to blob storage: {str(e)}")
        raise


def store_metadata(connection_string: str, filename: str, 
                   file_format: str, size: int, blob_url: str) -> dict:
    """
    Store file metadata in Azure Table Storage for reporting.
    Returns the metadata entity.
    """
    try:
        # Create table service client
        table_service_client = TableServiceClient.from_connection_string(connection_string)
        
        # Table name for metadata
        table_name = "uploadmetadata"
        
        # Create table if it doesn't exist
        try:
            table_client = table_service_client.create_table(table_name)
        except:
            # Table already exists
            table_client = table_service_client.get_table_client(table_name)
        
        # Create metadata entity
        upload_id = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        entity = TableEntity()
        entity['PartitionKey'] = file_format
        entity['RowKey'] = upload_id
        entity['Filename'] = filename
        entity['FileFormat'] = file_format
        entity['FileSize'] = size
        entity['BlobUrl'] = blob_url
        entity['UploadTimestamp'] = datetime.utcnow().isoformat()
        
        # Insert entity
        table_client.create_entity(entity)
        
        return entity
    
    except Exception as e:
        logging.error(f"Error storing metadata: {str(e)}")
        raise
