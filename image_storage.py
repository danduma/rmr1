from google.cloud import storage
from abc import ABC, abstractmethod
from typing import Union, BinaryIO
import os
from io import BytesIO
import pandas as pd
from google.oauth2 import service_account
from google.api_core import exceptions as google_exceptions
import logging
from data_processing.utils import generate_full_image_path

# Set pandas option to prevent downcasting warning
pd.set_option('future.no_silent_downcasting', True)

logger = logging.getLogger(__name__)

class ImageStorage(ABC):
    @abstractmethod
    def get_image(self, path: str) -> tuple[BinaryIO, str]:
        """Returns tuple of (image_data, content_type)"""
        pass

class LocalImageStorage(ImageStorage):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
    
    def get_image(self, path: str) -> tuple[BinaryIO, str]:
        full_path = os.path.join(self.base_dir, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Image not found: {full_path}")
        
        content_type = "image/jpeg"  # Default
        if path.lower().endswith('.png'):
            content_type = "image/png"
        elif path.lower().endswith('.gif'):
            content_type = "image/gif"
            
        return open(full_path, 'rb'), content_type

class GCSImageStorage(ImageStorage):
    def __init__(self, bucket_name: str, base_path: str, local_fallback_path: str = None):
        try:
            # Initialize client
            credentials = service_account.Credentials.from_service_account_file(
                'gcs_key2.json'
            )
            self.client = storage.Client(credentials=credentials)
            
            # Check if bucket exists
            try:
                self.bucket = self.client.get_bucket(bucket_name)
                logger.info(f"Successfully connected to bucket: {bucket_name}")
                
                # Optional: List some files to verify access
                blobs = list(self.bucket.list_blobs(max_results=1))
                logger.info(f"Successfully listed files in bucket. Found {len(blobs)} files.")
                
            except google_exceptions.NotFound:
                raise ValueError(f"Bucket {bucket_name} does not exist!")
            except google_exceptions.Forbidden:
                raise ValueError(f"No access to bucket {bucket_name}. Check permissions!")
            
            self.base_path = base_path
            self.use_gcs = True
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS: {str(e)}")
            if local_fallback_path:
                logger.warning("Falling back to local storage")
                self.local_storage = LocalImageStorage(local_fallback_path)
                self.use_gcs = False
            else:
                raise
    
    def get_image(self, path: str) -> tuple[BinaryIO, str]:
        blob = self.bucket.blob(os.path.join(self.base_path, path))
        if not blob.exists():
            raise FileNotFoundError(f"Image not found in GCS: {path}")
        
        content_type = "image/jpeg"  # Default
        if path.lower().endswith('.png'):
            content_type = "image/png"
        elif path.lower().endswith('.gif'):
            content_type = "image/gif"
        
        return BytesIO(blob.download_as_bytes()), content_type

def get_image_storage():
    """Factory function to create the appropriate image storage instance"""
    if os.getenv('USE_GCS', '').lower() == 'true':
        return GCSImageStorage(os.getenv('GCS_BUCKET_NAME'), os.getenv('GCS_BASE_PATH'))
    else:
        return LocalImageStorage(os.getenv('LOCAL_BASE_PATH'))
    
def load_mouse_images(image_csv_path='data/image_results.csv'):
    """Load and process mouse images from CSV"""
    # Read the CSV file with ear_tag as nullable integer type
    df = pd.read_csv(image_csv_path, dtype={'ear_tag': 'Int64'})
    
    # Drop rows with missing ear_tags and corrupt images
    corrupt_series = df.get('corrupt', pd.Series(False, index=df.index))
    df = df[
        df['ear_tag'].notna() & 
        ~corrupt_series.fillna(False)
    ]
    
    # Group by ear_tag and create a dictionary of images for each mouse
    result = {}
    for ear_tag, group in df.groupby('ear_tag'):
        if pd.isna(ear_tag):
            continue
            
        # Only include rows that have a valid new_file_path
        valid_images = group[group['new_file_path'].notna()]
        if not valid_images.empty:
            # Create list of dicts with only file_path and date
            images = [{'file_path': row['new_file_path'], 'date': row['date']} 
                     for _, row in valid_images.iterrows()]
            result[int(ear_tag)] = images
    
    return result

def get_images_for_mouse(ear_tag, mouse_images):
    """Get list of image paths for a specific mouse"""
    return mouse_images.get(ear_tag, [])
