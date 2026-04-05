from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import Optional

# Импортируем функцию поиска
from prozorro import search_tenders

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
        "message": "ProzorroHunter backend запущен успешно",
        "status": "ok",
        "version": "0.1.0"
    }

@app.get("/search")
async def search(
    keywords: Optional[str] = Query(None, description="Ключевые слова для поиска"),
    cpv: Optional[str] = Query(None, description="CPV-код"),
    region: Optional[str] = Query(None, description="Регион"),
    min_amount: Optional[float] = Query(None, description="Минимальная сумма"),
    max_amount: Optional[float] = Query(None, description="Максимальная сумма"),
    limit: int = Query(20, description="Количество результатов")
):
    """
    Поиск тендеров по параметрам.
    Пример: /search?keywords=будівництво&region=Харківська&min_amount=100000
    """
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
        "tenders": tenders
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)