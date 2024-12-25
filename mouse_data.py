import sqlite3
from datetime import date
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel

from image_storage import load_mouse_images
import logging

logger = logging.getLogger(__name__)

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
    try:
        conn = sqlite3.connect('data/mouse_study.db')
        cursor = conn.cursor()

        query = '''
        SELECT EarTag, Sex, DOB, DOD, DeathDetails, DeathNotes, Necropsy, Stagger, Group_Number, Cohort_id
        FROM MouseData
        '''

        if sort_column and sort_column != 'PictureCount':
            query += f' ORDER BY {sort_column} {sort_order.upper()}'

        cursor.execute(query)
        rows = cursor.fetchall()

        # Load mouse images data
        mouse_images = load_mouse_images()

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
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()