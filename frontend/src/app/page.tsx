"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { analyzeStock, StockAnalysis } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import SearchBar from "@/components/SearchBar";
import StockChart from "@/components/StockChart";
import CompositeSignal from "@/components/CompositeSignal";
import IndicatorCards from "@/components/IndicatorCards";
import SentimentPanel from "@/components/SentimentPanel";
import MarketList from "@/components/MarketList";
import { Activity, Radio, RefreshCw, LogOut, User } from "lucide-react";

const REFRESH_INTERVAL_MS = 60_000; // 60 seconds

export default function Home() {
  const { user, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTicker, setCurrentTicker] = useState("");
  const [activePeriod, setActivePeriod] = useState("2y");
  const [activeInterval, setActiveInterval] = useState("1d");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const latestParamsRef = useRef({ ticker: "", period: "2y", interval: "1d" });

  // Silent refresh (no loading spinner, updates data in-place)
  const silentRefresh = useCallback(async () => {
    const { ticker, period, interval } = latestParamsRef.current;
    if (!ticker) return;
    try {
      setIsRefreshing(true);
      const data = await analyzeStock(ticker, period, interval);
      setAnalysis(data);
      setLastRefreshed(new Date());
    } catch {
      // Silent fail on auto-refresh — don't overwrite existing data
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Start/stop auto-refresh timer
  useEffect(() => {
    if (refreshTimer.current) {
      clearInterval(refreshTimer.current);
      refreshTimer.current = null;
    }
    if (autoRefresh && currentTicker) {
      refreshTimer.current = setInterval(silentRefresh, REFRESH_INTERVAL_MS);
    }
    return () => {
      if (refreshTimer.current) clearInterval(refreshTimer.current);
    };
  }, [autoRefresh, currentTicker, silentRefresh]);

  const handleSearch = async (ticker: string, period: string, interval: string = "1d") => {
    setIsLoading(true);
    setError(null);
    setCurrentTicker(ticker);
    setActivePeriod(period);
    setActiveInterval(interval);
    latestParamsRef.current = { ticker, period, interval };
    try {
      const data = await analyzeStock(ticker, period, interval);
      setAnalysis(data);
      setLastRefreshed(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setAnalysis(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarketSelect = (ticker: string) => {
    handleSearch(ticker, activePeriod, activeInterval);
  };

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  // Show loading while checking auth
  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-blue-500" />
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0a0b0f]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Activity size={24} className="text-blue-500" />
            <span className="text-lg font-bold text-white">Vantage</span>
            <span className="hidden sm:inline text-xs text-gray-500 ml-1">
              Clear Sight. Smarter Trades.
            </span>
          </div>
          <div className="flex items-center gap-3">
            {currentTicker && (
              <div className="flex items-center gap-2">
                {/* Manual Refresh */}
                <button
                  onClick={silentRefresh}
                  disabled={isRefreshing}
                  className="rounded-md p-1.5 text-gray-400 transition hover:bg-gray-800 hover:text-gray-200 disabled:opacity-40"
                  title="Refresh now"
                >
                  <RefreshCw size={14} className={isRefreshing ? "animate-spin" : ""} />
                </button>

                {/* Auto-Refresh toggle */}
                <button
                  onClick={() => setAutoRefresh((v) => !v)}
                  className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide transition ${
                    autoRefresh
                      ? "bg-green-500/10 text-green-400 border border-green-500/30"
                      : "bg-gray-800 text-gray-500 border border-gray-700"
                  }`}
                  title={autoRefresh ? "Auto-refresh ON (60s) — click to pause" : "Auto-refresh OFF — click to enable"}
                >
                  <Radio size={10} className={autoRefresh ? "animate-pulse" : ""} />
                  {autoRefresh ? "LIVE" : "PAUSED"}
                </button>
              </div>
            )}
            <div className="text-xs text-gray-600">v0.1.0</div>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu((v) => !v)}
                className="flex items-center gap-2 rounded-lg border border-gray-700 bg-[#0f1117] px-3 py-1.5 text-sm text-gray-300 transition hover:border-gray-600 hover:bg-gray-800"
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-[11px] font-bold text-white">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:inline text-xs">{user.username}</span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-gray-800 bg-[#0f1117] p-2 shadow-2xl z-50">
                  <div className="border-b border-gray-800 px-3 py-2 mb-1">
                    <p className="text-sm font-medium text-gray-200">{user.username}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <button
                    onClick={() => { logout(); router.push("/login"); }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-400 transition hover:bg-red-500/10"
                  >
                    <LogOut size={14} />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout: Content + Sidebar */}
      <div className="mx-auto flex max-w-[1440px] gap-4 px-4 py-6">
        {/* Left: Main Content */}
        <main className="min-w-0 flex-1">
          {/* Search */}
          <div className="mb-6">
            <SearchBar onSearch={handleSearch} isLoading={isLoading} currentTicker={currentTicker} />
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="flex items-center justify-center py-20">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-blue-500" />
                <p className="text-sm text-gray-500">
                  Fetching data and running analysis...
                </p>
              </div>
            </div>
          )}

          {/* Results */}
          {analysis && !isLoading && (
            <div className="space-y-4">
              {/* Composite Signal + Price */}
              <CompositeSignal
                indicators={analysis.indicators}
                price={analysis.current_price}
                priceChange={analysis.price_change}
                priceChangePct={analysis.price_change_pct}
                companyName={analysis.company_name}
                ticker={analysis.ticker}
              />

              {/* Chart */}
              <StockChart data={analysis.ohlcv} ticker={analysis.ticker} overlays={analysis.overlays} />

              {/* Indicators + Sentiment */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <IndicatorCards indicators={analysis.indicators} />
                </div>
                <div>
                  <SentimentPanel sentiment={analysis.sentiment} />
                </div>
              </div>

              {/* Footer timestamp */}
              <p className="text-center text-xs text-gray-600">
                Analyzed at {new Date(analysis.analyzed_at).toLocaleString()}
                {lastRefreshed && (
                  <span className="ml-2 text-gray-700">
                    · Last refresh {lastRefreshed.toLocaleTimeString()}
                    {autoRefresh && " · Next in ~60s"}
                  </span>
                )}
              </p>
            </div>
          )}

          {/* Empty state */}
          {!analysis && !isLoading && !error && (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <Activity size={48} className="mb-4 text-gray-700" />
              <h2 className="text-xl font-semibold text-gray-400">
                Search for a stock to begin
              </h2>
              <p className="mt-2 max-w-md text-sm text-gray-600">
                Enter a ticker symbol above or pick one from the market list to
                get a full technical analysis with SMA, MACD, Parabolic SAR, OBV
                indicators, and AI-powered news sentiment scoring.
              </p>
            </div>
          )}
        </main>

        {/* Right Sidebar: Market List */}
        <aside className="hidden w-72 shrink-0 lg:block">
          <div className="sticky top-16">
            <h3 className="mb-3 text-sm font-medium text-gray-400">Markets</h3>
            <MarketList onSelect={handleMarketSelect} />
          </div>
        </aside>
      </div>
    </div>
  );
}
