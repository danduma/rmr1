import csv
import json
import os
import pandas as pd
import sqlite3
from datetime import datetime
import traceback

def load_grip_strength_data(start_directory):
    conn = sqlite3.connect('mouse_study.db')
    cursor = conn.cursor()
    
    dtype = {'Identifier': str, 'Index': str, 'Value': float, 'Date': str}

    for root, dirs, files in os.walk(start_directory):
        for file in files:
            if file.endswith(('.xls', '.xlsx')):
                file_path = os.path.join(root, file)
                try:
                    # Try reading with default engine, specifying dtype
                    df = pd.read_excel(file_path, header=None, dtype=dtype)
                except ValueError as e:
                    if "Excel file format cannot be determined" in str(e):
                        # If default fails, try with 'xlrd' engine for .xls files
                        try:
                            df = pd.read_excel(file_path, header=None, engine='xlrd', dtype=dtype)
                        except Exception as e2:
                            # If both Excel attempts fail, try reading as TSV
                            try:
                                df = pd.read_csv(file_path, sep='\t', header=None, encoding='utf-8', dtype=dtype)
                                print(f"Successfully read {file_path} as TSV")
                            except Exception as e3:
                                print(f"Error processing file {file_path}: {str(e3)}")
                                continue
                    else:
                        print(f"Error processing file {file_path}: {str(e)}")
                        continue

                try:
                    # Set column names based on the first row
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0])

                    # Convert 'Date' column to datetime
                    df['Date'] = pd.to_datetime(df['Date'])

                    # Add error checking for 'Identifier' and 'Index' columns
                    if 'Identifier' not in df.columns or 'Index' not in df.columns:
                        raise ValueError(f"Required columns 'Identifier' or 'Index' not found in {file_path}")
                    df['Identifier'] = df['Identifier'].astype(str)
                    df['Index'] = df['Index'].astype(str)
                    df['EarTag'] = df['Identifier'].apply(lambda x: int(str(x).split()[0]))

                    df['ValueIndex'] = df['Index'].astype(int)

                    # Rename 'Max Value' to 'Value' if it exists
                    if 'Max Value' in df.columns:
                        df = df.rename(columns={'Max Value': 'Value'})

                    # Select and reorder columns, dropping rows with None in ValueIndex
                    df = df[['EarTag', 'Date', 'ValueIndex', 'Value']].dropna(subset=['ValueIndex'])

                    # Add a unique constraint to the GripStrength table if it doesn't exist
                    cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_grip_strength 
                    ON GripStrength (EarTag, Date, ValueIndex)
                    ''')

                    # Replace the INSERT INTO statement with INSERT OR REPLACE
                    for _, row in df.iterrows():
                        cursor.execute('''
                        INSERT OR REPLACE INTO GripStrength (EarTag, Date, ValueIndex, Value)
                        VALUES (?, ?, ?, ?)
                        ''', (row['EarTag'], row['Date'].date(), int(row['ValueIndex']), row['Value']))

                    conn.commit()
                    print(f"Processed file: {file_path}")

                except Exception as e:
                    print(f"Error processing data in file {file_path}: {str(e)}")
                    print(f"DataFrame head:\n{df.head()}")
                    print(f"DataFrame info:\n{df.info()}")
                    continue

    conn.close()


def load_cohort_data(file_path):
    conn = sqlite3.connect('mouse_study.db')
    cursor = conn.cursor()

    try:
        df = pd.read_csv(file_path, sep=',', quotechar='"', 
                         lineterminator='\n', quoting=csv.QUOTE_MINIMAL, 
                         on_bad_lines='warn')
        
        print(f"Successfully read file. Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Create a dictionary to map cohort names to numbers
        cohort_map = {name: number for number, name in enumerate(sorted(df['CohortLookup'].unique()), 1)}
        
        for _, row in df.iterrows():
            try:
                ear_tag = int(row.get('EarTagLookup', 0))
                sex = str(row.get('SexLookup', ''))[:1]  # Take only the first character
                group_number = int(row.get('Group NoLookup', '').split()[-1])  # Extract number from "Group X"
                cohort_name = str(row.get('CohortLookup', ''))
                cohort_number = cohort_map[cohort_name]

                # Insert into MouseData table
                cursor.execute('''
                INSERT OR REPLACE INTO MouseData (EarTag, Sex, Group_Number, Cohort_id)
                VALUES (?, ?, ?, ?)
                ''', (ear_tag, sex, group_number, cohort_number))

                # Insert into Cohort table
                cursor.execute('''
                INSERT OR REPLACE INTO Cohort (Cohort_id, CohortName)
                VALUES (?, ?)
                ''', (cohort_number, cohort_name))  

                # Insert into Group table
                cursor.execute('''
                INSERT OR REPLACE INTO "Group" (Number, Cohort_id)
                VALUES (?, ?)
                ''', (group_number, cohort_number))

            except (sqlite3.IntegrityError, ValueError) as e:
                print(f"Error inserting row {row.to_dict()}: {str(e)}")
                print(f"Types: EarTag={type(ear_tag)}, Sex={type(sex)}, Group_Number={type(group_number)}, Cohort_id={type(cohort_number)}")
                continue

        conn.commit()
        print(f"Successfully loaded data from {file_path}")
        print(f"Cohort mapping: {cohort_map}")
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        print(traceback.format_exc())
    finally:
        conn.close()


def load_death_data(file_path):
    conn = sqlite3.connect('mouse_study.db')
    cursor = conn.cursor()

    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=0)
        
        # Iterate through each row
        for _, row in df.iterrows():
            # Check if there's a valid date in the first column (DOB)
            if pd.notna(row.iloc[0]) and isinstance(row.iloc[0], datetime):
                dob = row.iloc[0].date()
                dod = row.iloc[5].date() if pd.notna(row.iloc[5]) else None
                ear_tag = int(row.iloc[7]) if pd.notna(row.iloc[7]) else None
                
                if ear_tag is not None:
                    # Insert or update the data in the MouseData table
                    cursor.execute('''
                    INSERT OR REPLACE INTO MouseData (EarTag, DOB, DOD)
                    VALUES (?, ?, ?)
                    ON CONFLICT(EarTag) DO UPDATE SET
                    DOB = COALESCE(EXCLUDED.DOB, DOB),
                    DOD = COALESCE(EXCLUDED.DOD, DOD)
                    ''', (ear_tag, dob, dod))

        conn.commit()
        print(f"Successfully loaded death data from {file_path}")
    except Exception as e:
        print(f"Error processing death data: {str(e)}")
        print(traceback.format_exc())
    finally:
        conn.close()



from pathlib import Path

def index_mouse_images(root_directory):
    mouse_images = {}
    root_path = Path(root_directory)

    for file_path in root_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            if file_path.stem[:4].isdigit() and (len(file_path.stem) == 4 or file_path.stem[4] in [' ', '_'] or file_path.stem[4].isalpha()):
                ear_tag = file_path.stem[:4]
                relative_path = file_path.relative_to(root_path)
                img_data = {
                    "img_path": str(relative_path),
                    "img_desc": f"Image of mouse {ear_tag} at {relative_path}"
                }
                
                if ear_tag not in mouse_images:
                    mouse_images[ear_tag] = []
                mouse_images[ear_tag].append(img_data)

    return mouse_images


# Usage
if __name__ == '__main__':
    # start_directory = '/Users/masterman/Downloads/LEVF/Behavioral Testing/Grip strength'
    # load_grip_strength_data(start_directory)

    # cohort_file_path = '/path/to/your/cohort_file.txt'
    # load_cohort_data(cohort_file_path)

    # death_data_file_path = '/path/to/your/death_data.xlsx'
    # load_death_data(death_data_file_path)

    # root_directory = '/Users/masterman/Downloads/LEVF/Whole body pictures'
    # mouse_images = index_mouse_images(root_directory)
    # with open('mouse_images.json', 'w') as f:
    #     json.dump(mouse_images, f)
    pass
