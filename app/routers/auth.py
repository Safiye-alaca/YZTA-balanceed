# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.models import user as user_model
import bcrypt

router = APIRouter()

# Kullanıcıdan alınacak veri şeması
class UserCreate(BaseModel):
    username: str
    password: str

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
        password=hashed_password.decode('utf-8')  # Veritabanına string olarak kaydet
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Kayıt başarılı!",
        "user_id": new_user.id
    }
