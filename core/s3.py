import os
import shutil
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import config

def get_s3_client():
    """
    Returns an S3 client if keys are present, otherwise returns None.
    """
    if not config.AWS_ACCESS_KEY_ID or not config.AWS_SECRET_ACCESS_KEY or not config.AWS_S3_BUCKET_NAME:
        return None
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        return s3
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return None

def upload_file_to_s3(local_path: str, s3_key: str) -> bool:
    """
    Uploads a file to the S3 bucket. Falls back to local directory copy
    if AWS credentials or bucket configuration are missing.
    """
    s3_client = get_s3_client()
    
    if s3_client is None:
        # Fallback local storage logic
        print("[WARNING] AWS S3 configuration missing or incomplete. Falling back to local folder copy.")
        dest_path = os.path.join(config.DATA_DIR, s3_key)
        try:
            # Avoid self-copying if path is already the destination path
            if os.path.abspath(local_path) != os.path.abspath(dest_path):
                shutil.copy2(local_path, dest_path)
            print(f"Local Fallback: Saved copy to {dest_path}")
            return True
        except Exception as e:
            print(f"Local Fallback Error: Failed to copy file: {e}")
            return False

    # Actual S3 upload logic
    try:
        print(f"Uploading '{local_path}' to S3 bucket '{config.AWS_S3_BUCKET_NAME}' with key '{s3_key}'...")
        s3_client.upload_file(local_path, config.AWS_S3_BUCKET_NAME, s3_key)
        print("S3 upload successful!")
        return True
    except FileNotFoundError:
        print(f"S3 Upload Error: Local file not found: {local_path}")
        return False
    except NoCredentialsError:
        print("S3 Upload Error: AWS credentials not found.")
        return False
    except ClientError as e:
        print(f"S3 Upload Client Error: {e}")
        return False
    except Exception as e:
        print(f"S3 Upload Unexpected Error: {e}")
        return False

def delete_file_from_s3(s3_key: str) -> bool:
    """
    Deletes a file from the S3 bucket. Falls back to local directory delete
    if AWS credentials or bucket configuration are missing.
    """
    s3_client = get_s3_client()
    
    if s3_client is None:
        # Fallback local storage logic
        print("[WARNING] AWS S3 configuration missing or incomplete. Falling back to local folder delete.")
        local_path = os.path.join(config.DATA_DIR, s3_key)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                print(f"Local Fallback: Deleted {local_path}")
                return True
            except OSError as e:
                print(f"Local Fallback Error: Failed to delete: {e}")
                return False
        return True

    # Actual S3 deletion logic
    try:
        print(f"Deleting key '{s3_key}' from S3 bucket '{config.AWS_S3_BUCKET_NAME}'...")
        s3_client.delete_object(Bucket=config.AWS_S3_BUCKET_NAME, Key=s3_key)
        print("S3 delete successful!")
        return True
    except ClientError as e:
        print(f"S3 Delete Client Error: {e}")
        return False
    except Exception as e:
        print(f"S3 Delete Unexpected Error: {e}")
        return False
