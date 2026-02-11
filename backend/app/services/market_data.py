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

    Args:
        ticker: Stock symbol (e.g., "AAPL", "TSLA").
        period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max.
        interval: Data interval - 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo.

    Returns:
        Dictionary with company info and OHLCV DataFrame.
    """
    stock = yf.Ticker(ticker)

    # Fetch historical OHLCV data
    hist: pd.DataFrame = stock.history(period=period, interval=interval)

    if hist.empty:
        raise ValueError(f"No data found for ticker '{ticker}'. Verify the symbol is correct.")

    # Get company info (gracefully handle missing fields)
    info = stock.info or {}

    return {
        "ticker": ticker.upper(),
        "company_name": info.get("shortName", info.get("longName", ticker.upper())),
        "current_price": info.get("currentPrice", float(hist["Close"].iloc[-1])),
        "previous_close": info.get("previousClose", float(hist["Close"].iloc[-2]) if len(hist) > 1 else 0),
        "history": hist,
    }


def get_news_headlines(ticker: str, max_headlines: int = 10) -> list[str]:
    """
    Fetch recent news headlines for a ticker via yfinance.

    Args:
        ticker: Stock symbol.
        max_headlines: Maximum number of headlines to return.

    Returns:
        List of headline strings.
    """
    stock = yf.Ticker(ticker)
    news = stock.news or []

    headlines = []
    for article in news[:max_headlines]:
        # yfinance >= 1.0 nests title under "content"
        content = article.get("content", {})
        title = content.get("title", "") if isinstance(content, dict) else ""
        # Fallback for older yfinance versions
        if not title:
            title = article.get("title", "")
        if title:
            headlines.append(title)

    return headlines
