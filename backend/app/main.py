from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.conversations import router as conversations_router
from app.routers.profile import router as profile_router
from app.routers.admin import router as admin_router
from app.routers.developer import router as developer_router
from app.services.auth import init_auth_db
from app.services.persistence import init_persistence
from app.services.usage_logger import init_db

load_dotenv()

app = FastAPI(title="NutriBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
init_auth_db()
init_persistence()


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(profile_router)
app.include_router(admin_router)
app.include_router(developer_router)
