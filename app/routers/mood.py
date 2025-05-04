# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import mood as mood_model
from collections import Counter
from pydantic import BaseModel
from typing import List
from app.models import user as user_model


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

from datetime import datetime, date
from sqlalchemy import and_

@router.post("/submit")
def submit_mood_test(test_data: MoodTestInput, db: Session = Depends(get_db)):
    today = date.today()

    # Aynı gün içinde aynı kullanıcı ve sınıf için daha önce test yapılmış mı kontrol et
    existing = db.query(mood_model.MoodEntry).filter(
        and_(
            mood_model.MoodEntry.user_id == test_data.user_id,
            mood_model.MoodEntry.class_id == test_data.class_id,
            mood_model.MoodEntry.timestamp >= datetime.combine(today, datetime.min.time()),
            mood_model.MoodEntry.timestamp <= datetime.combine(today, datetime.max.time())
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Bugün bu test zaten gönderilmiş.")

    # Puan hesapla ve ruh hali belirle
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

@router.get("/teacher/{teacher_id}/student-latest-moods")
def get_teacher_students_latest_moods(teacher_id: int, db: Session = Depends(get_db)):
    from app.models import user as user_model

    # Bu öğretmene bağlı tüm öğrencileri bul
    students = db.query(user_model.User).filter(user_model.User.teacher_id == teacher_id).all()

    if not students:
        raise HTTPException(status_code=404, detail="Bu öğretmene bağlı öğrenci bulunamadı.")

    results = []
    for student in students:
        latest_entry = db.query(mood_model.MoodEntry).filter(
            mood_model.MoodEntry.user_id == student.id
        ).order_by(mood_model.MoodEntry.timestamp.desc()).first()

        if latest_entry:
            results.append({
                "student_id": student.id,
                "username": student.username,
                "score": latest_entry.score,
                "mood": latest_entry.mood,
                "timestamp": latest_entry.timestamp
            })

    return results

@router.get("/teacher/{teacher_id}/student/{student_id}/history")
def get_student_history_by_teacher(
    teacher_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    # Önce öğrencinin bu öğretmene bağlı olup olmadığını kontrol et
    from app.models import user as user_model
    student = db.query(user_model.User).filter(
        user_model.User.id == student_id,
        user_model.User.teacher_id == teacher_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Öğretmene bağlı böyle bir öğrenci bulunamadı.")

    # Öğrencinin mood geçmişi
    history = db.query(mood_model.MoodEntry).filter(
        mood_model.MoodEntry.user_id == student_id
    ).order_by(mood_model.MoodEntry.timestamp.desc()).all()

    if not history:
        raise HTTPException(status_code=404, detail="Bu öğrenciye ait geçmiş veri bulunamadı.")

    return [
        {
            "timestamp": entry.timestamp,
            "score": entry.score,
            "mood": entry.mood
        }
        for entry in history
    ]

@router.get("/teacher/{teacher_id}/class-summary")
def get_teacher_class_mood_summary(teacher_id: int, db: Session = Depends(get_db)):
    # Öğretmene ait öğrencileri bul
    students = db.query(user_model.User).filter(user_model.User.teacher_id == teacher_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="Bu öğretmene ait öğrenci bulunamadı.")

    student_ids = [s.id for s in students]

    # Öğrencilerin tüm mood girişlerini al
    mood_entries = db.query(mood_model.MoodEntry).filter(mood_model.MoodEntry.user_id.in_(student_ids)).all()
    if not mood_entries:
        return {"message": "Henüz bu sınıfa ait ruh hali verisi girilmedi."}

    # Verileri özetle
    scores = [e.score for e in mood_entries]
    moods = [e.mood for e in mood_entries]
    average_score = round(sum(scores) / len(scores), 2)
    mood_counts = dict(Counter(moods))
    most_common_mood = max(mood_counts, key=mood_counts.get)

    return {
        "teacher_id": teacher_id,
        "total_students": len(students),
        "total_entries": len(mood_entries),
        "average_score": average_score,
        "mood_distribution": mood_counts,
        "most_common_mood": most_common_mood
    }

from sqlalchemy import desc
from app.models import user as user_model  # Eksikse bunu en üste ekle

@router.get("/teacher/{teacher_id}/students-latest-moods")
def get_students_latest_moods(teacher_id: int, db: Session = Depends(get_db)):
    # Öğretmenin öğrencilerini bul
    students = db.query(user_model.User).filter(user_model.User.teacher_id == teacher_id).all()
    if not students:
        return {"message": "Bu öğretmene ait öğrenci bulunamadı."}

    result = []
    for student in students:
        latest_mood = (
            db.query(mood_model.MoodEntry)
            .filter(mood_model.MoodEntry.user_id == student.id)
            .order_by(desc(mood_model.MoodEntry.timestamp))
            .first()
        )
        if latest_mood:
            result.append({
                "student_id": student.id,
                "username": student.username,
                "mood": latest_mood.mood,
                "score": latest_mood.score,
                "timestamp": latest_mood.timestamp
            })

    if not result:
        return {"message": "Öğrencilere ait ruh hali verisi bulunamadı."}

    return result

