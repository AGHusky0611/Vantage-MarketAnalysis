"""
Vantage Backend - Technical Indicators Service
Calculates SMA, MACD, RSI, OBV, and Bollinger Bands using pandas-ta.
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
from app.models.schemas import Indicators, ChartOverlays, OverlayPoint, MACDPoint, PredictionPoint

def calculate_indicators(
    hist: pd.DataFrame,
    prediction_direction: str = "Neutral"
) -> Indicators:
    """
    Calculate technical indicators and generate signals.
    """
    # Create a copy to avoid SettingWithCopy warnings
    df = hist.copy()

    # 1. Calculate Indicators using pandas_ta
    # SMA
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)

    # RSI
    df['RSI'] = ta.rsi(df['Close'], length=14)

    # MACD
    macd = ta.macd(df['Close'])
    # pandas_ta column names: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_SIGNAL'] = macd['MACDs_12_26_9']

    # Bollinger Bands
    bb = ta.bbands(df['Close'], length=20)
    df['BB_UPPER'] = bb['BBU_20_2.0']
    df['BB_LOWER'] = bb['BBL_20_2.0']

    # OBV
    df['OBV'] = ta.obv(df['Close'], df['Volume'])
    
    # Parabolic SAR
    psar = ta.psar(df['High'], df['Low'], df['Close'])
    # PSAR returns columns like 'PSARl_0.02_0.2' and 'PSARs_0.02_0.2'
    # We combine them into one 'PSAR' column
    psar_combined = psar.iloc[:, 0].combine_first(psar.iloc[:, 1])
    df['PSAR'] = psar_combined

    # 2. Get Latest Values
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # 3. Generate Signals
    # Trend (SMA Cross)
    trend = "BULLISH" if latest['Close'] > latest['SMA_50'] else "BEARISH"
    trend_detail = "Price above 50-day SMA" if trend == "BULLISH" else "Price below 50-day SMA"

    # MACD Signal
    macd_val = latest['MACD']
    macd_sig = latest['MACD_SIGNAL']
    if macd_val > macd_sig:
        macd_signal = "BUY"
        macd_detail = "MACD crossed above Signal line"
    else:
        macd_signal = "SELL"
        macd_detail = "MACD crossed below Signal line"

    # OBV Signal (Divergence Check)
    obv_signal = "NEUTRAL"
    obv_detail = "Volume confirms trend"
    # Simple check: Is OBV trending with price?
    price_up = latest['Close'] > prev['Close']
    obv_up = latest['OBV'] > prev['OBV']
    
    if price_up and not obv_up:
        obv_signal = "BEARISH DIVERGENCE"
        obv_detail = "Price rising but volume falling (Weakness)"
    elif not price_up and obv_up:
        obv_signal = "BULLISH DIVERGENCE"
        obv_detail = "Price falling but volume rising (Strength)"

    # Parabolic SAR Signal
    # If price is above SAR, it's an uptrend (dots below)
    sar_val = latest['PSAR']
    if latest['Close'] > sar_val:
        sar_signal = "BUY"
        sar_detail = "Price above SAR dots"
    else:
        sar_signal = "SELL"
        sar_detail = "Price below SAR dots"

    # Composite Signal Logic
    signals = [trend == "BULLISH", macd_signal == "BUY", sar_signal == "BUY"]
    score = sum(signals)
    
    if score == 3:
        comp_signal = "STRONG BUY"
    elif score == 2:
        comp_signal = "BUY"
    elif score == 0:
        comp_signal = "STRONG SELL"
    elif score == 1:
        comp_signal = "SELL"
    else:
        comp_signal = "NEUTRAL"

    # Adjust based on prediction direction (if provided)
    if prediction_direction == "Bullish" and comp_signal in ["BUY", "NEUTRAL"]:
        comp_signal = "STRONG BUY"
    elif prediction_direction == "Bearish" and comp_signal in ["SELL", "NEUTRAL"]:
        comp_signal = "STRONG SELL"

    # Calculate Confidence (Simple heuristic)
    confidence = (score / 3) * 100
    if prediction_direction != "Neutral":
        confidence = min(confidence + 10, 95)

    return Indicators(
        trend=trend,
        trend_detail=trend_detail,
        sar_signal=sar_signal,
        sar_detail=sar_detail,
        macd_signal=macd_signal,
        macd_detail=macd_detail,
        obv_signal=obv_signal,
        obv_detail=obv_detail,
        composite_signal=comp_signal,
        confidence=round(confidence, 1)
    )

def calculate_overlays(
    hist: pd.DataFrame,
    is_intraday: bool = False
) -> ChartOverlays:
    """
    Generate chart overlay data for the frontend.
    """
    df = hist.copy()
    
    # Calculate indicators needed for overlays
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    
    macd = ta.macd(df['Close'])
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_SIGNAL'] = macd['MACDs_12_26_9']
    df['MACD_HIST'] = macd['MACDh_12_26_9']
    
    psar = ta.psar(df['High'], df['Low'], df['Close'])
    df['PSAR'] = psar.iloc[:, 0].combine_first(psar.iloc[:, 1])

    # Helper to format dates
    def format_date(idx):
        if is_intraday:
            # Return Unix timestamp for intraday
            return int(idx.timestamp())
        else:
            return idx.strftime('%Y-%m-%d')

    # Build response objects
    sma_50 = []
    sma_200 = []
    sar = []
    macd_data = []

    for idx, row in df.iterrows():
        d_str = format_date(idx)
        
        # SMA 50
        if not pd.isna(row['SMA_50']):
            sma_50.append(OverlayPoint(date=str(d_str), value=row['SMA_50']))
            
        # SMA 200
        if not pd.isna(row['SMA_200']):
            sma_200.append(OverlayPoint(date=str(d_str), value=row['SMA_200']))
            
        # SAR
        if not pd.isna(row['PSAR']):
            sar.append(OverlayPoint(date=str(d_str), value=row['PSAR']))
            
        # MACD
        if not pd.isna(row['MACD']):
            macd_data.append(MACDPoint(
                date=str(d_str),
                macd=row['MACD'],
                signal=row['MACD_SIGNAL'],
                histogram=row['MACD_HIST']
            ))

    # Simple Linear Regression Prediction (5 days)
    # Get last 30 days for trend line
    recent = df.tail(30)
    dates_future = []
    last_date = df.index[-1]
    
    for i in range(1, 6):
        if is_intraday:
             # Add minutes/hours? Simplification: just add huge number for now
             # Intraday prediction is complex, skipping for MVP
             next_date = last_date # Placeholder
        else:
            next_date = last_date + timedelta(days=i)
            # Skip weekends logic omitted for brevity
            dates_future.append(next_date.strftime('%Y-%m-%d'))

    # Determine simple direction
    p1 = recent['Close'].iloc[0]
    p2 = recent['Close'].iloc[-1]
    direction = "Bullish" if p2 > p1 else "Bearish"
    
    # Generate dummy prediction points based on direction
    prediction = []
    last_val = p2
    step = (p2 - p1) / 30  # Average daily move
    
    for d in dates_future:
        last_val += step
        prediction.append(PredictionPoint(date=d, value=last_val))

    return ChartOverlays(
        sma_50=sma_50,
        sma_200=sma_200,
        sar=sar,
        macd=macd_data,
        prediction=prediction,
        prediction_direction=direction,
        prediction_target=round(last_val, 2)
    )