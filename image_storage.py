from google.cloud import storage
from abc import ABC, abstractmethod
from typing import Union, BinaryIO
import os
from io import BytesIO
import pandas as pd

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
    def __init__(self, bucket_name: str, base_path: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.base_path = base_path
    
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

def load_mouse_images():
    """Load and process mouse images from CSV"""
    # Read the CSV file with ear_tag as nullable integer type
    df = pd.read_csv('data/ocr/image_results.csv', dtype={'ear_tag': 'Int64'})
    
    # Drop NA values before grouping
    df = df.dropna(subset=['ear_tag'])
    
    # Group by ear_tag and create a dictionary of records
    mouse_images = df.groupby('ear_tag').apply(
        lambda x: x[['file_path', 'date', 'full_text']].to_dict('records')
    ).to_dict()
    
    # Convert ear_tag keys to strings
    return {str(k): v for k, v in mouse_images.items()}

def get_images_for_mouse(ear_tag, mouse_images):
    """Get images for a specific mouse by ear tag"""
    return mouse_images.get(str(ear_tag), [])
