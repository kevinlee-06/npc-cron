from pydantic import BaseModel
from typing import Optional

class SoundOut(BaseModel):
    id: int
    filename: str
    label: str
    is_tts: bool

    class Config:
        from_attributes = True

class SoundUpdate(BaseModel):
    label: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-TW-HsiaoChenNeural"
    rate: str = "+0" # percentage as string e.g. "+0", "-10", "+20"
    pitch: str = "+0" # Hz as string, e.g. "+0", "-5"
    label: Optional[str] = None

class ScheduleBase(BaseModel):
    sound_id: int
    time: str
    days_of_week: str
    is_active: bool = True

class ScheduleIn(ScheduleBase):
    pass

class ScheduleOut(ScheduleBase):
    id: int
    class Config:
        from_attributes = True

class ExclusionBase(BaseModel):
    date: str
    reason: str

class ExclusionIn(ExclusionBase):
    pass

class ExclusionOut(ExclusionBase):
    id: int
    class Config:
        from_attributes = True
