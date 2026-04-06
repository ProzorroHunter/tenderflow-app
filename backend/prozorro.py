import httpx
from typing import Optional, List, Dict, Any

async def search_tenders(
    keywords: Optional[str] = None,
    cpv: Optional[str] = None,
    region: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    url = "https://public-api.prozorro.gov.ua/api/2.5/tenders"
    params: Dict[str, Any] = {
        "limit": limit,
        "opt_fields": "title,description,procuringEntity,amount,value,status,dateModified,auctionPeriod"
    }

    if keywords:
        params["text"] = keywords
    if cpv:
        params["cpv"] = cpv
    if region:
        params["procuringEntity.region"] = region

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        tenders = data.get("data", [])

        if min_amount is not None or max_amount is not None:
            filtered = []
            for tender in tenders:
                value = tender.get("value") or tender.get("amount")
                amount = value.get("amount") if isinstance(value, dict) else value
                if amount is not None:
                    try:
                        amount = float(amount)
                        if (min_amount is None or amount >= min_amount) and (max_amount is None or amount <= max_amount):
                            filtered.append(tender)
                    except (ValueError, TypeError):
                        filtered.append(tender)
                else:
                    filtered.append(tender)
            tenders = filtered

        return tenders
