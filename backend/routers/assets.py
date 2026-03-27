import os
import shutil
import uuid
import edge_tts
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/assets", tags=["Assets"])

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.SoundOut)
async def upload_asset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".mp3", ".wav")):
        raise HTTPException(status_code=400, detail="Only MP3 or WAV files are supported")

    # Auto-rename if filename already exists on disk or in DB
    base, ext = os.path.splitext(file.filename)
    filename = file.filename
    counter = 1
    while (
        os.path.exists(os.path.join(MEDIA_DIR, filename))
        or db.query(models.Sound).filter(models.Sound.filename == filename).first()
    ):
        filename = f"{base}_{counter}{ext}"
        counter += 1

    file_path = os.path.join(MEDIA_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_sound = models.Sound(
        filename=filename,
        label=filename,
        is_tts=False,
        volume_offset=1.0
    )
    db.add(db_sound)
    db.commit()
    db.refresh(db_sound)
    return db_sound

@router.get("/", response_model=list[schemas.SoundOut])
def list_assets(db: Session = Depends(get_db)):
    return db.query(models.Sound).all()

@router.put("/{sound_id}", response_model=schemas.SoundOut)
def update_asset(sound_id: int, request: schemas.SoundUpdate, db: Session = Depends(get_db)):
    sound = db.query(models.Sound).filter(models.Sound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
        
    if request.label is not None:
        sound.label = request.label
        
    db.commit()
    db.refresh(sound)
    return sound

@router.delete("/{sound_id}")
def delete_asset(sound_id: int, db: Session = Depends(get_db)):
    sound = db.query(models.Sound).filter(models.Sound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")

    # Remove all schedules that reference this sound to prevent dangling FKs
    db.query(models.Schedule).filter(models.Schedule.sound_id == sound_id).delete()

    # Delete the audio file from disk
    file_path = os.path.join(MEDIA_DIR, sound.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(sound)
    db.commit()
    return {"status": "success", "message": "Deleted"}

@router.post("/tts", response_model=schemas.SoundOut)
async def generate_tts(request: schemas.TTSRequest, db: Session = Depends(get_db)):
    output_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    output_path = os.path.join(MEDIA_DIR, output_filename)
    
    communicate = edge_tts.Communicate(
        text=request.text,
        voice=request.voice,
        rate=f"{request.rate}%",
        pitch=f"{request.pitch}Hz"
    )
    await communicate.save(output_path)
    
    db_sound = models.Sound(
        filename=output_filename,
        label=request.label or ("TTS: " + request.text[:10]),
        is_tts=True,
        volume_offset=1.0
    )
    db.add(db_sound)
    db.commit()
    db.refresh(db_sound)
    return db_sound

@router.get("/tts/voices")
async def list_tts_voices():
    try:
        voices = await edge_tts.list_voices()
        # Return voices relevant to typical usage (e.g. all or filtered by zh-TW / en-US)
        zh_voices = [v for v in voices if "zh-" in v["Locale"] or "en-" in v["Locale"]]
        return zh_voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
