/**
 * Vantage Frontend - API Client
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface OHLCVBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorSignals {
  trend: string;
  trend_detail: string;
  sar_signal: string;
  sar_detail: string;
  macd_signal: string;
  macd_detail: string;
  obv_signal: string;
  obv_detail: string;
  composite_signal: string;
  confidence: number;
}

export interface SentimentResult {
  score: number;
  label: string;
  headline_count: number;
  top_headlines: string[];
}

export interface StockAnalysis {
  ticker: string;
  company_name: string;
  current_price: number;
  price_change: number;
  price_change_pct: number;
  ohlcv: OHLCVBar[];
  indicators: IndicatorSignals;
  overlays: ChartOverlays | null;
  sentiment: SentimentResult | null;
  analyzed_at: string;
}

export interface OverlayPoint {
  date: string;
  value: number | null;
}

export interface MACDPoint {
  date: string;
  macd: number | null;
  signal: number | null;
  histogram: number | null;
}

export interface PredictionPoint {
  date: string;
  value: number;
}

export interface ChartOverlays {
  sma_50: OverlayPoint[];
  sma_200: OverlayPoint[];
  sar: OverlayPoint[];
  macd: MACDPoint[];
  prediction: PredictionPoint[];
  prediction_direction: string;
  prediction_target: number | null;
}

export async function analyzeStock(
  ticker: string,
  period: string = "1y",
  interval: string = "1d"
): Promise<StockAnalysis> {
  const res = await fetch(
    `${API_BASE}/api/market/analyze/${ticker}?period=${period}&interval=${interval}&include_sentiment=true`
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `Failed to analyze ${ticker}`);
  }
  return res.json();
}

export async function getPrice(ticker: string) {
  const res = await fetch(`${API_BASE}/api/market/price/${ticker}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `Failed to fetch price for ${ticker}`);
  }
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// ── Watchlist / Market List ──────────────────────────────────

export interface MarketItem {
  ticker: string;
  name: string;
  price: number | null;
  change: number | null;
  change_pct: number | null;
}

export interface WatchlistData {
  stocks: MarketItem[];
  crypto: MarketItem[];
  tokens: MarketItem[];
}

export async function getWatchlist(): Promise<WatchlistData> {
  const res = await fetch(`${API_BASE}/api/market/watchlist`);
  if (!res.ok) {
    throw new Error("Failed to fetch watchlist");
  }
  return res.json();
}

export async function getWatchlistCategory(
  category: string
): Promise<{ category: string; items: MarketItem[] }> {
  const res = await fetch(`${API_BASE}/api/market/watchlist/category/${category}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${category}`);
  }
  return res.json();
}
