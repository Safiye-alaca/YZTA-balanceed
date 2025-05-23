from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    teacher_id = Column(Integer, nullable=True)  # Yeni eklenen alan
    class_id = Column(Integer, nullable=True)  # Öğrencinin ait olduğu sınıfı belirtir
