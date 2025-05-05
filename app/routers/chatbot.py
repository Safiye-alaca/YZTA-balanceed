# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import mood as mood_model, user as user_model
from pydantic import BaseModel
from collections import Counter
from typing import List

router = APIRouter()

# 1️⃣ KİŞİSEL RUH HALİ ÖNERİSİ (Chatbot)
MOOD_RESPONSES = {
    "Yorgun": "Bugün biraz dinlenmeyi unutma. Yarın yeni bir başlangıç olabilir!",
    "Dalgın": "Zihnini toparlamak için kısa bir yürüyüş iyi gelebilir.",
    "Normal": "Harika! Bugünü verimli geçirmen için güzel bir fırsat.",
    "Meraklı": "Araştırmaya devam et! Belki yeni bir şey öğrenmenin tam zamanı.",
    "Enerjik": "Enerjini verimli kullan! Arkadaşlarınla bilgi paylaş, projelere katıl."
}

@router.get("/{user_id}")
def chatbot_suggestion(user_id: int, db: Session = Depends(get_db)):
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

# 2️⃣ YENİ: SUNUM ÖNERİ ŞABLONU (template + not + bölümler)
class ChatbotRequest(BaseModel):
    user_id: int
    class_id: int

MOOD_TEMPLATE_MAP = {
    "Yorgun": ("calm_structure", "Daha dinlendirici, sakin bir içerik önerilir."),
    "Dalgın": ("simple_focus", "Kısa ve dikkat çekici materyaller önerilir."),
    "Normal": ("balanced_flow", "Dengeli ve standart bir içerik önerilir."),
    "Meraklı": ("interactive_deep", "Etkileşimli etkinlikler ve sorular eklenebilir."),
    "Enerjik": ("visual_dive", "Grupla çalışma, tartışma gibi aktif yöntemler önerilir.")
}

TEMPLATE_SECTIONS = {
    "calm_structure": ["Giriş", "Temel Bilgiler", "1 Görsel", "Özet"],
    "simple_focus": ["Kısa Tanım", "Anahtar Kavramlar", "1 Soru", "Özet"],
    "balanced_flow": ["Giriş", "Detaylar", "Örnekler", "Sonuç"],
    "interactive_deep": ["Giriş", "Soru-Cevap", "Video Önerisi", "Derinlemesine Tartışma"],
    "visual_dive": ["Resimlerle Tanıtım", "Kısa Açıklamalar", "Etkinlik Önerisi", "Slogan"]
}

@router.post("/recommend")
def get_chatbot_recommendation(request: ChatbotRequest, db: Session = Depends(get_db)):
    latest_entry = db.query(mood_model.MoodEntry).filter(
        mood_model.MoodEntry.user_id == request.user_id,
        mood_model.MoodEntry.class_id == request.class_id
    ).order_by(mood_model.MoodEntry.timestamp.desc()).first()

    if not latest_entry:
        raise HTTPException(status_code=404, detail="Kullanıcının ruh hali verisi bulunamadı.")

    mood = latest_entry.mood
    if mood not in MOOD_TEMPLATE_MAP:
        raise HTTPException(status_code=400, detail="Geçersiz ruh hali verisi.")

    template_key, note = MOOD_TEMPLATE_MAP[mood]

    return {
        "user_id": request.user_id,
        "mood": mood,
        "recommendation": {
            "template": template_key,
            "sections": TEMPLATE_SECTIONS[template_key],
            "note": note
        }
    }
