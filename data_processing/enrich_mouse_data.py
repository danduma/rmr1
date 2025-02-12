import pandas as pd
import os
from backend.mouse_data import get_db, get_full_mice_data_from_db

def enrich_mouse_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches a DataFrame containing mouse data with group, cohort, and sex information from the database.
    
    Args:
        df: DataFrame with columns: file_path, ear_tag, date, full_text
        
    Returns:
        DataFrame with additional columns: group, cohort, sex
    """
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
    
    # Convert ear_tag to int to ensure matching works
    df['ear_tag'] = df['ear_tag'].astype(int)
    
    # Merge the enrichment data with the original dataframe
    enriched_df = df.merge(
        enrichment_df,
        on='ear_tag',
        how='left'
    )
    
    return enriched_df

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
