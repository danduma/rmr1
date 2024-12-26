import os

from fastapi import FastAPI, Request, Query, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import pandas as pd

from llm_sql import call_llm_and_get_results, clean_response, determine_chart_type, read_sql_query

import logging
logger = logging.getLogger(__name__)
app = FastAPI()

from image_storage import get_image_storage, load_mouse_images, get_images_for_mouse
from mouse_data import get_full_mice_data_from_db

# Initialize storage based on environment
image_storage = get_image_storage()
mouse_images = load_mouse_images()

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
        return get_full_mice_data_from_db(column, order)
    return get_full_mice_data_from_db()

# Load mice data from the database
mice_data = get_full_mice_data_from_db()


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
    
    sql, results_dict, chart_type = call_llm_and_get_results(question)
    
    return {
        "sql": sql,
        "results": results_dict,
        "chart_type": chart_type
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8111)
