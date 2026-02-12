# 📈 Vantage

**Clear Sight. Smarter Trades.**

---

## 1. Executive Summary

Vantage is a full-stack web application designed to empower retail traders with institutional-grade analytics. Unlike standard stock viewers, Vantage combines **quantitative technical analysis** (using industry-standard indicators) with **qualitative AI-driven sentiment analysis** to provide actionable "Buy/Sell" signals and market crash warnings.

---

## 2. Tech Stack (Client-Server Architecture)

This project uses a modern, separated **3-Tier Architecture** to ensure scalability, security, and a clean separation of concerns.

| Component   | Technology         | Role                                                        | Hosting   |
| ----------- | ------------------ | ----------------------------------------------------------- | --------- |
| Frontend    | Next.js (React)    | **The Face:** Interactive UI, charts, and user dashboard.   | Vercel    |
| Backend     | Python (FastAPI)   | **The Brain:** Data fetching, math calculations, AI inference. | Render    |
| Database    | Supabase (PostgreSQL) | **The Memory:** User profiles, watchlists, historical logs. | Supabase  |
| Auth        | Supabase Auth      | **The Guard:** Secure logins (Email/Password, Google).      | Supabase  |
| Data Source | yfinance           | Fetches live market data and news headlines.                | N/A       |
| AI Model    | FinBERT / VADER    | NLP for news sentiment analysis.                            | Render    |

---

## 3. Core Features & Algorithms

### A. Technical Analysis (The "Math")

The backend processes live **OHLCV** (Open, High, Low, Close, Volume) data to generate these signals:

| Indicator        | Method                                | Buy / Bullish Signal                  | Sell / Bearish Signal                  |
| ---------------- | ------------------------------------- | ------------------------------------- | -------------------------------------- |
| **SMA**          | Simple Moving Average (50 & 200)      | Price > SMA-50                        | Price < SMA-50                         |
| **Parabolic SAR**| Stop and Reverse dots                 | Dots flip below price (Entry)         | Dots flip above price (Exit)           |
| **MACD**         | Moving Avg Convergence Divergence     | MACD crosses above Signal line        | MACD crosses below Signal line         |
| **OBV**          | On-Balance Volume                     | Volume confirms price trend           | Divergence = weak / reversing trend    |
| **ARIMA Forecast**| AutoRegressive Integrated Moving Average | Forecasted price trend is upward      | Forecasted price trend is downward     |
#### ARIMA-Based Price Prediction

Vantage now uses an ARIMA (AutoRegressive Integrated Moving Average) model for advanced price forecasting. The backend analyzes recent price data and projects future prices, providing:

- **Forecasted price points** for the next 30 days (default)
- **Prediction direction** (Bullish, Bearish, Neutral) based on the ARIMA trend
- **Fallback to linear regression** if ARIMA cannot fit the data

This enables more robust and data-driven market predictions, supplementing traditional technical indicators.

### B. Sentiment Analysis (The "News Engine")

**Goal:** Predict market crashes or surges based on mass psychology.

1. Fetch the top 10 recent news headlines for a specific ticker (e.g., AAPL).
2. Feed headlines into an NLP model (VADER / FinBERT).
3. **Scoring:**
   - Score < -0.5 → **Crash Warning / Panic**
   - Score > +0.5 → **Surge Alert / Hype**

---

## 4. Data Flow Architecture

```
User searches "TSLA" on the Dashboard
        │
        ▼
   [ Next.js Frontend ]  ──── API Request ────►  [ FastAPI Backend ]
                                                        │
                                          ┌─────────────┼──────────────┐
                                          ▼             ▼              ▼
                                    [ Supabase ]  [ yfinance ]  [ NLP Model ]
                                     (Auth/DB)    (OHLCV Data)   (Sentiment)
                                          │             │              │
                                          └─────────────┼──────────────┘
                                                        ▼
                                                 JSON Response
                                                        │
                                                        ▼
                                    [ Frontend renders chart + BUY/SELL badge ]
```

---

## 5. Project Structure

```
Vantage-MarketAnalysis/
├── README.md
├── assets/
│   └── logo/
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   └── app/
│       ├── main.py              ← FastAPI entry point
│       ├── core/
│       │   └── config.py        ← Settings & environment config
│       ├── models/
│       │   └── schemas.py       ← Pydantic request/response models
│       ├── routers/
│       │   └── market.py        ← /api/market/* endpoints
│       └── services/
│           ├── market_data.py   ← yfinance integration
│           ├── indicators.py    ← SMA, SAR, MACD, OBV calculations
│           └── sentiment.py     ← News sentiment scoring (VADER)
└── frontend/                    ← (Phase 2 — Next.js)
```

---

## 6. Getting Started

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn app.main:app --reload --port 8000
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API docs.

### API Endpoints

| Method | Endpoint                         | Description                          |
| ------ | -------------------------------- | ------------------------------------ |
| GET    | `/`                              | API info                             |
| GET    | `/health`                        | Health check                         |
| GET    | `/api/market/analyze/{ticker}`   | Full analysis (indicators + sentiment) |
| GET    | `/api/market/price/{ticker}`     | Quick price lookup                   |
| GET    | `/api/market/sentiment/{ticker}` | Standalone sentiment analysis        |

---

## 7. Development Roadmap

### Phase 1: The Foundation (Backend)
- [x] Set up Python virtual environment
- [x] Build FastAPI "Hello World" endpoint
- [x] Implement yfinance to fetch live stock prices
- [x] Create the `calculate_indicators()` function (SMA, MACD, SAR, OBV)

### Phase 2: The Interface (Frontend)
- [ ] Initialize Next.js project
- [ ] Create a basic dashboard layout
- [ ] Integrate a charting library (e.g., Recharts or Lightweight Charts)
- [ ] Connect Frontend to Backend API to display live data

### Phase 3: The Intelligence (AI & Auth)
- [ ] Connect Supabase for User Login/Sign-up
- [ ] Implement the Sentiment Analysis engine (FinBERT upgrade)
- [ ] Build the "Watchlist" feature (Save favorite stocks to DB)

### Phase 4: Deployment
- [ ] Push Backend to Render
- [ ] Push Frontend to Vercel
- [ ] Perform integration testing