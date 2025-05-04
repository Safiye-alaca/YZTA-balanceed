from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import mood as mood_model
from collections import Counter
from fastapi import HTTPException


router = APIRouter()

# Test formu verisi için veri yapısı
from pydantic import BaseModel
from typing import List

class MoodTestInput(BaseModel):
    answers: List[int]  # örneğin [2, 4, 3, 1, 5]
    user_id: int
    class_id: int  #  eklendi

# Ruh halini puana göre belirleyen fonksiyon
def calculate_mood(score: int) -> str:
    if score <= 7:
        return "Yorgun"
    elif score <= 12:
        return "Dalgın"
    elif score <= 17:
        return "Normal"
    elif score <= 22:
        return "Meraklı"
    else:
        return "Enerjik"

@router.post("/submit")
def submit_mood_test(
    test_data: MoodTestInput,
    db: Session = Depends(get_db)
):
    score = sum(test_data.answers)
    mood = calculate_mood(score)

    mood_entry = mood_model.MoodEntry(
        user_id=test_data.user_id,
        class_id=test_data.class_id,
        score=score,
        mood=mood
    )
    db.add(mood_entry)
    db.commit()
    db.refresh(mood_entry)

    return {
        "score": score,
        "mood": mood,
        "message": "Ruh hali başarıyla kaydedildi!"
    }

@router.get("/class/{class_id}/summary")
def get_class_summary(class_id: int, db: Session = Depends(get_db)):
    # Belirli sınıfa ait tüm mood kayıtlarını getir
    moods = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.class_id == class_id).all()

    if not moods:
        raise HTTPException(status_code=404, detail="Bu sınıf için veri bulunamadı.")

    scores = [m.score for m in moods]
    mood_names = [m.mood for m in moods]

    average_score = sum(scores) / len(scores)
    mood_counts = dict(Counter(mood_names))
    dominant_mood = max(mood_counts, key=mood_counts.get)

    # Sunum şablonu önerisi (örnek amaçlı basit karar)
    if dominant_mood == "Yorgun":
        template_key = "relax_focus"
    elif dominant_mood == "Enerjik":
        template_key = "deep_dive"
    else:
        template_key = "balanced_engagement"

    return {
        "class_id": class_id,
        "average_score": round(average_score, 2),
        "mood_distribution": mood_counts,
        "suggested_template": template_key
    }

from fastapi import HTTPException  # eğer üstte import edilmediyse ekle

@router.get("/class/{class_id}/recommendation")
def get_recommendation_for_class(class_id: int, db: Session = Depends(get_db)):
    mood_entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.class_id == class_id).all()
    
    if not mood_entries:
        raise HTTPException(status_code=404, detail="Bu sınıf için ruh hali verisi bulunamadı.")

    mood_counts = {}
    for entry in mood_entries:
        mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1

    most_common_mood = max(mood_counts, key=mood_counts.get)

    recommendations = {
        "Yorgun": "Daha dinlendirici, sakin bir içerik önerilir.",
        "Dalgın": "Kısa ve dikkat çekici materyaller kullanın.",
        "Normal": "Dengeli ve standart bir içerik önerilir.",
        "Meraklı": "Etkileşimli etkinlikler ve sorular eklenebilir.",
        "Enerjik": "Grupla çalışma, tartışma gibi aktif yöntemler önerilir."
    }

    return {
        "most_common_mood": most_common_mood,
        "recommendation": recommendations.get(most_common_mood, "Genel bir şablon önerisi bulunamadı.")
    }

@router.get("/class-summary/{class_id}")
def get_class_mood_summary(class_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.class_id == class_id).all()

    if not entries:
        return {"message": "Bu sınıf için henüz veri yok."}

    mood_counts = {}
    for entry in entries:
        mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1

    # En sık görülen ruh hali
    most_common_mood = max(mood_counts, key=mood_counts.get)

    return {
        "class_id": class_id,
        "total_entries": len(entries),
        "mood_distribution": mood_counts,
        "most_common_mood": most_common_mood
    }
