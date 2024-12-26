import json
from datetime import datetime, timedelta
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3

start_date = '2023-11-03'
end_date = '2024-10-03'

def convert_survival_data(df, start_date=start_date, end_date=end_date):
    # Initialize data structure
    survival_data = {}
    death_events = []

    # Process data
    current_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        survival_data[date_str] = {}

        for group in df['Group'].unique():
            alive_count = ((df['DOD'].isna()) | (pd.to_datetime(df['DOD']) > current_date)) & (df['Group'] == group)
            survival_data[date_str][f'Group {group}'] = alive_count.sum()

        # Check for deaths on this date
        deaths_today = df[pd.to_datetime(df['DOD']) == current_date]
        for _, mouse in deaths_today.iterrows():
            death_events.append({
                'date': date_str,
                'group': f"Group {mouse['Group']}",
                'ear_tag': mouse['EarTag']
            })

        current_date += pd.Timedelta(days=1)
    return survival_data, death_events

def get_survival_data(start_date=start_date, end_date=end_date, survival_data_path='data/survival_data.json'):
    # check if the file exists
    if os.path.exists(survival_data_path):
        try:
            with open(survival_data_path, 'r') as f:
                survival_data = json.load(f)
            return survival_data
        except json.JSONDecodeError:
            # If JSON loading fails, continue with generating new data
            pass
    
    conn = sqlite3.connect('data/mouse_study.db')

    # Convert dates to SQLite format
    start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
    end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')

    # Get all mice and their death dates
    query = '''
    SELECT m.EarTag, m.DOD, g.Number as "Group"
    FROM MouseData m
    JOIN "Group" g ON m.Group_Number = g.Number
    WHERE m.DOB <= ? AND (m.DOD IS NULL OR m.DOD <= ?)
    '''
    
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()

    survival_data, death_events = convert_survival_data(df, start_date, end_date)

    # Convert numpy types to native Python types before JSON serialization
    survival_data_serializable = {}
    for date, groups in survival_data.items():
        survival_data_serializable[date] = {
            group: int(count) for group, count in groups.items()
        }

    # Save the data to a JSON file for caching
    with open(survival_data_path, 'w') as f:
        json.dump(survival_data_serializable, f, indent=4)

    return {
        'survival_data': survival_data_serializable,
        'death_events': death_events
    }

def draw_kaplan_meier_chart(data_json):
    survival_data = data_json['survival_data']
    death_events = data_json['death_events']

    # Convert survival_data to DataFrame
    df = pd.DataFrame(survival_data).T
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)

    # Create the plot
    plt.figure(figsize=(12, 8))
    for column in df.columns:
        sns.lineplot(x=df.index, y=df[column], label=column)

    # Add death events as points
    for event in death_events:
        plt.scatter(pd.to_datetime(event['date']), df.loc[event['date'], event['group']], 
                    color='red', s=50, zorder=5)

    plt.title('Kaplan-Meier Survival Chart')
    plt.xlabel('Date')
    plt.ylabel('Number of Mice Alive')
    plt.legend(title='Group')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig('kaplan_meier_chart.png')
    plt.show()
    # save the plot to a file
    
    
if __name__=="__main__":
    survival_data = get_survival_data()
    draw_kaplan_meier_chart(survival_data)