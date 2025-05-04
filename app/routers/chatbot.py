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

@router.get("/chatbot/{user_id}/latest-mood")
def get_latest_user_mood(user_id: int, db: Session = Depends(get_db)):
    latest = db.query(mood_model.MoodEntry).filter_by(user_id=user_id).order_by(
        mood_model.MoodEntry.timestamp.desc()
    ).first()

    if not latest:
        raise HTTPException(status_code=404, detail="Henüz ruh hali verisi yok.")

    return {
        "user_id": user_id,
        "latest_mood": latest.mood,
        "score": latest.score,
        "timestamp": latest.timestamp
    }


@router.get("/chatbot/{user_id}/personal-recommendation")
def chatbot_personal_recommendation(user_id: int, db: Session = Depends(get_db)):
    last_entry = db.query(mood_model.MoodEntry).filter_by(user_id=user_id).order_by(
        mood_model.MoodEntry.timestamp.desc()
    ).first()

    if not last_entry:
        raise HTTPException(status_code=404, detail="Kullanıcının ruh hali kaydı bulunamadı.")

    mood = last_entry.mood

    suggestions = {
        "Yorgun": "Basit grafikler ve sade içeriklerle dikkat çekmeye çalış.",
        "Dalgın": "Görsel ağırlıklı ve dikkat çeken sunumlar tercih edilmeli.",
        "Normal": "Sunum akıcı ve dengeli olabilir.",
        "Meraklı": "Etkileşimli içerikler ve sorular eklemek faydalı olabilir.",
        "Enerjik": "Yüksek tempolu ve katılım teşvik eden sunumlar tercih edilmeli."
    }

    return {
        "user_id": user_id,
        "mood": mood,
        "suggested_presentation_type": suggestions.get(mood, "Genel bir içerik planı önerilebilir.")
    }

@router.get("/chatbot/{user_id}/summary")
def chatbot_summary(user_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(
        mood_model.MoodEntry.user_id == user_id
    ).order_by(mood_model.MoodEntry.timestamp.asc()).all()

    if not entries:
        raise HTTPException(status_code=404, detail="Kullanıcı için veri bulunamadı.")

    total_score = sum(e.score for e in entries)
    average_score = total_score / len(entries)

    mood_counts = {}
    for e in entries:
        mood_counts[e.mood] = mood_counts.get(e.mood, 0) + 1

    most_common_mood = max(mood_counts, key=mood_counts.get)

    return {
        "user_id": user_id,
        "average_score": round(average_score, 2),
        "most_common_mood": most_common_mood,
        "total_entries": len(entries),
        "mood_distribution": mood_counts
    }
