from datetime import date
from typing import Optional
from fastapi import HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import MouseData as MouseModel
from image_storage import load_mouse_images
import logging

logger = logging.getLogger(__name__)

class Mouse(BaseModel):
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
    
    class Config:
        from_attributes = True
    

def get_full_mice_data_from_db(sort_column: str = None, sort_order: str = 'asc', db: Session = Depends(get_db)):
    # try:
        query = db.query(MouseModel)
        
        if sort_column and sort_column != 'PictureCount':
            order_column = getattr(MouseModel, sort_column.lower())
            if sort_order.lower() == 'desc':
                order_column = desc(order_column)
            query = query.order_by(order_column)
            
        mice = query.all()
        
        # Load mouse images data
        mouse_images = load_mouse_images()
        
        mice_data = [
            Mouse(
                EarTag=mouse.EarTag,
                Sex=mouse.Sex,
                DOB=mouse.DOB,
                DOD=mouse.DOD,
                DeathDetails=mouse.DeathDetails,
                DeathNotes=mouse.DeathNotes,
                Necropsy=mouse.Necropsy,
                Stagger=mouse.Stagger,
                Group_Number=mouse.Group_Number,
                Cohort_id=mouse.Cohort_id,
                PictureCount=len(mouse_images.get(str(mouse.EarTag), []))
            )
            for mouse in mice
        ]
        
        if sort_column == 'PictureCount':
            mice_data.sort(key=lambda x: x.PictureCount, reverse=(sort_order.lower() == 'desc'))
            
        return mice_data
        
    # except Exception as e:
    #     logger.error(f"Database error: {e}")
    #     raise HTTPException(status_code=500, detail="Database error")