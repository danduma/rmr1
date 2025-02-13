# this file is used to enrich the mouse data with group, cohort, and sex information from the database. Currently not needed as it's already been enriched via annotation_editor.py

import pandas as pd
import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mouse_data import get_db, get_full_mice_data_from_db
from data_processing.utils import generate_full_image_path

def enrich_mouse_data(df: pd.DataFrame, base_dir: str = "") -> pd.DataFrame:
    """
    Enriches a DataFrame containing mouse data with group, cohort, and sex information from the database,
    but only for rows where these values are missing. Also adds a new_file_path column.
    
    Args:
        df: DataFrame with columns: file_path, ear_tag, date, full_text
        base_dir: Base directory where processed images are stored
        
    Returns:
        DataFrame with filled-in columns: group, cohort, sex, new_file_path
    """
    # Check if any enrichment is needed
    columns_to_check = ['sex', 'group', 'cohort']
    empty_columns = [col for col in columns_to_check if col in df.columns and df[col].isna().any()]
    
    if not empty_columns:
        print("All columns already populated - no enrichment needed")
        return df
    
    print(f"Enriching columns: {empty_columns}")
    
    # Get database session
    db = next(get_db())
    
    # Query to get the enrichment data
    query = """
    SELECT 
        md.EarTag as ear_tag,
        md.Sex as sex,
        md.Group_Number as "group",
        c.CohortName as cohort
    FROM MouseData md
    LEFT JOIN Cohort c ON md.Cohort_id = c.Cohort_id
    """
    
    # Get the enrichment data
    enrichment_df = pd.read_sql_query(query, db.connection())
    
    # Close the database session
    db.close()
    
    # Convert ear_tag to int, dropping any rows where ear_tag is NA
    df_clean = df.copy()
    
    # Drop rows where ear_tag is NA
    na_count = df_clean['ear_tag'].isna().sum()
    if na_count > 0:
        print(f"Warning: Dropping {na_count} rows with missing ear tags")
        df_clean = df_clean.dropna(subset=['ear_tag'])
    
    # Convert to int
    df_clean['ear_tag'] = df_clean['ear_tag'].astype(int)
    
    # For each empty column, update only the missing values
    for col in empty_columns:
        # Create a temporary merge for this column
        temp_df = df_clean.merge(
            enrichment_df[['ear_tag', col]],
            on='ear_tag',
            how='left',
            suffixes=('', '_new')
        )
        
        # Update only the missing values using index-based update
        df_clean.loc[df_clean[col].isna(), col] = temp_df.loc[temp_df.index[df_clean[col].isna()], f'{col}_new']
    
    # Add new_file_path column
    required_columns = ['group', 'sex', 'ear_tag', 'date']
    if all(col in df_clean.columns for col in required_columns):
        # Handle NaN values in group column before integer conversion
        df_clean = df_clean.dropna(subset=['group'])
        if len(df_clean) < len(df):
            print(f"Warning: Dropped {len(df) - len(df_clean)} rows with missing group values")
        
        # Convert group to integer type to avoid float formatting
        df_clean['group'] = df_clean['group'].astype(int)
        
        # First generate all base paths without counters
        base_paths = df_clean.apply(
            lambda row: generate_full_image_path(
                base_dir=base_dir,
                group=str(int(row['group'])),  # Ensure integer conversion
                sex=row['sex'],
                ear_tag=str(row['ear_tag']),
                date=row['date']
            ) if pd.notna(row[required_columns]).all() else None,
            axis=1
        )
        
        # Create a dictionary to track counts of each base path
        path_counts = {}
        # Create a list to store final paths with counters
        final_paths = []
        
        # Process each path and add counters where needed
        for path in base_paths:
            if path is None:
                final_paths.append(None)
                continue
                
            # Split the path into base and extension
            base, ext = os.path.splitext(path)
            
            # Initialize or increment counter for this base path
            if base not in path_counts:
                path_counts[base] = 0
            path_counts[base] += 1
            
            # Add counter to path if it's not the first occurrence
            if path_counts[base] == 1:
                final_paths.append(path)
            else:
                final_paths.append(f"{base}_{path_counts[base]}{ext}")
        
        # Assign the final paths to the new_file_path column
        df_clean['new_file_path'] = final_paths
    else:
        print(f"Warning: Cannot generate new_file_path, missing one or more required columns: {required_columns}")
    
    return df_clean

def enrich_and_save_file(input_path: str = 'data/image_results.csv', 
                        output_path: str = 'data/image_enriched.csv') -> None:
    """
    Reads a CSV file, enriches it with mouse data, and saves the result to a new CSV file.
    
    Args:
        input_path: Path to the input CSV file (default: 'data/image_results.csv')
        output_path: Path to save the enriched CSV file (default: 'data/image_enriched.csv')
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Read the input CSV
    df = pd.read_csv(input_path)
    
    # Enrich the data
    enriched_df = enrich_mouse_data(df)
    
    # Save the enriched data
    enriched_df.to_csv(output_path, index=False)
    print(f"Enriched data saved to {output_path}")

if __name__ == "__main__":
    enrich_and_save_file()
