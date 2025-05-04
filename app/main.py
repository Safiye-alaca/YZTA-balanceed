from fastapi import FastAPI
from app.db.database import Base, engine

# Model dosyaları (yalnızca veritabanı için kullanılır)
from app.models import user, mood as mood_model, presentation as presentation_model

# Router dosyaları (FastAPI endpoint'leri için)
from app.routers import auth, mood as mood_router, presentation as presentation_router

app = FastAPI()

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

# Router'ları ekle
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(mood_router.router, prefix="/mood", tags=["Mood"])
app.include_router(presentation_router.router, prefix="/presentation", tags=["Presentation"])

@app.get("/")
def read_root():
    return {"message": "BalanceED Backend is running 🎯"}

