from sqlalchemy import Column, Integer, String, Boolean, Float, Time, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Sound(Base):
    __tablename__ = "sounds"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    label = Column(String, index=True)
    is_tts = Column(Boolean, default=False)
    volume_offset = Column(Float, default=1.0) # Gain value
    
    schedules = relationship("Schedule", back_populates="sound")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    sound_id = Column(Integer, ForeignKey("sounds.id"))
    time = Column(String, index=True) # HH:MM format
    days_of_week = Column(String) # "1,2,3,4,5"
    is_active = Column(Boolean, default=True)
    output_device = Column(String, nullable=True)
    
    sound = relationship("Sound", back_populates="schedules")

class Exclusion(Base):
    __tablename__ = "exclusions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD format
    reason = Column(String)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    played_at = Column(String, index=True) # ISO format
    status = Column(String) # "Success" / "Fail"
    sound_id = Column(Integer, ForeignKey("sounds.id"), nullable=True)
