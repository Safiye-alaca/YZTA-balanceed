# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import mood as mood_model

router = APIRouter()

# Duyguya göre öneri sözlüğü
MOOD_RESPONSES = {
    "Yorgun": "Bugün biraz dinlenmeyi unutma. Yarın yeni bir başlangıç olabilir!",
    "Dalgın": "Zihnini toparlamak için kısa bir yürüyüş iyi gelebilir.",
    "Normal": "Harika! Bugünü verimli geçirmen için güzel bir fırsat.",
    "Meraklı": "Araştırmaya devam et! Belki yeni bir şey öğrenmenin tam zamanı.",
    "Enerjik": "Enerjini verimli kullan! Arkadaşlarınla bilgi paylaş, projelere katıl."
}

@router.get("/chatbot/{user_id}")
def chatbot_suggestion(user_id: int, db: Session = Depends(get_db)):
    # En son mood kaydını çek
    last_entry = db.query(mood_model.MoodEntry).filter_by(user_id=user_id).order_by(
        mood_model.MoodEntry.timestamp.desc()
    ).first()

    if not last_entry:
        raise HTTPException(status_code=404, detail="Kullanıcının ruh hali kaydı bulunamadı.")

    mood = last_entry.mood
    response = MOOD_RESPONSES.get(mood, "Bugünün nasıl geçtiğini düşünmek için güzel bir an.")

    return {
        "user_id": user_id,
        "mood": mood,
        "suggestion": response
    }

from pydantic import BaseModel

class ChatMessage(BaseModel):
    message: str

@router.post("/ask")
def ask_chatbot(user_input: ChatMessage):
    response = generate_response(user_input.message)
    return {"response": response}

def generate_response(message: str) -> str:
    message = message.lower()
    if "merhaba" in message:
        return "Merhaba! Sana nasıl yardımcı olabilirim?"
    elif "sunum" in message:
        return "Sunumları görmek için sunum sayfasını kullanabilirsin."
    elif "ruh hali" in message:
        return "Ruh halini test etmek için test sayfasına göz at!"
    else:
        return "Üzgünüm, bu konuyu henüz anlayamıyorum. Başka bir şey dene :)"
