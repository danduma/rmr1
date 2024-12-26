import pandas as pd
import re
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Read the CSV file using path relative to script location
df = pd.read_csv(os.path.join(script_dir, '../data/image_results.csv'))

# Function to extract group number
def extract_group(text):
    if pd.isna(text):
        return None
    match = re.search(r'group\s*(\d)', text, re.IGNORECASE)
    return int(match.group(1)) if match else None

# Function to extract sex
def extract_sex(text):
    if pd.isna(text):
        return None
    match = re.search(r'(male|female)', text, re.IGNORECASE)
    if match:
        return 'M' if match.group(1).lower() == 'male' else 'F'
    return None

# Apply the extraction functions to create new columns
df['group'] = df['full_text'].apply(extract_group)
df['sex'] = df['full_text'].apply(extract_sex)

# Save the updated dataframe using path relative to script location
df.to_csv(os.path.join(script_dir, '..', 'data', 'image_results_processed.csv'), index=False)
