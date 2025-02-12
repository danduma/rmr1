import json
from datetime import date
import sqlite3
import pandas as pd
from data_processing.data_functions import get_survival_data
from backend.llm import get_llm_response


def clean_response(response):
    response = response.replace("```sql", "").replace("```json", "").replace("```", "").strip()
    return response

def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def determine_chart_type(df):
    if len(df.columns) == 2:
        if df.dtypes[1] in ['int64', 'float64'] and len(df) > 1:
            return 'bar'
        elif df.dtypes[1] in ['int64', 'float64'] and len(df) <= 10:
            return 'pie'
    elif len(df.columns) >= 3 and df.dtypes[1] in ['int64', 'float64']:
        return 'line'
    return None

def call_llm_and_get_results(question):
    # Read prompt from file
    with open("prompt.txt", "r") as f:
        prompt = f.read()
    
    # Get LLM response
    response = get_llm_response(question, prompt)
    response = clean_response(response)
    response_json = json.loads(response)
    
    sql = response_json['sql']
    chart_type = response_json.get('graph')
    
    # Execute SQL query
    database_path = "data/mouse_study.db"
    
    # If it's a Kaplan-Meier chart, get survival data
    if chart_type == 'kaplan-meier':
        results = get_survival_data()
        # Convert any numpy types in the survival data
        results_dict = json.loads(json.dumps(results, default=lambda x: x.item() if hasattr(x, 'item') else x))
    else:
        results = read_sql_query(sql, database_path)
        if not chart_type:
            chart_type = determine_chart_type(results)
            
        # Convert DataFrame to records and handle special types
        results_dict = []
        for record in results.to_dict(orient='records'):
            processed_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    processed_record[key] = None
                elif isinstance(value, (pd.Timestamp, date)):
                    processed_record[key] = value.isoformat()
                elif hasattr(value, 'item'):  # Handle numpy types
                    processed_record[key] = value.item()
                else:
                    processed_record[key] = value
            results_dict.append(processed_record)
    
    return sql, results_dict, chart_type
