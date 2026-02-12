"""
Vantage Backend - Technical Indicators Service
Calculates SMA, MACD, RSI, OBV, Bollinger Bands, and ARIMA Predictions.
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
# Import ARIMA for forecasting
from statsmodels.tsa.arima.model import ARIMA
import warnings
from app.models.schemas import Indicators, ChartOverlays, OverlayPoint, MACDPoint, PredictionPoint

# Suppress statsmodels warnings (they can clutter logs)
warnings.filterwarnings("ignore")

def calculate_indicators(
    hist: pd.DataFrame,
    prediction_direction: str = "Neutral"
) -> Indicators:
    """
    Calculate technical indicators and generate signals.
    """
    df = hist.copy()

    # 1. Calculate Indicators using pandas_ta
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)

    macd = ta.macd(df['Close'])
    # pandas_ta column names: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_SIGNAL'] = macd['MACDs_12_26_9']

    # Bollinger Bands (20, 2.0)
    bb = ta.bbands(df['Close'], length=20)
    df['BB_UPPER'] = bb['BBU_20_2.0']
    df['BB_LOWER'] = bb['BBL_20_2.0']

    # OBV
    df['OBV'] = ta.obv(df['Close'], df['Volume'])
    
    # Parabolic SAR
    psar = ta.psar(df['High'], df['Low'], df['Close'])
    df['PSAR'] = psar.iloc[:, 0].combine_first(psar.iloc[:, 1])

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
    price_up = latest['Close'] > prev['Close']
    obv_up = latest['OBV'] > prev['OBV']
    
    if price_up and not obv_up:
        obv_signal = "BEARISH DIVERGENCE"
        obv_detail = "Price rising but volume falling (Weakness)"
    elif not price_up and obv_up:
        obv_signal = "BULLISH DIVERGENCE"
        obv_detail = "Price falling but volume rising (Strength)"

    # Parabolic SAR Signal
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

    # Adjust based on prediction direction (Arima Forecast)
    if prediction_direction == "Bullish" and comp_signal in ["BUY", "NEUTRAL"]:
        comp_signal = "STRONG BUY"
    elif prediction_direction == "Bearish" and comp_signal in ["SELL", "NEUTRAL"]:
        comp_signal = "STRONG SELL"

    # Calculate Confidence
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
    Generate chart overlay data and run ARIMA prediction.
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
        if not pd.isna(row['SMA_50']):
            sma_50.append(OverlayPoint(date=str(d_str), value=row['SMA_50']))
        if not pd.isna(row['SMA_200']):
            sma_200.append(OverlayPoint(date=str(d_str), value=row['SMA_200']))
        if not pd.isna(row['PSAR']):
            sar.append(OverlayPoint(date=str(d_str), value=row['PSAR']))
        if not pd.isna(row['MACD']):
            macd_data.append(MACDPoint(
                date=str(d_str),
                macd=row['MACD'],
                signal=row['MACD_SIGNAL'],
                histogram=row['MACD_HIST']
            ))

    # ---------------------------------------------------------
    # ARIMA PREDICTION LOGIC (Replacing simple regression)
    # ---------------------------------------------------------
    prediction = []
    direction = "Neutral"
    last_val = df['Close'].iloc[-1]
    
    try:
        # 1. Prepare Data: ARIMA works best on a 1D series
        # Using last 60 points keeps it fast for the API
        train_data = df['Close'].tail(60).values
        
        # 2. Define Model: ARIMA(5,1,0) is a solid general-purpose config for stocks
        # p=5 (lag), d=1 (differencing), q=0 (moving average)
        model = ARIMA(train_data, order=(5, 1, 0))
        model_fit = model.fit()
        
        # 3. Forecast next 5 steps
        forecast = model_fit.forecast(steps=5)
        
        # 4. Generate Future Dates
        dates_future = []
        last_date = df.index[-1]
        for i in range(1, 6):
            if is_intraday:
                # Add 1 hour per step for intraday fallback (simplification)
                next_date = last_date + timedelta(hours=i)
                dates_future.append(int(next_date.timestamp()))
            else:
                next_date = last_date + timedelta(days=i)
                dates_future.append(next_date.strftime('%Y-%m-%d'))
        
        # 5. Build Prediction Points
        for i, val in enumerate(forecast):
            prediction.append(PredictionPoint(date=str(dates_future[i]), value=val))
            
        # 6. Determine Direction based on Forecast
        predicted_price = forecast[-1]
        current_price = train_data[-1]
        
        if predicted_price > current_price * 1.005: # > 0.5% gain
            direction = "Bullish"
        elif predicted_price < current_price * 0.995: # > 0.5% loss
            direction = "Bearish"
        else:
            direction = "Neutral"

        last_val = predicted_price

    except Exception as e:
        print(f"ARIMA Failed: {e}")
        # Fallback to simple flat prediction if ARIMA crashes (rare but possible)
        direction = "Neutral"
        # Return empty prediction or just a flat line
        
    return ChartOverlays(
        sma_50=sma_50,
        sma_200=sma_200,
        sar=sar,
        macd=macd_data,
        prediction=prediction,
        prediction_direction=direction,
        prediction_target=round(last_val, 2)
    )