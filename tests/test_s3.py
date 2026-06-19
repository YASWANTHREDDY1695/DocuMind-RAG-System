import os
from unittest.mock import patch, MagicMock
from core.s3 import upload_file_to_s3, delete_file_from_s3

@patch('core.s3.config')
@patch('core.s3.shutil')
def test_s3_upload_fallback(mock_shutil, mock_config):
    """
    Verifies that if AWS credentials are not set, S3 upload falls back
    to copying the file locally into the data/ directory.
    """
    mock_config.AWS_ACCESS_KEY_ID = ""
    mock_config.AWS_SECRET_ACCESS_KEY = ""
    mock_config.AWS_S3_BUCKET_NAME = ""
    mock_config.DATA_DIR = "mock_data_dir"
    
    success = upload_file_to_s3("source.pdf", "dest.pdf")
    
    assert success is True
    # Verify local copy fallback was called
    mock_shutil.copy2.assert_called_once_with("source.pdf", os.path.join("mock_data_dir", "dest.pdf"))

@patch('core.s3.config')
@patch('core.s3.boto3.client')
def test_s3_upload_aws(mock_boto_client, mock_config):
    """
    Verifies that if AWS credentials are set, the file is uploaded to the S3 bucket.
    """
    mock_config.AWS_ACCESS_KEY_ID = "test_key"
    mock_config.AWS_SECRET_ACCESS_KEY = "test_secret"
    mock_config.AWS_S3_BUCKET_NAME = "test_bucket"
    mock_config.AWS_REGION = "us-east-1"
    
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    
    success = upload_file_to_s3("source.pdf", "dest.pdf")
    
    assert success is True
    # Verify S3 client was called correctly
    mock_s3.upload_file.assert_called_once_with("source.pdf", "test_bucket", "dest.pdf")

@patch('core.s3.config')
@patch('core.s3.os.path.exists')
@patch('core.s3.os.remove')
def test_s3_delete_fallback(mock_remove, mock_exists, mock_config):
    """
    Verifies that if AWS credentials are not set, document deletion falls back
    to deleting the file locally from the data/ directory.
    """
    mock_config.AWS_ACCESS_KEY_ID = ""
    mock_config.AWS_SECRET_ACCESS_KEY = ""
    mock_config.AWS_S3_BUCKET_NAME = ""
    mock_config.DATA_DIR = "mock_data_dir"
    
    mock_exists.return_value = True
    
    success = delete_file_from_s3("dest.pdf")
    
    assert success is True
    # Verify local remove fallback was called
    mock_remove.assert_called_once_with(os.path.join("mock_data_dir", "dest.pdf"))

@patch('core.s3.config')
@patch('core.s3.boto3.client')
def test_s3_delete_aws(mock_boto_client, mock_config):
    """
    Verifies that if AWS credentials are set, the document is deleted from the S3 bucket.
    """
    mock_config.AWS_ACCESS_KEY_ID = "test_key"
    mock_config.AWS_SECRET_ACCESS_KEY = "test_secret"
    mock_config.AWS_S3_BUCKET_NAME = "test_bucket"
    mock_config.AWS_REGION = "us-east-1"
    
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    
    success = delete_file_from_s3("dest.pdf")
    
    assert success is True
    # Verify S3 client deleted the object
    mock_s3.delete_object.assert_called_once_with(Bucket="test_bucket", Key="dest.pdf")
