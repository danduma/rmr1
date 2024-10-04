import streamlit as st
# import google.generativeai as genai
import sqlite3
import pandas as pd

import plotly.express as px
import json
from litellm import completion
import os

from data_functions import get_survival_data

# GOOGLE_API_KEY = 'Your API Key'

# genai.configure(api_key=GOOGLE_API_KEY)
# database_path = '/Users/abhi/Desktop/Text_SQL_Proj/Job_Postings.db'

current_dir = os.path.dirname(os.path.abspath(__file__))
default_location = os.path.join(current_dir, "vertexai-api-key.json")  
file_path = os.environ.get("VERTEXAI_API_KEY_PATH", default_location)

os.environ["VERTEXAI_PROJECT"] = os.environ.get("VERTEXAI_PROJECT", "cognivita")
os.environ["VERTEXAI_LOCATION"] = os.environ.get("VERTEXAI_LOCATION", "us-central1")

with open(file_path, 'r') as file:
    vertex_credentials = json.load(file)


def clean_response(response):
    response = response.replace("```sql", "").replace("```json", "").replace("```", "").strip()
    return response

def get_llm_response(question, prompt):
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question}
    ]
    
    response = completion( 
        model='vertex_ai/gemini-1.5-pro-002',
        messages=messages,
        stream=False,
        vertex_credentials=vertex_credentials
        )
    
    response_text = response.choices[0].message.content
    return response_text

def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def get_sql_query_from_response(response):
    try:
        query_start = response.index('SELECT')  
        query_end = response.index(';') + 1  
        sql_query = response[query_start:query_end]  
        return sql_query
    except ValueError:
        st.error("Could not extract SQL query from the response." + response)
        return None

def determine_chart_type(df):
    if len(df.columns) == 2:
        if df.dtypes[1] in ['int64', 'float64'] and len(df) > 1:
            return 'bar'
        elif df.dtypes[1] in ['int64', 'float64'] and len(df) <= 10:
            return 'pie'
    elif len(df.columns) >= 3 and df.dtypes[1] in ['int64', 'float64']:
        return 'line'
    return None

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def draw_km_plotly(data):    
    survival_data = data['survival_data']
    death_events = data['death_events']

    # Create figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add survival lines for each group
    for group in survival_data[list(survival_data.keys())[0]].keys():
        dates = list(survival_data.keys())
        values = [survival_data[date][group] for date in dates]
        fig.add_trace(
            go.Scatter(x=dates, y=values, name=group, mode='lines'),
            secondary_y=False
        )

    # Add death events as scatter points
    for event in death_events:
        fig.add_trace(
            go.Scatter(x=[event['date']], y=[survival_data[event['date']][event['group']]], 
                       mode='markers', name=f'Death Event ({event["group"]})',
                       marker=dict(color='red', 
                                   size=6, symbol='circle'),
                       showlegend=False),
            secondary_y=False
        )

    # Update layout
    fig.update_layout(
        title='Kaplan-Meier Survival Chart',
        xaxis_title='Date',
        yaxis_title='Number of Mice Alive',
        legend_title='Group',
        hovermode='closest'
    )
    fig.update_xaxes(tickangle=45)

    return fig

def generate_chart(df, chart_type):
    if df.empty:
        st.write("No data available to generate a chart.")
        return
    
    if chart_type == 'bar':
        fig = px.bar(df, x=df.columns[0], y=df.columns[1],
                     title=f"{df.columns[0]} vs. {df.columns[1]}",
                     template="plotly_white", color=df.columns[0])
    elif chart_type == 'pie':
        fig = px.pie(df, names=df.columns[0], values=df.columns[1],
                     title=f"Distribution of {df.columns[0]}",
                     template="plotly_white")
    elif chart_type == 'line':
        fig = px.line(df, x=df.columns[0], y=df.columns[1],
                      title=f"{df.columns[1]} Over {df.columns[0]}",
                      template="plotly_white", markers=True)
    elif chart_type == 'kaplan-meier':
        data = get_survival_data()
        fig = draw_km_plotly(data)
    else:
        st.write("No suitable chart type determined for this data.")
        return
    
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def generate_chart2(df, chart_type):
    if chart_type == 'bar':
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=f"{df.columns[0]} vs. {df.columns[1]}",
                     template="plotly_white", color=df.columns[0],
                     labels={df.columns[0]: "Category", df.columns[1]: "Count"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", 
                          yaxis=dict(title='Count'), 
                          xaxis=dict(title='Category'))
        fig.update_traces(marker_line_color='rgb(8,48,107)',
                          marker_line_width=1.5, opacity=0.6)
        st.plotly_chart(fig, use_container_width=True)

st.set_page_config(page_title="SQL Query Retrieval App", layout="wide")

st.markdown("""
    <h1 style="color: white; text-align: center;">
        🐭 LEVF Cheese Chasers 🧀
    </h1>
    """, unsafe_allow_html=True)

with st.container():
    st.subheader("What are you looking for?")

    with st.form(key='query_form'):
        col1, col2 = st.columns([4, 1], gap="small")

        with col1:
            question = st.text_input("Input your question here:", 
                                     key="input", 
                                     placeholder="Type here...",
                                     value="show me survival by group")

        with col2:
            st.write("")
            st.write("")
            submit = st.form_submit_button("Run", help="Click to submit your question.", use_container_width=True)

prompt = open("prompt.txt", "r").read()
database_path = "mouse_study.db"

if submit or question:  # This will trigger on button click or when Enter is pressed
    response = get_llm_response(question, prompt)
    response = clean_response(response)
    response_json = json.loads(response)
    sql = response_json['sql']
    chart_type = response_json.get('graph')
    
    # sql_query = get_sql_query_from_response(sql)
    sql_query = sql
    
    if sql_query:
        st.code(sql_query, language='sql')
        df = read_sql_query(sql_query, database_path)
        
        if not df.empty:
            col_data, col_chart = st.columns(2)
            with col_data:
                st.subheader("Query Results:")
                st.dataframe(df)
            if not chart_type:
                chart_type = determine_chart_type(df)
            
            if chart_type:
                with col_chart:
                    st.subheader("Visualization:")
                    generate_chart(df, chart_type)  
        else:
            st.write("No results found for the given query.")
    else:
        st.write("No valid SQL query could be extracted from the response.")


