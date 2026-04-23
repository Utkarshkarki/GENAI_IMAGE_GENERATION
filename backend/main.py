"""
backend/main.py — FastAPI application entry point for AdSnap Studio
"""
import sys, os

# Allow importing from the project root (services/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.routers import generate, lifestyle, packshot, shadow, fill, erase, agent

load_dotenv()

app = FastAPI(
    title="AdSnap Studio API",
    description="FastAPI backend wrapping Bria AI services for AdSnap Studio",
    version="2.0.0",
)

# Allow requests from the React dev server and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.include_router(lifestyle.router, prefix="/api")
app.include_router(packshot.router, prefix="/api")
app.include_router(shadow.router, prefix="/api")
app.include_router(fill.router, prefix="/api")
app.include_router(erase.router, prefix="/api")
app.include_router(agent.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AdSnap Studio API"}
