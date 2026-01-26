import pytest
import json
from unittest.mock import Mock, patch
from UploadFunction import main, validate_and_get_format
import azure.functions as func


def test_upload_no_file():
    """Test upload without a file."""
    # Create a mock request with no file
    req = Mock(spec=func.HttpRequest)
    req.files = {}
    
    # Call the function
    response = main(req)
    
    # Verify response
    assert response.status_code == 400
    response_data = json.loads(response.get_body())
    assert 'error' in response_data


def test_upload_invalid_format():
    """Test upload with invalid file format."""
    # Create a mock file with invalid format
    file_content = b'This is not a valid JSON, CSV, or XML file'
    
    # Create a mock file object
    mock_file = Mock()
    mock_file.read.return_value = file_content
    mock_file.filename = 'test.txt'
    mock_file.content_type = 'text/plain'
    
    # Create a mock request
    req = Mock(spec=func.HttpRequest)
    req.files = {'file': mock_file}
    
    # Call the function
    response = main(req)
    
    # Verify response
    assert response.status_code == 400
    response_data = json.loads(response.get_body())
    assert 'error' in response_data


def test_upload_valid_json():
    """Test upload with valid JSON file."""
    # Create valid JSON content
    json_data = {"name": "John", "age": 30, "city": "New York"}
    file_content = json.dumps(json_data).encode('utf-8')
    
    # Create a mock file object
    mock_file = Mock()
    mock_file.read.return_value = file_content
    mock_file.filename = 'test.json'
    mock_file.content_type = 'application/json'
    
    # Create a mock request
    req = Mock(spec=func.HttpRequest)
    req.files = {'file': mock_file}
    
    # Call the function
    response = main(req)
    
    # Verify response
    assert response.status_code == 200
    response_data = json.loads(response.get_body())
    assert 'filename' in response_data
    assert response_data['format'] == 'JSON'


def test_upload_valid_csv():
    """Test upload with valid CSV file."""
    # Create valid CSV content
    csv_content = b'name,age,city\nJohn,30,New York\nJane,25,Boston'
    
    # Create a mock file object
    mock_file = Mock()
    mock_file.read.return_value = csv_content
    mock_file.filename = 'test.csv'
    mock_file.content_type = 'text/csv'
    
    # Create a mock request
    req = Mock(spec=func.HttpRequest)
    req.files = {'file': mock_file}
    
    # Call the function
    response = main(req)
    
    # Verify response
    assert response.status_code == 200
    response_data = json.loads(response.get_body())
    assert 'filename' in response_data
    assert response_data['format'] == 'CSV'


def test_upload_valid_xml():
    """Test upload with valid XML file."""
    # Create valid XML content
    xml_content = b'<?xml version="1.0"?><root><person><name>John</name><age>30</age></person></root>'
    
    # Create a mock file object
    mock_file = Mock()
    mock_file.read.return_value = xml_content
    mock_file.filename = 'test.xml'
    mock_file.content_type = 'application/xml'
    
    # Create a mock request
    req = Mock(spec=func.HttpRequest)
    req.files = {'file': mock_file}
    
    # Call the function
    response = main(req)
    
    # Verify response
    assert response.status_code == 200
    response_data = json.loads(response.get_body())
    assert 'filename' in response_data
    assert response_data['format'] == 'XML'


def test_validate_json_format():
    """Test JSON format validation."""
    json_data = {"test": "data"}
    content = json.dumps(json_data).encode('utf-8')
    result = validate_and_get_format('test.json', content)
    assert result == 'JSON'


def test_validate_csv_format():
    """Test CSV format validation."""
    csv_data = b'col1,col2\nval1,val2'
    result = validate_and_get_format('test.csv', csv_data)
    assert result == 'CSV'


def test_validate_xml_format():
    """Test XML format validation."""
    xml_data = b'<?xml version="1.0"?><root><item>test</item></root>'
    result = validate_and_get_format('test.xml', xml_data)
    assert result == 'XML'


def test_validate_invalid_format():
    """Test invalid format validation."""
    invalid_data = b'This is just plain text'
    result = validate_and_get_format('test.txt', invalid_data)
    assert result is None
