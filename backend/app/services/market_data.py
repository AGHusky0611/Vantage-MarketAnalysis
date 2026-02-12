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
    Relies on yfinance internal handling (via curl_cffi) to avoid blocks.
    """
    # 1. Create Ticker object (Let yfinance handle the session!)
    stock = yf.Ticker(ticker)

    # 2. Fetch historical OHLCV data with error handling
    try:
        # Attempt 1: Requested period
        hist: pd.DataFrame = stock.history(period=period, interval=interval)
        
        # Fallback: If '1y' returns empty (common on servers), try '5d'
        if hist.empty:
            print(f"Warning: {period} data empty for {ticker}. Trying fallback to 5d.")
            hist = stock.history(period="5d", interval=interval)
            
        # If STILL empty, raise error
        if hist.empty:
            raise ValueError(f"No data found for '{ticker}'. Yahoo is blocking the Render IP.")
            
    except Exception as e:
        raise ValueError(f"Yahoo Finance Error for {ticker}: {str(e)}")

    # 3. Get company info (gracefully handle missing fields)
    try:
        # Use fast_info if available (newer yfinance) or fallback to info
        info = stock.fast_info
        # Map fast_info keys to our expected schema if possible, or fallback to standard info
        if not info:
             info = stock.info or {}
    except:
        info = {}

    # 4. Safe data extraction
    current_price = 0.0
    previous_close = 0.0
    
    if not hist.empty:
        current_price = float(hist["Close"].iloc[-1])
        if len(hist) > 1:
            previous_close = float(hist["Close"].iloc[-2])
        else:
            previous_close = float(hist["Open"].iloc[-1])
            
    try:
        company_name = stock.info.get("shortName", ticker.upper())
    except:
        company_name = ticker.upper()

    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "current_price": current_price,
        "previous_close": previous_close,
        "history": hist,
    }

def get_news_headlines(ticker: str, max_headlines: int = 10) -> list[str]:
    """
    Fetch recent news headlines for a ticker via yfinance.
    """
    try:
        # Let yfinance handle the session
        stock = yf.Ticker(ticker)
        news = stock.news or []

        headlines = []
        for article in news[:max_headlines]:
            content = article.get("content", {})
            title = content.get("title", "") if isinstance(content, dict) else ""
            
            if not title:
                title = article.get("title", "")
                
            if title:
                headlines.append(title)

        return headlines
    except Exception:
        return []