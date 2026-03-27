import asyncio
from datetime import datetime
from database import SessionLocal
import models
import os
from settings import get_settings

async def play_sound(sound_filename, volume_offset=1.0):
    media_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media", sound_filename))
    if not os.path.exists(media_path):
        print(f"File not found: {media_path}")
        return False
        
    # Scale volume_offset (0.0 to 1.0) to mpv percentage (0 to 100)
    vol_pct = int(volume_offset * 100)
    cmd = ["mpv", "--no-video", "--really-quiet", f"--volume={vol_pct}"]
    
    device = get_settings().get("output_device")
    if device:
        cmd.extend([f"--audio-device={device}"])
        
    cmd.append(media_path)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        await process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Error playing sound: {e}")
        return False

async def run_scheduler():
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_day_str = str(now.isoweekday())
        current_date_str = now.strftime("%Y-%m-%d")
        
        seconds_to_wait = 60 - now.second
        await asyncio.sleep(seconds_to_wait)
        
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        db = SessionLocal()
        try:
            exclusion = db.query(models.Exclusion).filter(models.Exclusion.date == current_date_str).first()
            if exclusion:
                continue
                
            schedules = db.query(models.Schedule).filter(
                models.Schedule.time == current_time_str,
                models.Schedule.is_active == True
            ).all()
            
            for sched in schedules:
                if current_day_str in sched.days_of_week.split(","):
                    sound = db.query(models.Sound).filter(models.Sound.id == sched.sound_id).first()
                    if sound:
                        # Start playback in background but track it for logging
                        async def play_and_log(s_id, filename, vol):
                            success = await play_sound(filename, vol)
                            inner_db = SessionLocal()
                            try:
                                log = models.Log(
                                    played_at=datetime.now().isoformat(),
                                    status="Success" if success else "Fail",
                                    sound_id=s_id
                                )
                                inner_db.add(log)
                                inner_db.commit()
                            finally:
                                inner_db.close()
                        
                        asyncio.create_task(play_and_log(sound.id, sound.filename, sound.volume_offset))
        except Exception as e:
            print(f"Scheduler exception: {e}")
        finally:
            db.close()
