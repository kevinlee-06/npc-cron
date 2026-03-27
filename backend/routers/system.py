import os
import asyncio
import subprocess
import re
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
from scheduler import play_sound
from settings import get_settings, save_settings
from pydantic import BaseModel

playing_tasks = []


router = APIRouter(prefix="/api/system", tags=["System & Hardware"])

@router.post("/stop")
async def stop_all_audio():
    try:
        subprocess.run(["killall", "mpv"], check=False)
    except Exception:
        pass
        
    for task in playing_tasks:
        if not task.done():
            task.cancel()
    playing_tasks.clear()
    
    return {"status": "stopped"}

@router.post("/clear")
def clear_all_data(db: Session = Depends(get_db)):
    # Clear logs, exclusions, schedules first due to FK dependencies
    db.query(models.Log).delete()
    db.query(models.Exclusion).delete()
    db.query(models.Schedule).delete()
    
    # Get all sounds to delete their files
    sounds = db.query(models.Sound).all()
    media_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "media"))
    for sound in sounds:
        file_path = os.path.join(media_dir, sound.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
    # Now delete sounds from DB
    db.query(models.Sound).delete()
    db.commit()
    
    return {"status": "success", "message": "All database records and media files have been cleared."}

@router.get("/settings")
def load_sys_settings():
    return get_settings()

@router.post("/play/{sound_id}")
async def instant_play(sound_id: int, db: Session = Depends(get_db)):
    try:
        sound = db.query(models.Sound).filter(models.Sound.id == sound_id).first()
        if not sound:
            raise HTTPException(status_code=404, detail="Sound not found")
            
        # Fire and forget playback with its DB-stored volume offset
        task = asyncio.create_task(play_sound(sound.filename, sound.volume_offset))
        playing_tasks.append(task)
        return {"status": "success", "message": f"Playing {sound.label}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
