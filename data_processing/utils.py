import os

def generate_image_output_path(output_folder: str, group: str, sex: str, ear_tag: str) -> str:
    """
    Generate the output path for an image based on its metadata.
    
    Args:
        output_folder (str): Base directory where processed images will be saved
        group (str): The group number/identifier
        sex (str): The sex of the animal
        ear_tag (str): The ear tag identifier
        
    Returns:
        str: The complete output path for the image
    """
    return os.path.join(output_folder, group, sex, ear_tag) 

def generate_image_filename(group: str, sex: str, ear_tag: str, date: str) -> str:
    """
    Generate the filename for an image based on its metadata.
    
    Args:
        group (str): The group number/identifier
        sex (str): The sex of the animal
        ear_tag (str): The ear tag identifier
        date (str): The date in YYYY-MM-DD format
        
    Returns:
        str: The formatted filename with .jpg extension
    """
    return f"G{group}_{sex}_{ear_tag}_{date}.jpg"

def generate_full_image_path(base_dir: str, group: str, sex: str, ear_tag: str, date: str) -> str:
    """
    Generate the complete path to a processed image file.
    
    Args:
        base_dir (str): Base directory where processed images are stored
        group (str): The group number/identifier
        sex (str): The sex of the animal
        ear_tag (str): The ear tag identifier
        date (str): The date in YYYY-MM-DD format
        
    Returns:
        str: The complete path to the image file
    """
    output_path = generate_image_output_path(base_dir, group, sex, ear_tag)
    filename = generate_image_filename(group, sex, ear_tag, date)
    return os.path.join(output_path, filename) 