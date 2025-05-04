# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import mood as mood_model
from collections import Counter
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Mood test verisi şeması
class MoodTestInput(BaseModel):
    answers: List[int]  # örneğin [2, 4, 3, 1, 5]
    user_id: int
    class_id: int

# Skora göre ruh hali belirle
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

# 1️⃣ Test verisi kaydetme
@router.post("/submit")
def submit_mood_test(test_data: MoodTestInput, db: Session = Depends(get_db)):
    score = sum(test_data.answers)
    mood = calculate_mood(score)

    entry = mood_model.MoodEntry(
        user_id=test_data.user_id,
        class_id=test_data.class_id,
        score=score,
        mood=mood
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "score": score,
        "mood": mood,
        "message": "Ruh hali başarıyla kaydedildi!"
    }

# 2️⃣ Sınıfa özel özet + şablon önerisi
@router.get("/class/{class_id}/summary")
def get_class_summary(class_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.class_id == class_id).all()

    if not entries:
        raise HTTPException(status_code=404, detail="Bu sınıf için veri bulunamadı.")

    scores = [e.score for e in entries]
    moods = [e.mood for e in entries]

    avg_score = sum(scores) / len(scores)
    mood_counts = dict(Counter(moods))
    dominant = max(mood_counts, key=mood_counts.get)

    template = {
        "Yorgun": "relax_focus",
        "Enerjik": "deep_dive"
    }.get(dominant, "balanced_engagement")

    return {
        "class_id": class_id,
        "average_score": round(avg_score, 2),
        "mood_distribution": mood_counts,
        "suggested_template": template
    }

# 3️⃣ Ruh hali önerisi
@router.get("/class/{class_id}/recommendation")
def get_recommendation_for_class(class_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.class_id == class_id).all()

    if not entries:
        raise HTTPException(status_code=404, detail="Bu sınıf için ruh hali verisi bulunamadı.")

    mood_counts = Counter([e.mood for e in entries])
    common_mood = max(mood_counts, key=mood_counts.get)

    recommendations = {
        "Yorgun": "Daha dinlendirici, sakin bir içerik önerilir.",
        "Dalgın": "Kısa ve dikkat çekici materyaller kullanın.",
        "Normal": "Dengeli ve standart bir içerik önerilir.",
        "Meraklı": "Etkileşimli etkinlikler ve sorular eklenebilir.",
        "Enerjik": "Grupla çalışma, tartışma gibi aktif yöntemler önerilir."
    }

    return {
        "most_common_mood": common_mood,
        "recommendation": recommendations.get(common_mood, "Genel bir öneri mevcut değil.")
    }

# 4️⃣ Yalnızca sınıf özeti (şablonsuz)
@router.get("/class-summary/{class_id}")
def get_class_mood_summary(class_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.class_id == class_id).all()

    if not entries:
        return {"message": "Bu sınıf için henüz veri yok."}

    mood_counts = Counter([e.mood for e in entries])
    common_mood = max(mood_counts, key=mood_counts.get)

    return {
        "class_id": class_id,
        "total_entries": len(entries),
        "mood_distribution": dict(mood_counts),
        "most_common_mood": common_mood
    }

@router.get("/history/{user_id}")
def get_user_mood_history(user_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(
        mood_model.MoodEntry.user_id == user_id
    ).order_by(mood_model.MoodEntry.timestamp.desc()).all()

    if not entries:
        raise HTTPException(status_code=404, detail="Bu kullanıcıya ait geçmiş veri bulunamadı.")

    return [
        {
            "timestamp": entry.timestamp.isoformat(),
            "score": entry.score,
            "mood": entry.mood
        }
        for entry in entries
    ]

@router.get("/mood-history/{user_id}/chart")
def get_mood_chart_data(user_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(
        mood_model.MoodEntry.user_id == user_id
    ).order_by(mood_model.MoodEntry.timestamp.asc()).all()

    if not entries:
        raise HTTPException(status_code=404, detail="Kullanıcının ruh hali geçmişi bulunamadı.")

    mood_data = [
        {
            "timestamp": entry.timestamp.isoformat(),
            "score": entry.score,
            "mood": entry.mood
        }
        for entry in entries
    ]

    return {
        "user_id": user_id,
        "mood_data": mood_data
    }

@router.get("/user/{user_id}/chart-data")
def get_user_mood_chart_data(user_id: int, db: Session = Depends(get_db)):
    entries = db.query(mood_model.MoodEntry).filter(
        mood_model.MoodEntry.user_id == user_id
    ).order_by(mood_model.MoodEntry.timestamp).all()

    if not entries:
        raise HTTPException(status_code=404, detail="Bu kullanıcı için ruh hali geçmişi bulunamadı.")

    labels = [entry.timestamp.strftime("%Y-%m-%d") for entry in entries]
    scores = [entry.score for entry in entries]
    moods = [entry.mood for entry in entries]

    return {
        "user_id": user_id,
        "labels": labels,
        "scores": scores,
        "moods": moods
    }

@router.get("/history/{user_id}")
def get_user_mood_history(
    user_id: int,
    current_user_id: int,  # Gerçek sistemde JWT token ile alınır
    db: Session = Depends(get_db)
):
    # Erişim kontrolü
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Başka bir kullanıcının verisine erişim izniniz yok.")

    entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.user_id == user_id).all()

    if not entries:
        return {"message": "Henüz ruh hali kaydınız bulunmamaktadır."}

    return [
        {
            "timestamp": entry.timestamp,
            "score": entry.score,
            "mood": entry.mood
        }
        for entry in entries
    ]
