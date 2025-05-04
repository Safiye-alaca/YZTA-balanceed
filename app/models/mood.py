from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.db.database import Base
from datetime import datetime

class MoodEntry(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    class_id = Column(Integer)  # Yeni eklendi
    score = Column(Integer)
    mood = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
