import json
from datetime import datetime, timedelta
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3


def get_survival_data(start_date='11/03/23', end_date='10/03/24'):
    conn = sqlite3.connect('mouse_study.db')
    cursor = conn.cursor()

    # Convert dates to SQLite format
    start_date = datetime.strptime(start_date, '%m/%d/%y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%m/%d/%y').strftime('%Y-%m-%d')

    # Get all mice and their death dates
    cursor.execute('''
    SELECT m.EarTag, m.DOD, g.Number as Group_Number
    FROM MouseData m
    JOIN "Group" g ON m.Group_Number = g.Number
    WHERE m.DOB <= ? AND (m.DOD IS NULL OR m.DOD <= ?)
    ''', (start_date, end_date))

    mice_data = cursor.fetchall()

    # Initialize data structure
    survival_data = {}
    death_events = []

    # Process data
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        survival_data[date_str] = {}

        for group in set(mouse[2] for mouse in mice_data):
            alive_count = sum(1 for mouse in mice_data if mouse[2] == group and (mouse[1] is None or datetime.strptime(mouse[1], '%Y-%m-%d') > current_date))
            survival_data[date_str][f'Group {group}'] = alive_count

        # Check for deaths on this date
        for mouse in mice_data:
            if mouse[1] == date_str:
                death_events.append({
                    'date': date_str,
                    'group': f'Group {mouse[2]}',
                    'ear_tag': mouse[0]
                })

        current_date += timedelta(days=1)

    conn.close()

    return {
        'survival_data': survival_data,
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
    with open('survival_data.json', 'w') as f:
        json.dump(survival_data, f, indent=4)
    draw_kaplan_meier_chart(survival_data)