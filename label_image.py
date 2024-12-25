import json
import os
import textwrap
from pathlib import Path
from typing import Dict
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor, AutoModelForCausalLM
import csv
import re
from datetime import datetime
from dateutil import parser
from tqdm import tqdm

model_id = 'microsoft/Florence-2-base'
device = 'mps'

#load Florence-2 model
model = AutoModelForCausalLM.from_pretrained(model_id, device_map = device, trust_remote_code=True).eval()

processor = AutoProcessor.from_pretrained(model_id, device_map = device, trust_remote_code=True)

# task_prompt = 'extract the following information from the image: mouse EarTag (4 digits), Date'
task_prompt = ''

def generate_labels(task_prompt, image, text_input=None):
    if text_input is None:
        prompt = task_prompt
    else:
        prompt = task_prompt + text_input

    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)

    generated_ids = model.generate(
      input_ids=inputs["input_ids"],
      pixel_values=inputs["pixel_values"],
      max_new_tokens=1024,
      early_stopping=False,
      do_sample=False,
      num_beams=3,
    )

    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

    output = processor.post_process_generation(
        generated_text,
        task=task_prompt,
        image_size=(image.width, image.height)
    )

    return output
     
     
def ocr_regions(task_prompt: str, image, text_input: str="") -> Dict:
    prompt = task_prompt + text_input

    inputs = processor(text=prompt, images=image, return_tensors="pt")
    generated_ids = model.generate(
        input_ids=inputs["input_ids"].to(device),
        pixel_values=inputs["pixel_values"].to(device),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

    parsed_answer = processor.post_process_generation(generated_text, task=task_prompt, image_size=(image.width, image.height))

    return parsed_answer

def extract_metadata(text, file_path):
    # Extract 4-digit ear tag
    ear_tag_match = re.search(r'\b{5,6}\d{3}\b', text)
    ear_tag = ear_tag_match.group(0) if ear_tag_match else ''
    
    # Extract date using dateutil - first try from text
    date = ''
    date_match = re.search(r'DATE:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if date_match:
        try:
            parsed_date = parser.parse(date_match.group(1).strip())
            date = parsed_date.strftime('%Y-%m-%d')
        except parser.ParserError:
            pass
    
    # If no date found, try to find it in the file path
    if not date:
        # Convert Path object to string and split into parts
        path_parts = str(file_path).split('/')
        for part in path_parts:
            # Look for common date formats in path components
            # e.g., "29MAR23", "2023-03-29", etc.
            try:
                parsed_date = parser.parse(part, fuzzy=True)
                date = parsed_date.strftime('%Y-%m-%d')
                break
            except parser.ParserError:
                continue
    
    return ear_tag, date

def label_images(root_directory, csv_path, image_database={}):
    root_path = Path(root_directory)
    
    # Pre-process to get total file count and remaining files
    all_image_files = [
        f for f in root_path.rglob('*') 
        if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']
    ]
    
    # Convert to relative paths and filter out already processed files
    remaining_files = [
        f for f in all_image_files 
        if str(f.relative_to(root_path)) not in image_database
    ]
    
    print(f"Found {len(all_image_files)} total images")
    print(f"Already processed: {len(all_image_files) - len(remaining_files)}")
    print(f"Remaining to process: {len(remaining_files)}")
    
    files_with_errors = []
    
    with open(csv_path, 'a', newline='') as csvfile:
        fieldnames = ['file_path', 'ear_tag', 'date', 'full_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        
        try:
            # Replace the for loop with tqdm
            for file_path in tqdm(remaining_files, desc="Processing images"):
                try:
                    relative_path = str(file_path.relative_to(root_path))
                    image = Image.open(file_path)
                    prompt = "<OCR_WITH_REGION>"
                    result = ocr_regions(prompt, image)
                    image_text = "\n".join(result[prompt]['labels'])
                    
                    # Extract metadata
                    ear_tag, date = extract_metadata(image_text, file_path)
                    
                    # Create dictionary with all metadata
                    image_data = {
                        'file_path': relative_path,
                        'ear_tag': ear_tag,
                        'date': date,
                        'full_text': image_text
                    }
                    
                    # Write to CSV
                    writer.writerow(image_data)
                    
                    # Update image database with complete metadata
                    image_database[relative_path] = image_data
                    
                    print(f"{relative_path}: {image_text} [{ear_tag}] ({date})")
                    
                    # Flush CSV after each write
                    csvfile.flush()

                except Exception as e:
                    print(f"\nError processing {file_path}: {e}. Skipping this image...")
                    files_with_errors.append(file_path)
                    continue

        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Progress saved to CSV...")
        except Exception as e:
            print(f"\nAn error occurred: {e}. Progress saved to CSV...")
        finally:
            print(f"Error with files ")
            for error_file in files_with_errors:
                print(error_file)
            return image_database
        
if __name__ == '__main__':
    image_database = {}
    csv_path = 'image_results.csv'
    
    # Load existing data from CSV if it exists
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            image_database = {row['file_path']: row for row in reader}

    image_database = label_images('/Users/masterman/Downloads/LEVF/Whole body pictures', csv_path, image_database)
    
    # Still save JSON for backwards compatibility
    with open('image_database.jsonl', 'w') as f:
        for entry in image_database.values():
            json.dump(entry, f)
            f.write('\n')