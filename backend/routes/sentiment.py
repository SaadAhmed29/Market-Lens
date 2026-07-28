"""
MarketLens — Sentiment Router
Exposes GET /api/sentiment, which returns a single aggregated payload
covering all sentiment analysis widgets.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.modules.sentiment import get_sentiment_data

router = APIRouter(prefix="/api", tags=["sentiment"])


@router.get("/sentiment")
def sentiment() -> JSONResponse:
    """
    Return all sentiment data in one response.

    Response shape::

        {
            "status": "success",
            "data": {
                "sample_posts": {
                    "<SYMBOL>": [
                        {
                            "symbol": str,
                            "title": str,
                            "body": str,
                            "comments": [str, ...],
                            "label": "bullish" | "bearish" | "neutral",
                            "confidence_score": float
                        },
                        ...
                    ],
                    ...
                },
                "overall_distribution": {
                    "bullish": int,
                    "bearish": int,
                    "neutral": int
                },
                "per_symbol_distribution": {
                    "<SYMBOL>": {"bullish": int, "bearish": int, "neutral": int},
                    ...
                },
                "symbol_sentiment": {
                    "<SYMBOL>": "bullish" | "bearish" | "neutral",
                    ...
                },
                "market_sentiment": "bullish" | "bearish" | "neutral"
            }
        }

    On failure returns HTTP 500 with::

        {"status": "error", "message": str}
    """
    try:
        data = get_sentiment_data()
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )
