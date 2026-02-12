"""
Vantage Backend - Market Data Service
Fetches live OHLCV data and company info from Yahoo Finance via yfinance.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_stock_data(ticker: str, period: str = "1y", interval: str = "1d") -> dict:
    """
    Fetch OHLCV data and company metadata for a given ticker.
    Includes fallback logic to prevent 404s on servers.
    """
    # 1. Create Ticker object
    stock = yf.Ticker(ticker)

    # 2. Fetch historical OHLCV data with error handling
    try:
        hist: pd.DataFrame = stock.history(period=period, interval=interval)
        
        # FALLBACK LOGIC: If '1y' returns empty (common on servers), try '5d'
        if hist.empty:
            print(f"Warning: {period} data empty for {ticker}. Trying fallback to 5d.")
            hist = stock.history(period="5d", interval=interval)
            
        # If STILL empty, then raise error
        if hist.empty:
            raise ValueError(f"No data found for '{ticker}'. Yahoo may be blocking requests or ticker is invalid.")
            
    except Exception as e:
        raise ValueError(f"Yahoo Finance Error for {ticker}: {str(e)}")

    # 3. Get company info (gracefully handle missing fields)
    try:
        info = stock.info or {}
    except:
        info = {}

    # 4. Safe data extraction
    current_price = info.get("currentPrice")
    if current_price is None:
        if not hist.empty:
            current_price = float(hist["Close"].iloc[-1])
        else:
            current_price = 0.0

    previous_close = info.get("previousClose")
    if previous_close is None:
        if len(hist) > 1:
            previous_close = float(hist["Close"].iloc[-2])
        else:
            previous_close = current_price

    return {
        "ticker": ticker.upper(),
        "company_name": info.get("shortName", info.get("longName", ticker.upper())),
        "current_price": current_price,
        "previous_close": previous_close,
        "history": hist,
    }

def get_news_headlines(ticker: str, max_headlines: int = 10) -> list[str]:
    """
    Fetch recent news headlines for a ticker via yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news or []

        headlines = []
        for article in news[:max_headlines]:
            # yfinance >= 1.0 nests title under "content"
            content = article.get("content", {})
            title = content.get("title", "") if isinstance(content, dict) else ""
            
            # Fallback for older yfinance versions or different structures
            if not title:
                title = article.get("title", "")
                
            if title:
                headlines.append(title)

        return headlines
    except Exception:
        return [] # Return empty list instead of crashing if news fails