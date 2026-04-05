import httpx
from typing import Optional, List, Dict
from datetime import datetime, timedelta

async def search_tenders(
    keywords: Optional[str] = None,
    cpv: Optional[str] = None,
    region: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Поиск тендеров через публичный API Prozorro.
    """
    base_url = "https://public-api.prozorro.gov.ua/api/2.5/tenders"
    params = {
        "limit": limit,
        "opt_fields": "title,description,procuringEntity,amount,value,auctionPeriod,status,dateModified"
    }

    if keywords:
        params["text"] = keywords
    if cpv:
        params["cpv"] = cpv
    if region:
        params["procuringEntity.region"] = region  # пример фильтра

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        tenders = data.get("data", [])

        # Простая фильтрация по сумме (если указана)
        if min_amount or max_amount:
            filtered = []
            for tender in tenders:
                amount = tender.get("value", {}).get("amount") or tender.get("amount")
                if amount:
                    amount = float(amount)
                    if (min_amount is None or amount >= min_amount) and (max_amount is None or amount <= max_amount):
                        filtered.append(tender)
                else:
                    filtered.append(tender)
            tenders = filtered

        return tenders