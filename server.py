from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import date
import sqlite3
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

def load_mouse_images():
    with open('mouse_images.json', 'r') as f:
        return json.load(f)

def get_images_for_mouse(ear_tag, mouse_images):
    return mouse_images.get(str(ear_tag), [])

# Usage
mouse_images = load_mouse_images()
selected_ear_tag = 5003
images = get_images_for_mouse(selected_ear_tag, mouse_images)


# Update the path to your images
IMAGES_DIR = "/Users/masterman/Downloads/LEVF/Whole body pictures"

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add this new route to serve mouse images
@app.get("/mouse-images/{path:path}")
async def get_mouse_image(path: str):
    full_path = os.path.join(IMAGES_DIR, path)
    logger.debug(f"Requested image path: {full_path}")
    if os.path.isfile(full_path):
        logger.debug(f"File found: {full_path}")
        return FileResponse(full_path)
    logger.error(f"File not found: {full_path}")
    raise HTTPException(status_code=404, detail="Image not found")

# Templates
templates = Jinja2Templates(directory="templates")

# Mock data (replace with your actual data source)
class MouseData(BaseModel):
    EarTag: int
    Sex: str
    DOB: date
    DOD: Optional[date] = None
    DeathDetails: Optional[str] = None
    DeathNotes: Optional[str] = None
    Necropsy: Optional[bool] = None
    Stagger: Optional[int] = None
    Group_Number: Optional[int] = None
    Cohort_id: Optional[int] = None
    PictureCount: int

def get_mice_data_from_db(sort_column: str = None, sort_order: str = 'asc'):
    conn = sqlite3.connect('mouse_study.db')
    cursor = conn.cursor()

    query = '''
    SELECT EarTag, Sex, DOB, DOD, DeathDetails, DeathNotes, Necropsy, Stagger, Group_Number, Cohort_id
    FROM MouseData
    '''

    if sort_column and sort_column != 'PictureCount':
        query += f' ORDER BY {sort_column} {sort_order.upper()}'

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    # Load mouse images data
    with open('mouse_images.json', 'r') as f:
        mouse_images = json.load(f)

    mice_data = [
        MouseData(
            EarTag=row[0],
            Sex=row[1],
            DOB=date.fromisoformat(row[2]) if row[2] else None,
            DOD=date.fromisoformat(row[3]) if row[3] else None,
            DeathDetails=row[4],
            DeathNotes=row[5],
            Necropsy=row[6],
            Stagger=row[7],
            Group_Number=row[8],
            Cohort_id=row[9],
            PictureCount=len(mouse_images.get(str(row[0]), []))
        )
        for row in rows
    ]

    if sort_column == 'PictureCount':
        mice_data.sort(key=lambda x: x.PictureCount, reverse=(sort_order == 'desc'))

    return mice_data

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
