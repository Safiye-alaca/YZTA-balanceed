from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base
from datetime import datetime

class Presentation(Base):
    __tablename__ = "presentations"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, index=True)
    title = Column(String)
    file_path = Column(String)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
