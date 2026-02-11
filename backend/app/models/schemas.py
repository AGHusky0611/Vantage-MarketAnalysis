"""
Vantage Backend - Pydantic Schemas
Defines the shape of all API request/response data.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ──────────────────────────────────────────────
#  Market Data Schemas
# ──────────────────────────────────────────────

class OHLCVBar(BaseModel):
    """A single OHLCV candlestick bar."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class OverlayPoint(BaseModel):
    """A single data point for an overlay line/marker on the chart."""
    date: str
    value: Optional[float] = None


class MACDPoint(BaseModel):
    """A single MACD data point with all three values."""
    date: str
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None


class PredictionPoint(BaseModel):
    """A predicted future price point."""
    date: str
    value: float


class ChartOverlays(BaseModel):
    """Raw indicator series data for chart overlays."""
    sma_50: list[OverlayPoint] = []
    sma_200: list[OverlayPoint] = []
    sar: list[OverlayPoint] = []
    macd: list[MACDPoint] = []
    prediction: list[PredictionPoint] = []
    prediction_direction: str = Field(default="Neutral", description="Bullish / Bearish / Neutral")
    prediction_target: Optional[float] = Field(default=None, description="Predicted price target")


class IndicatorSignals(BaseModel):
    """Computed technical indicator signals."""
    trend: str = Field(..., description="Bullish / Bearish / Neutral")
    trend_detail: str = Field(..., description="Explanation of the SMA signal")

    sar_signal: str = Field(..., description="BUY / SELL / HOLD")
    sar_detail: str = Field(..., description="Explanation of the SAR signal")

    macd_signal: str = Field(..., description="Bullish / Bearish / Neutral")
    macd_detail: str = Field(..., description="Explanation of the MACD signal")

    obv_signal: str = Field(..., description="Confirmed / Divergence")
    obv_detail: str = Field(..., description="Explanation of the OBV signal")

    composite_signal: str = Field(..., description="BUY / SELL / HOLD")
    confidence: float = Field(..., ge=0, le=1, description="Confidence 0-1")


class SentimentResult(BaseModel):
    """Result from the sentiment analysis engine."""
    score: float = Field(..., ge=-1, le=1)
    label: str  # Panic / Bearish / Neutral / Bullish / Hype
    headline_count: int
    top_headlines: list[str]


class StockAnalysis(BaseModel):
    """Full analysis response for a single ticker."""
    ticker: str
    company_name: str
    current_price: float
    price_change: float
    price_change_pct: float
    ohlcv: list[OHLCVBar]
    indicators: IndicatorSignals
    overlays: Optional[ChartOverlays] = None
    sentiment: Optional[SentimentResult] = None
    analyzed_at: str


# ──────────────────────────────────────────────
#  Health / Utility Schemas
# ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
