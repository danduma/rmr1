import os

from fastapi import FastAPI, Request, Query, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import date
import sqlite3
import os
import pandas as pd
from data_functions import get_survival_data
from llm import get_llm_response

from sql_db import clean_response, determine_chart_type, read_sql_query

import logging
logger = logging.getLogger(__name__)
app = FastAPI()

from image_storage import get_image_storage, load_mouse_images, get_images_for_mouse
from mouse_data import get_mice_data_from_db

# Initialize storage based on environment
image_storage = get_image_storage()

# Templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add this new route to serve mouse images
@app.get("/mouse-images/{path:path}")
async def get_mouse_image(path: str):
    try:
        image_data, content_type = image_storage.get_image(path)
        return Response(content=image_data.read(), media_type=content_type)
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.error(f"Error retrieving image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving image")

@app.get("/api/mice")
async def get_mice(sort: Optional[str] = Query(None)):
    if sort:
        column, _, order = sort.partition('-')
        order = 'asc' if order == 'asc' else 'desc'
        return get_mice_data_from_db(column, order)
    return get_mice_data_from_db()

# Load mice data from the database
mice_data = get_mice_data_from_db()


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/mice")
async def mice(request: Request):
    return templates.TemplateResponse("mice.html", {"request": request, "mice": mice_data})

@app.get("/query")
async def query(request: Request):
    return templates.TemplateResponse("query.html", {"request": request})

@app.get("/api/mouse/{ear_tag}")
async def get_mouse(ear_tag: int):
    mouse = next((m for m in mice_data if m.EarTag == ear_tag), None)
    if mouse:
        return {**mouse.dict(), "image": mouse_images.get(ear_tag)}
    return {"error": "Mouse not found"}

@app.get("/api/mouse-pictures/{ear_tag}")
async def get_mouse_pictures(ear_tag: int):
    mouse = next((m for m in mice_data if m.EarTag == ear_tag), None)
    if not mouse:
        raise HTTPException(status_code=404, detail="Mouse not found")
    
    images = get_images_for_mouse(ear_tag, mouse_images)
    logger.debug(f"Images for mouse {ear_tag}: {images}")
    return {
        "ear_tag": ear_tag,
        "sex": mouse.Sex,
        "dob": mouse.DOB.isoformat(),
        "pictures": images
    }

# Add new endpoint for handling queries
@app.post("/api/query")
async def handle_query(request: Request):
    data = await request.json()
    question = data.get('question')
    
    if not question:
        raise HTTPException(status_code=400, detail="No question provided")
    
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
    
    return {
        "sql": sql,
        "results": results_dict,
        "chart_type": chart_type
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8111)
