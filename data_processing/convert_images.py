import os
import pandas as pd
from PIL import Image
from datetime import datetime
from pathlib import Path
from utils import generate_image_output_path, generate_image_filename
from tqdm import tqdm
import multiprocessing as mp
from functools import partial

def process_single_image(row, output_folder: str, root_folder: str):
    """
    Process a single image based on the row data.
    
    Args:
        row: Pandas Series containing image metadata
        output_folder (str): Base directory where processed images will be saved
        root_folder (str): Root directory where the original images are stored
    """
    try:
        # Skip if the row is marked as corrupt
        if pd.notna(row.get('corrupt')) and row['corrupt']:
            return
            
        # Get the values from the row
        file_path = os.path.join(root_folder, row['file_path'])
        new_file_path = row.get('new_file_path')
        
        # Skip if required fields are missing or if new_file_path is NaN
        if not all([file_path, new_file_path]) or pd.isna(new_file_path):
            print(f"Skipping {file_path}: Missing required fields or new_file_path is NaN")
            return
            
        # Create the full output path
        output_file_path = os.path.join(output_folder, new_file_path)
        
        # Create the output directory
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        if os.path.exists(output_file_path):
            return
        
        # Open and process the image
        with Image.open(file_path) as img:
            # Calculate new dimensions (25% of original)
            new_width = int(img.width * 0.25)
            new_height = int(img.height * 0.25)
            
            # Resize the image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save the resized image with 85% quality
            resized_img.save(output_file_path, 'JPEG', quality=85)
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return

def process_and_resize_images(csv_path: str, output_folder: str, root_folder: str, max_files: int = None):
    """
    Process images from a CSV file in parallel, resize them to 25% of original size, and save them in an organized directory structure.
    
    Args:
        csv_path (str): Path to the CSV file containing image metadata
        output_folder (str): Base directory where processed images will be saved
        root_folder (str): Root directory where the original images are stored
        max_files (int, optional): Maximum number of files to process, useful for testing. If None, process all files.
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Limit the number of files if max_files is specified
    if max_files is not None:
        df = df.head(max_files)
    
    # Get the number of CPU cores (leave one core free for system processes)
    num_processes = max(1, mp.cpu_count() - 1)
    
    # Create a partial function with fixed arguments
    process_func = partial(process_single_image, output_folder=output_folder, root_folder=root_folder)
    
    print(f"Processing {len(df)} images using {num_processes} processes")
    # Create a pool of workers and process the images in parallel
    with mp.Pool(num_processes) as pool:
        list(tqdm(
            pool.imap(process_func, [row for _, row in df.iterrows()]),
            total=len(df),
            desc=f"Processing images"
        ))

if __name__ == '__main__':
    # Example usage
    csv_path = 'data/image_results.csv'
    root_folder = '/Users/masterman/Downloads/LEVF/Whole body pictures'
    output_folder = os.path.join(root_folder, 'processed_images')
    
    max_files = None
    process_and_resize_images(csv_path, output_folder, root_folder, max_files=max_files)
