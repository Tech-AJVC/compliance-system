"""
S3 Storage Utility for document management
"""
import boto3
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime
import mimetypes
from dotenv import load_dotenv, find_dotenv
# Load environment variables
load_dotenv()


logger = logging.getLogger(__name__)

class S3DocumentStorage:
    """
    S3 storage utility for uploading, downloading, and listing documents
    """
    
    def __init__(self, bucket_name: str = None, region_name: str = "ap-south-1"):
        """
        Initialize S3 client
        
        Args:
            bucket_name: S3 bucket name (can be set via environment variable)
            region_name: AWS region
        """
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        self.region_name = region_name
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided either as parameter or S3_BUCKET_NAME environment variable")
        
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                region_name=self.region_name,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 client initialized successfully for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            logger.error(f"Error initializing S3 client: {e}")
            raise
    
    def upload_file(self, 
                   local_file_path: str, 
                   s3_key: str, 
                   metadata: Dict[str, str] = None,
                   content_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to S3 with metadata
        
        Args:
            local_file_path: Path to local file
            s3_key: S3 object key (path in bucket)
            metadata: Additional metadata to store with file
            content_type: MIME type of file (auto-detected if not provided)
            
        Returns:
            Dictionary with upload result information
        """
        try:
            file_path = Path(local_file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(local_file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare metadata
            file_metadata = {
                'original_filename': file_path.name,
                'file_extension': file_path.suffix.lower(),
                'file_size': str(file_path.stat().st_size),
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_type': content_type
            }
            
            # Add custom metadata if provided
            if metadata:
                file_metadata.update(metadata)
            
            # Upload file with metadata
            extra_args = {
                'ContentType': content_type,
                'Metadata': file_metadata
            }
            
            self.s3_client.upload_file(
                Filename=local_file_path,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded {local_file_path} to s3://{self.bucket_name}/{s3_key}")
            
            return {
                'success': True,
                'bucket': self.bucket_name,
                's3_key': s3_key,
                's3_url': s3_url,
                'content_type': content_type,
                'metadata': file_metadata,
                'file_size': file_metadata['file_size']
            }
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, s3_key: str, local_file_path: str) -> Dict[str, Any]:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key
            local_file_path: Local path to save file
            
        Returns:
            Dictionary with download result information
        """
        try:
            # Create directory if it doesn't exist
            local_path = Path(local_file_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=local_file_path
            )
            
            logger.info(f"Successfully downloaded s3://{self.bucket_name}/{s3_key} to {local_file_path}")
            
            return {
                'success': True,
                'local_path': local_file_path,
                's3_key': s3_key
            }
            
        except Exception as e:
            logger.error(f"Error downloading file from S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_objects(self, prefix: str = "", limit: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket recursively from a folder or bucket with user-set limit
        
        Args:
            prefix: S3 key prefix to filter objects (folder path)
            limit: Maximum number of objects to return
            
        Returns:
            List of object information dictionaries
        """
        try:
            objects = []
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                PaginationConfig={'MaxItems': limit}
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'etag': obj['ETag'].strip('"'),
                            'storage_class': obj.get('StorageClass', 'STANDARD'),
                            's3_url': f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{obj['Key']}"
                        })
                        
                        # Stop if we've reached the limit
                        if len(objects) >= limit:
                            break
                
                if len(objects) >= limit:
                    break
            
            logger.info(f"Listed {len(objects)} objects with prefix '{prefix}' (limit: {limit})")
            return objects
            
        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            return []
    
    def delete_object(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete an object from S3
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted s3://{self.bucket_name}/{s3_key}")
            
            return {
                'success': True,
                's3_key': s3_key
            }
            
        except Exception as e:
            logger.error(f"Error deleting S3 object: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to S3 object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {s3_key} (expires in {expiration}s)")
            return url
            
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return ""
    



def get_s3_storage() -> S3DocumentStorage:
    """
    Factory function to get S3 storage instance
    
    Returns:
        S3DocumentStorage instance
    """
    return S3DocumentStorage()