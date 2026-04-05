from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import Optional

# Правильный импорт из папки app
from app.prozorro import search_tenders

load_dotenv()

app = FastAPI(
    title="ProzorroHunter — TenderFlow",
    description="Автоматический трекер тендеров Prozorro 24/7",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "ProzorroHunter backend успешно запущен",
        "status": "ok",
        "version": "0.1.0"
    }

@app.get("/search")
async def search_tenders_endpoint(
    keywords: Optional[str] = Query(None, description="Ключевые слова, например: будівництво Харків"),
    cpv: Optional[str] = Query(None, description="CPV-код"),
    region: Optional[str] = Query(None, description="Регион, например: Харківська"),
    min_amount: Optional[float] = Query(None, description="Минимальная сумма тендера"),
    max_amount: Optional[float] = Query(None, description="Максимальная сумма тендера"),
    limit: int = Query(20, ge=1, le=100, description="Количество результатов")
):
    """Поиск тендеров по заданным параметрам"""
    tenders = await search_tenders(
        keywords=keywords,
        cpv=cpv,
        region=region,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit
    )
    return {
        "count": len(tenders),
        "tenders": tenders[:limit]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)