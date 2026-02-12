"""
Vantage Backend - Market Data Service
Fetches live OHLCV data and company info from Yahoo Finance via yfinance.
Includes Anti-Blocking (User-Agent Spoofing) logic.
"""
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

def get_session():
    """
    Create a custom session to mimic a real Chrome browser.
    This prevents Yahoo from blocking the request as a 'bot'.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session

def get_stock_data(ticker: str, period: str = "1y", interval: str = "1d") -> dict:
    """
    Fetch OHLCV data and company metadata for a given ticker.
    Includes fallback logic and custom session handling.
    """
    # 1. Create Ticker object with CUSTOM SESSION
    session = get_session()
    stock = yf.Ticker(ticker, session=session)

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

    # 4. Safe data extraction (Hybrid approach for different yfinance versions)
    # Try to get price from history first (most reliable)
    current_price = 0.0
    previous_close = 0.0
    
    if not hist.empty:
        current_price = float(hist["Close"].iloc[-1])
        if len(hist) > 1:
            previous_close = float(hist["Close"].iloc[-2])
        else:
            previous_close = float(hist["Open"].iloc[-1])
            
    # Attempt to fill name from info
    # Note: accessing .info triggers a separate web request, which might also fail.
    # We use a default name if it fails.
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
        session = get_session()
        stock = yf.Ticker(ticker, session=session)
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