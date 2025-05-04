# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional  # teacher_id için gerekli
from app.db.database import get_db
from app.models import user as user_model
import bcrypt

router = APIRouter()

# Kullanıcıdan alınacak veri şeması
class UserCreate(BaseModel):
    username: str
    password: str
    teacher_id: Optional[int] = None  # Yeni eklendi

# Kullanıcı kaydı
@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Kullanıcı adı zaten var mı kontrol et
    existing_user = db.query(user_model.User).filter(user_model.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten var.")

    # Şifreyi hashle
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

    # Yeni kullanıcıyı oluştur
    new_user = user_model.User(
        username=user_data.username,
        password=hashed_password.decode('utf-8'),
        teacher_id=user_data.teacher_id  # Yeni eklendi
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Kayıt başarılı!",
        "user_id": new_user.id
    }

@router.get("/teacher/{teacher_id}/students")
def get_students_by_teacher(teacher_id: int, db: Session = Depends(get_db)):
    students = db.query(user_model.User).filter(user_model.User.teacher_id == teacher_id).all()
    
    if not students:
        raise HTTPException(status_code=404, detail="Bu öğretmene ait öğrenci bulunamadı.")

    return [
        {
            "user_id": student.id,
            "username": student.username
        }
        for student in students
    ]

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(user_model.User).filter(user_model.User.username == user_data.username).first()

    if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

    return {
        "message": "Giriş başarılı!",
        "user_id": user.id,
        "username": user.username,
        "is_teacher": user.teacher_id is None  # Eğer teacher_id yoksa bu kişi öğretmendir
    }

@router.get("/teacher/{teacher_id}/students")
def get_students_by_teacher(teacher_id: int, db: Session = Depends(get_db)):
    students = db.query(user_model.User).filter(user_model.User.teacher_id == teacher_id).all()

    if not students:
        raise HTTPException(status_code=404, detail="Bu öğretmene bağlı öğrenci bulunamadı.")

    return [
        {
            "user_id": student.id,
            "username": student.username
        }
        for student in students
    ]
