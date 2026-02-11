"""
Vantage Backend - Market Router
Endpoints for stock analysis, indicators, and sentiment.
"""
import asyncio
import logging
from functools import partial

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional

from app.services.market_data import get_stock_data
from app.services.indicators import calculate_indicators, calculate_overlays
from app.services.sentiment import analyze_sentiment
from app.models.schemas import StockAnalysis, OHLCVBar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["Market"])

# ── Popular tickers by category ────────────────────────────────
WATCHLIST = {
    "stocks": [
        {"ticker": "AAPL", "name": "Apple"},
        {"ticker": "MSFT", "name": "Microsoft"},
        {"ticker": "GOOGL", "name": "Alphabet"},
        {"ticker": "AMZN", "name": "Amazon"},
        {"ticker": "TSLA", "name": "Tesla"},
        {"ticker": "NVDA", "name": "NVIDIA"},
        {"ticker": "META", "name": "Meta"},
        {"ticker": "NFLX", "name": "Netflix"},
        {"ticker": "AMD", "name": "AMD"},
        {"ticker": "DIS", "name": "Disney"},
    ],
    "crypto": [
        {"ticker": "BTC-USD", "name": "Bitcoin"},
        {"ticker": "ETH-USD", "name": "Ethereum"},
        {"ticker": "SOL-USD", "name": "Solana"},
        {"ticker": "BNB-USD", "name": "BNB"},
        {"ticker": "XRP-USD", "name": "XRP"},
        {"ticker": "ADA-USD", "name": "Cardano"},
        {"ticker": "DOGE-USD", "name": "Dogecoin"},
        {"ticker": "AVAX-USD", "name": "Avalanche"},
        {"ticker": "DOT-USD", "name": "Polkadot"},
        {"ticker": "MATIC-USD", "name": "Polygon"},
    ],
    "tokens": [
        {"ticker": "LINK-USD", "name": "Chainlink"},
        {"ticker": "UNI-USD", "name": "Uniswap"},
        {"ticker": "AAVE-USD", "name": "Aave"},
        {"ticker": "MKR-USD", "name": "Maker"},
        {"ticker": "CRV-USD", "name": "Curve"},
        {"ticker": "LDO-USD", "name": "Lido DAO"},
        {"ticker": "ARB-USD", "name": "Arbitrum"},  # Changed from ARB11841-USD
        {"ticker": "OP-USD", "name": "Optimism"},
        {"ticker": "GRT-USD", "name": "The Graph"},
        {"ticker": "SNX-USD", "name": "Synthetix"},
    ],
}


@router.get("/analyze/{ticker}", response_model=StockAnalysis)
async def analyze_stock(
    ticker: str,
    period: str = Query(default="1y", description="Data period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,max"),
    interval: str = Query(default="1d", description="Data interval: 1m,5m,15m,30m,1h,1d,1wk,1mo"),
    include_sentiment: bool = Query(default=True, description="Include news sentiment analysis"),
):
    """
    Full analysis for a stock ticker.
    Returns OHLCV data, technical indicator signals, and optional sentiment analysis.
    """
    try:
        # Determine if this is intraday data
        is_intraday = interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h")

        loop = asyncio.get_event_loop()

        # 1. Fetch market data (run blocking yfinance call in thread pool)
        data = await loop.run_in_executor(None, partial(get_stock_data, ticker, period, interval))

        # 2b. Calculate chart overlay data (SMA lines, SAR dots, MACD, prediction)
        #     Run overlays FIRST so we can feed prediction_direction into composite
        overlays = await loop.run_in_executor(None, partial(calculate_overlays, data["history"], is_intraday=is_intraday))

        # 2. Calculate technical indicators (using prediction direction for consistency)
        prediction_direction = overlays.prediction_direction if overlays else "Neutral"
        indicators = await loop.run_in_executor(
            None, partial(calculate_indicators, data["history"], prediction_direction=prediction_direction)
        )

        # 3. Build OHLCV response
        hist = data["history"]

        def _format_date(idx):
            """Format index as YYYY-MM-DD for daily or Unix timestamp for intraday."""
            if is_intraday:
                # lightweight-charts needs Unix timestamp (seconds) for intraday
                import calendar
                ts = idx
                if hasattr(ts, 'timestamp'):
                    return int(ts.timestamp())
                return str(ts)
            else:
                return str(idx.date()) if hasattr(idx, "date") else str(idx)

        ohlcv = [
            OHLCVBar(
                date=str(_format_date(idx)),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=int(row["Volume"]),
            )
            for idx, row in hist.iterrows()
        ]

        # 4. Sentiment analysis (optional, run in thread pool)
        sentiment = None
        if include_sentiment:
            try:
                sentiment = await loop.run_in_executor(None, analyze_sentiment, ticker)
            except Exception:
                sentiment = None  # Gracefully skip if news fetch fails

        # 5. Calculate price change
        current_price = data["current_price"]
        previous_close = data["previous_close"]
        price_change = round(current_price - previous_close, 2)
        price_change_pct = round((price_change / previous_close) * 100, 2) if previous_close else 0

        return StockAnalysis(
            ticker=data["ticker"],
            company_name=data["company_name"],
            current_price=round(current_price, 2),
            price_change=price_change,
            price_change_pct=price_change_pct,
            ohlcv=ohlcv,
            indicators=indicators,
            overlays=overlays,
            sentiment=sentiment,
            analyzed_at=datetime.now().isoformat(),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/price/{ticker}")
async def get_price(ticker: str):
    """Quick endpoint to get just the current price of a stock."""
    try:
        data = get_stock_data(ticker, period="5d")
        return {
            "ticker": data["ticker"],
            "company_name": data["company_name"],
            "current_price": round(data["current_price"], 2),
            "previous_close": round(data["previous_close"], 2),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sentiment/{ticker}")
async def get_sentiment(ticker: str):
    """Get standalone sentiment analysis for a ticker."""
    try:
        result = analyze_sentiment(ticker)
        return {"ticker": ticker.upper(), **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.get("/watchlist")
async def get_watchlist():
    """
    Return the curated list of popular stocks, crypto, and tokens
    with live price and daily % change for each.
    """
    results = {}
    for category, items in WATCHLIST.items():
        category_data = []
        for item in items:
            try:
                data = get_stock_data(item["ticker"], period="5d")
                current = data["current_price"]
                prev = data["previous_close"]
                change = round(current - prev, 2)
                change_pct = round((change / prev) * 100, 2) if prev else 0
                category_data.append({
                    "ticker": item["ticker"],
                    "name": item["name"],
                    "price": round(current, 2),
                    "change": change,
                    "change_pct": change_pct,
                })
            except Exception:
                category_data.append({
                    "ticker": item["ticker"],
                    "name": item["name"],
                    "price": None,
                    "change": None,
                    "change_pct": None,
                })
        results[category] = category_data
    return results


@router.get("/watchlist/category/{category}")
async def get_watchlist_category(category: str):
    """Get prices for a single category: stocks, crypto, or tokens."""
    if category not in WATCHLIST:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found. Use: stocks, crypto, tokens")

    items = WATCHLIST[category]
    results = []
    for item in items:
        try:
            data = get_stock_data(item["ticker"], period="5d")
            current = data["current_price"]
            prev = data["previous_close"]
            change = round(current - prev, 2)
            change_pct = round((change / prev) * 100, 2) if prev else 0
            results.append({
                "ticker": item["ticker"],
                "name": item["name"],
                "price": round(current, 2),
                "change": change,
                "change_pct": change_pct,
            })
        except Exception:
            results.append({
                "ticker": item["ticker"],
                "name": item["name"],
                "price": None,
                "change": None,
                "change_pct": None,
            })
    return {"category": category, "items": results}
