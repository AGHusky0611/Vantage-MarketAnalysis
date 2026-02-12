"""
Vantage Backend - Technical Indicators Service
Calculates SMA, Parabolic SAR, MACD, and OBV from OHLCV data.
"""
import pandas as pd
import numpy as np
from datetime import timedelta
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.arima.model import ARIMA
from app.models.schemas import (
    IndicatorSignals,
    ChartOverlays,
    OverlayPoint,
    MACDPoint,
    PredictionPoint,
)



    close: pd.Series, dates: list[str],
    lookback: int = 60, forecast_days: int = 30,
) -> tuple[list[PredictionPoint], str, float | None]:
    """
    ARIMA-based price prediction.
    Uses the last `lookback` days to project `forecast_days` into the future.
    Returns the prediction points, direction, and target price.
    """
    if len(close) < lookback:
        lookback = len(close)
    if lookback < 10:
        return [], "Neutral", None

    # Use last `lookback` prices
    recent = close.iloc[-lookback:]
    # Fit ARIMA model (order can be tuned)
    try:
        model = ARIMA(recent, order=(1,1,1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=forecast_days)
    except Exception:
        return [], "Neutral", None

    # Direction based on last forecasted value vs last actual
    if len(forecast) > 0:
        last_actual = float(recent.iloc[-1])
        last_forecast = float(forecast.iloc[-1])
        if last_forecast > last_actual * 1.01:
            direction = "Bullish"
        elif last_forecast < last_actual * 0.99:
            direction = "Bearish"
        else:
            direction = "Neutral"
    else:
        direction = "Neutral"

    # Generate prediction points
    last_date = pd.Timestamp(dates[-1])
    prediction = []
    # Anchor point
    prediction.append(PredictionPoint(
        date=dates[-1],
        value=round(float(recent.iloc[-1]), 2),
    ))
    for i, value in enumerate(forecast):
        future_date = last_date + timedelta(days=i+1)
        while future_date.weekday() >= 5:
            future_date += timedelta(days=1)
        prediction.append(PredictionPoint(
            date=str(future_date.date()),
            value=round(float(value), 2),
        ))

    target = round(float(forecast.iloc[-1]), 2) if len(forecast) > 0 else None
    return prediction, direction, target
def calculate_indicators(
    hist: pd.DataFrame,
    prediction_direction: str = "Neutral",
) -> IndicatorSignals:
    """
    Run all technical analysis calculations on historical OHLCV data.

    Args:
        hist: pandas DataFrame with columns [Open, High, Low, Close, Volume].
        prediction_direction: "Bullish", "Bearish", or "Neutral" from the
            linear-regression prediction, so the composite signal stays
            consistent with the prediction line on the chart.

    Returns:
        IndicatorSignals with computed signals and a composite recommendation.
    """
    close = hist["Close"]
    high = hist["High"]
    low = hist["Low"]
    volume = hist["Volume"]

    # ── 1. SMA (Simple Moving Average) ──────────────────────────
    trend, trend_detail = _calculate_sma(close)

    # ── 2. Parabolic SAR ────────────────────────────────────────
    sar_signal, sar_detail = _calculate_parabolic_sar(high, low, close)

    # ── 3. MACD ─────────────────────────────────────────────────
    macd_signal, macd_detail = _calculate_macd(close)

    # ── 4. OBV (On-Balance Volume) ──────────────────────────────
    obv_signal, obv_detail = _calculate_obv(close, volume)

    # ── 5. Composite Signal (includes prediction direction) ─────
    composite_signal, confidence = _composite(
        trend, sar_signal, macd_signal, obv_signal, prediction_direction
    )

    return IndicatorSignals(
        trend=trend,
        trend_detail=trend_detail,
        sar_signal=sar_signal,
        sar_detail=sar_detail,
        macd_signal=macd_signal,
        macd_detail=macd_detail,
        obv_signal=obv_signal,
        obv_detail=obv_detail,
        composite_signal=composite_signal,
        confidence=confidence,
    )


# ════════════════════════════════════════════════════════════════
#  Individual Indicator Calculations
# ════════════════════════════════════════════════════════════════

def _calculate_sma(close: pd.Series) -> tuple[str, str]:
    """
    SMA-50 & SMA-200 trend identification.
    - Price > SMA-50 → Bullish
    - Price < SMA-50 → Bearish
    - SMA-50 crossing above SMA-200 → Golden Cross (strong bullish)
    """
    current_price = float(close.iloc[-1])

    sma_50 = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else None
    sma_200 = float(close.rolling(window=200).mean().iloc[-1]) if len(close) >= 200 else None

    if sma_50 is None:
        return "Neutral", "Insufficient data for SMA-50 (need 50+ bars)."

    if current_price > sma_50:
        trend = "Bullish"
        detail = f"Price (${current_price:.2f}) is above SMA-50 (${sma_50:.2f})."
    else:
        trend = "Bearish"
        detail = f"Price (${current_price:.2f}) is below SMA-50 (${sma_50:.2f})."

    # Golden / Death Cross check
    if sma_200 is not None:
        if sma_50 > sma_200:
            detail += f" Golden Cross: SMA-50 (${sma_50:.2f}) > SMA-200 (${sma_200:.2f})."
        else:
            detail += f" Death Cross: SMA-50 (${sma_50:.2f}) < SMA-200 (${sma_200:.2f})."

    return trend, detail


def _calculate_parabolic_sar(
    high: pd.Series, low: pd.Series, close: pd.Series,
    af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.20,
) -> tuple[str, str]:
    """
    Parabolic Stop and Reverse (SAR).
    - SAR below price → BUY (uptrend)
    - SAR above price → SELL (downtrend)
    """
    length = len(close)
    if length < 5:
        return "HOLD", "Insufficient data for Parabolic SAR."

    sar = np.zeros(length)
    af = af_start
    is_uptrend = True
    extreme_point = float(high.iloc[0])
    sar[0] = float(low.iloc[0])

    for i in range(1, length):
        prev_sar = sar[i - 1]

        if is_uptrend:
            sar[i] = prev_sar + af * (extreme_point - prev_sar)
            # Clamp: SAR cannot be above the two prior lows
            sar[i] = min(sar[i], float(low.iloc[max(0, i - 1)]), float(low.iloc[max(0, i - 2)]))

            if float(low.iloc[i]) < sar[i]:
                # Trend reversal → downtrend
                is_uptrend = False
                sar[i] = extreme_point
                extreme_point = float(low.iloc[i])
                af = af_start
            else:
                if float(high.iloc[i]) > extreme_point:
                    extreme_point = float(high.iloc[i])
                    af = min(af + af_increment, af_max)
        else:
            sar[i] = prev_sar + af * (extreme_point - prev_sar)
            # Clamp: SAR cannot be below the two prior highs
            sar[i] = max(sar[i], float(high.iloc[max(0, i - 1)]), float(high.iloc[max(0, i - 2)]))

            if float(high.iloc[i]) > sar[i]:
                # Trend reversal → uptrend
                is_uptrend = True
                sar[i] = extreme_point
                extreme_point = float(high.iloc[i])
                af = af_start
            else:
                if float(low.iloc[i]) < extreme_point:
                    extreme_point = float(low.iloc[i])
                    af = min(af + af_increment, af_max)

    current_price = float(close.iloc[-1])
    current_sar = float(sar[-1])

    if current_sar < current_price:
        signal = "BUY"
        detail = f"SAR (${current_sar:.2f}) is below price (${current_price:.2f}) → Uptrend. Entry signal."
    else:
        signal = "SELL"
        detail = f"SAR (${current_sar:.2f}) is above price (${current_price:.2f}) → Downtrend. Exit signal."

    return signal, detail


def _calculate_macd(
    close: pd.Series,
    fast: int = 12, slow: int = 26, signal_period: int = 9,
) -> tuple[str, str]:
    """
    MACD (Moving Average Convergence Divergence).
    - MACD line crosses above Signal line → Bullish momentum
    - MACD line crosses below Signal line → Bearish momentum
    """
    if len(close) < slow + signal_period:
        return "Neutral", f"Insufficient data for MACD (need {slow + signal_period}+ bars)."

    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    current_macd = float(macd_line.iloc[-1])
    current_signal = float(signal_line.iloc[-1])
    current_hist = float(histogram.iloc[-1])
    prev_hist = float(histogram.iloc[-2])

    if current_macd > current_signal:
        signal = "Bullish"
        detail = f"MACD ({current_macd:.4f}) is above Signal ({current_signal:.4f}). Bullish momentum."
    else:
        signal = "Bearish"
        detail = f"MACD ({current_macd:.4f}) is below Signal ({current_signal:.4f}). Bearish momentum."

    # Check for crossover (histogram sign change)
    if prev_hist < 0 and current_hist > 0:
        detail += " Recent bullish crossover detected."
    elif prev_hist > 0 and current_hist < 0:
        detail += " Recent bearish crossover detected."

    return signal, detail


def _calculate_obv(close: pd.Series, volume: pd.Series) -> tuple[str, str]:
    """
    On-Balance Volume (OBV).
    - Rising price + rising OBV → Trend confirmed
    - Rising price + falling OBV → Divergence (likely reversal)
    """
    if len(close) < 20:
        return "Confirmed", "Insufficient data for OBV divergence check."

    # Calculate OBV
    obv = pd.Series(0, index=close.index, dtype=float)
    for i in range(1, len(close)):
        if float(close.iloc[i]) > float(close.iloc[i - 1]):
            obv.iloc[i] = obv.iloc[i - 1] + float(volume.iloc[i])
        elif float(close.iloc[i]) < float(close.iloc[i - 1]):
            obv.iloc[i] = obv.iloc[i - 1] - float(volume.iloc[i])
        else:
            obv.iloc[i] = obv.iloc[i - 1]

    # Compare trends over the last 20 bars
    lookback = 20
    price_trend = float(close.iloc[-1]) - float(close.iloc[-lookback])
    obv_trend = float(obv.iloc[-1]) - float(obv.iloc[-lookback])

    price_rising = price_trend > 0
    obv_rising = obv_trend > 0

    if price_rising and obv_rising:
        return "Confirmed", "Price and OBV both rising. Uptrend is volume-confirmed."
    elif not price_rising and not obv_rising:
        return "Confirmed", "Price and OBV both falling. Downtrend is volume-confirmed."
    elif price_rising and not obv_rising:
        return "Divergence", "Price is rising but OBV is falling. Weak trend — likely to reverse downward."
    else:
        return "Divergence", "Price is falling but OBV is rising. Accumulation detected — possible reversal upward."


# ════════════════════════════════════════════════════════════════
#  Composite Signal
# ════════════════════════════════════════════════════════════════

def _composite(
    trend: str, sar: str, macd: str, obv: str,
    prediction_direction: str = "Neutral",
) -> tuple[str, float]:
    """
    Combine all indicator signals into a single BUY/SELL/HOLD recommendation
    with a confidence score from 0.0 to 1.0.

    Uses 5 factors: SMA trend, Parabolic SAR, MACD, OBV divergence,
    and the linear-regression prediction direction.
    """
    bullish_count = 0
    bearish_count = 0
    total = 5  # 4 indicators + prediction

    # SMA Trend
    if trend == "Bullish":
        bullish_count += 1
    elif trend == "Bearish":
        bearish_count += 1

    # Parabolic SAR
    if sar == "BUY":
        bullish_count += 1
    elif sar == "SELL":
        bearish_count += 1

    # MACD
    if macd == "Bullish":
        bullish_count += 1
    elif macd == "Bearish":
        bearish_count += 1

    # Prediction direction (linear regression trend)
    if prediction_direction == "Bullish":
        bullish_count += 1
    elif prediction_direction == "Bearish":
        bearish_count += 1

    # OBV - divergence is a warning
    if obv == "Confirmed":
        # Reinforces the existing trend direction
        pass
    elif obv == "Divergence":
        # Penalize the dominant signal slightly
        bearish_count += 0.5
        bullish_count -= 0.5

    bullish_count = max(0, bullish_count)
    bearish_count = max(0, bearish_count)

    if bullish_count >= 3:
        signal = "BUY"
        confidence = round(bullish_count / total, 2)
    elif bearish_count >= 3:
        signal = "SELL"
        confidence = round(bearish_count / total, 2)
    else:
        signal = "HOLD"
        confidence = round(max(bullish_count, bearish_count) / total, 2)

    return signal, confidence


# ════════════════════════════════════════════════════════════════
#  Chart Overlay Data (raw series for frontend rendering)
# ════════════════════════════════════════════════════════════════

def calculate_overlays(hist: pd.DataFrame, is_intraday: bool = False) -> ChartOverlays:
    """
    Calculate raw indicator series for chart overlays + price prediction.

    Returns SMA-50, SMA-200 lines, SAR dots, MACD lines, and a 30-day
    linear regression prediction.
    """
    close = hist["Close"]
    high = hist["High"]
    low = hist["Low"]

    def _fmt_date(idx):
        if is_intraday:
            if hasattr(idx, 'timestamp'):
                return str(int(idx.timestamp()))
            return str(idx)
        return str(idx.date()) if hasattr(idx, "date") else str(idx)

    dates = [_fmt_date(idx) for idx in hist.index]

    # ── SMA-50 ──────────────────────────────────────────────────
    sma_50_series = close.rolling(window=50).mean()
    sma_50 = [
        OverlayPoint(date=d, value=round(float(v), 2) if pd.notna(v) else None)
        for d, v in zip(dates, sma_50_series)
        if pd.notna(v)
    ]

    # ── SMA-200 ─────────────────────────────────────────────────
    sma_200_series = close.rolling(window=200).mean()
    sma_200 = [
        OverlayPoint(date=d, value=round(float(v), 2) if pd.notna(v) else None)
        for d, v in zip(dates, sma_200_series)
        if pd.notna(v)
    ]

    # ── Parabolic SAR dots ──────────────────────────────────────
    sar_values = _compute_sar_series(high, low, close)
    sar = [
        OverlayPoint(date=d, value=round(float(v), 2))
        for d, v in zip(dates, sar_values)
    ]

    # ── MACD lines ──────────────────────────────────────────────
    macd_data = _compute_macd_series(close, dates)


    # ── Price Prediction (ARIMA) ────────────────────────────────
    # Skip prediction for intraday data (doesn't make sense on 5-min candles)
    if is_intraday:
        prediction, direction, target = [], "Neutral", None
    else:
        # Use ARIMA for prediction; fallback to linear regression if ARIMA fails
        prediction, direction, target = _compute_arima_prediction(close, dates)
        if not prediction:
            prediction, direction, target = _compute_prediction(close, dates)

    return ChartOverlays(
        sma_50=sma_50,
        sma_200=sma_200,
        sar=sar,
        macd=macd_data,
        prediction=prediction,
        prediction_direction=direction,
        prediction_target=target,
    )


def _compute_sar_series(
    high: pd.Series, low: pd.Series, close: pd.Series,
    af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.20,
) -> np.ndarray:
    """Return the full SAR series as a numpy array."""
    length = len(close)
    if length < 5:
        return np.full(length, np.nan)

    sar = np.zeros(length)
    af = af_start
    is_uptrend = True
    extreme_point = float(high.iloc[0])
    sar[0] = float(low.iloc[0])

    for i in range(1, length):
        prev_sar = sar[i - 1]
        if is_uptrend:
            sar[i] = prev_sar + af * (extreme_point - prev_sar)
            sar[i] = min(sar[i], float(low.iloc[max(0, i - 1)]), float(low.iloc[max(0, i - 2)]))
            if float(low.iloc[i]) < sar[i]:
                is_uptrend = False
                sar[i] = extreme_point
                extreme_point = float(low.iloc[i])
                af = af_start
            else:
                if float(high.iloc[i]) > extreme_point:
                    extreme_point = float(high.iloc[i])
                    af = min(af + af_increment, af_max)
        else:
            sar[i] = prev_sar + af * (extreme_point - prev_sar)
            sar[i] = max(sar[i], float(high.iloc[max(0, i - 1)]), float(high.iloc[max(0, i - 2)]))
            if float(high.iloc[i]) > sar[i]:
                is_uptrend = True
                sar[i] = extreme_point
                extreme_point = float(high.iloc[i])
                af = af_start
            else:
                if float(low.iloc[i]) < extreme_point:
                    extreme_point = float(low.iloc[i])
                    af = min(af + af_increment, af_max)
    return sar


def _compute_macd_series(
    close: pd.Series, dates: list[str],
    fast: int = 12, slow: int = 26, signal_period: int = 9,
) -> list[MACDPoint]:
    """Return the full MACD series for chart rendering."""
    if len(close) < slow + signal_period:
        return []

    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    result = []
    for i in range(slow - 1, len(close)):
        result.append(MACDPoint(
            date=dates[i],
            macd=round(float(macd_line.iloc[i]), 4),
            signal=round(float(signal_line.iloc[i]), 4),
            histogram=round(float(histogram.iloc[i]), 4),
        ))
    return result


def _compute_prediction(
    close: pd.Series, dates: list[str],
    lookback: int = 60, forecast_days: int = 30,
) -> tuple[list[PredictionPoint], str, float | None]:
    """
    Simple linear regression prediction.
    Uses the last `lookback` days to project `forecast_days` into the future.
    Returns the prediction points, direction, and target price.
    """
    if len(close) < lookback:
        lookback = len(close)
    if lookback < 10:
        return [], "Neutral", None

    # Use last `lookback` prices
    recent = close.iloc[-lookback:].values.astype(float)
    x = np.arange(len(recent))
    # Fit linear regression
    coeffs = np.polyfit(x, recent, deg=1)
    slope, intercept = coeffs[0], coeffs[1]

    # Direction
    if slope > 0.05:
        direction = "Bullish"
    elif slope < -0.05:
        direction = "Bearish"
    else:
        direction = "Neutral"

    # Generate prediction points
    last_date = pd.Timestamp(dates[-1])
    prediction = []

    # Start from last actual data point (anchor)
    anchor_value = float(intercept + slope * (len(recent) - 1))
    prediction.append(PredictionPoint(
        date=dates[-1],
        value=round(anchor_value, 2),
    ))

    for day in range(1, forecast_days + 1):
        future_x = len(recent) - 1 + day
        future_price = float(intercept + slope * future_x)
        future_date = last_date + timedelta(days=day)
        # Skip weekends
        while future_date.weekday() >= 5:
            future_date += timedelta(days=1)
        prediction.append(PredictionPoint(
            date=str(future_date.date()),
            value=round(future_price, 2),
        ))

    target = round(float(intercept + slope * (len(recent) - 1 + forecast_days)), 2)

    return prediction, direction, target
