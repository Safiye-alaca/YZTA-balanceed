from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
import os
from typing import List

router = APIRouter()

UPLOAD_DIR = "presentations"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_presentation(
    class_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_location = f"{UPLOAD_DIR}/{class_id}_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    from app.models import presentation as presentation_model
    from datetime import datetime

    # Veritabanına kayıt
    new_presentation = presentation_model.Presentation(
        class_id=class_id,
        title=title,
        file_path=file_location,
        upload_timestamp=datetime.utcnow()
    )
    db.add(new_presentation)
    db.commit()
    db.refresh(new_presentation)

    return {
        "message": "Sunum başarıyla yüklendi.",
        "file_path": file_location,
        "title": title,
        "class_id": class_id
    }


@router.get("/presentations/{class_id}")
def list_presentations(class_id: int):
    files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(f"{class_id}_")]
    return {
        "class_id": class_id,
        "presentations": files
    }


from fastapi import HTTPException
from typing import List
from app.models import presentation as presentation_model
from datetime import datetime

@router.get("/class/{class_id}", response_model=List[dict])
def get_presentations_for_class(class_id: int, db: Session = Depends(get_db)):
    presentations = db.query(presentation_model.Presentation).filter(
        presentation_model.Presentation.class_id == class_id
    ).all()

    if not presentations:
        raise HTTPException(status_code=404, detail="Bu sınıf için sunum bulunamadı.")

    return [
        {
            "title": p.title,
            "file_path": p.file_path,
            "upload_timestamp": p.upload_timestamp
        }
        for p in presentations
    ]


from sqlalchemy import desc  # en son ekleneni bulmak için

@router.get("/latest/{class_id}")
def get_latest_presentation(class_id: int, db: Session = Depends(get_db)):
    latest_presentation = (
        db.query(presentation_model.Presentation)
        .filter(presentation_model.Presentation.class_id == class_id)
        .order_by(presentation_model.Presentation.upload_timestamp.desc())
        .first()
    )

    if not latest_presentation:
        return {"message": "Henüz bu sınıfa ait bir sunum yüklenmedi."}

    return {
        "class_id": latest_presentation.class_id,
        "filename": latest_presentation.file_path,
        "title": latest_presentation.title,
        "timestamp": latest_presentation.upload_timestamp.isoformat(),
    }

@router.get("/student/class/{class_id}/presentations")
def get_presentations_for_student(class_id: int, db: Session = Depends(get_db)):
    from app.models import presentation as presentation_model

    presentations = db.query(presentation_model.Presentation).filter(
        presentation_model.Presentation.class_id == class_id
    ).all()

    return [
        {
            "title": p.title,
            "download_link": f"/files/{p.file_path}",
            "uploaded_at": p.upload_timestamp
        } for p in presentations
    ]

@router.get("/student/{class_id}/presentations")
def get_presentations_for_student(class_id: int, db: Session = Depends(get_db)):
    from app.models import presentation as presentation_model

    presentations = db.query(presentation_model.Presentation).filter(
        presentation_model.Presentation.class_id == class_id
    ).all()

    return [
        {
            "title": p.title,
            "download_link": f"/files/{p.file_path}",
            "uploaded_at": p.upload_timestamp
        } for p in presentations
    ]

@router.get("/student/{student_id}/presentation/{presentation_id}/detail")
def get_presentation_detail_for_student(student_id: int, presentation_id: int, db: Session = Depends(get_db)):
    from app.models import user as user_model
    from app.models import presentation as presentation_model

    # Öğrenciyi kontrol et
    student = db.query(user_model.User).filter(user_model.User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı.")

    # Sunumu kontrol et: öğrenci ile aynı sınıfa ait mi
    presentation = db.query(presentation_model.Presentation).filter(
        presentation_model.Presentation.id == presentation_id,
        presentation_model.Presentation.class_id == student.class_id
    ).first()

    if not presentation:
        raise HTTPException(status_code=404, detail="Bu sunum bu öğrenciye ait sınıfla eşleşmiyor.")

    # Sunumu yükleyen öğretmeni al
    teacher = db.query(user_model.User).filter(user_model.User.id == presentation.teacher_id).first()
    teacher_name = teacher.username if teacher else "Bilinmiyor"

    return {
        "presentation_id": presentation.id,
        "title": presentation.title,
        "description": presentation.description,
        "uploaded_at": presentation.upload_timestamp,
        "teacher_name": teacher_name,
        "download_link": f"/files/{presentation.file_path}"
    }
