from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers.chat import router as chat_router
from app.routers.admin import router as admin_router
from app.routers.developer import router as developer_router
from app.services.usage_logger import init_db

load_dotenv()

app = FastAPI(title="NutriBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(developer_router)
