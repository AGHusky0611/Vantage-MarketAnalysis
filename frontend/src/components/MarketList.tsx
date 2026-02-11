"use client";

import { useState, useEffect } from "react";
import {
  getWatchlistCategory,
  MarketItem,
} from "@/lib/api";
import {
  TrendingUp,
  TrendingDown,
  Loader2,
  BarChart2,
  Bitcoin,
  Coins,
} from "lucide-react";

interface MarketListProps {
  onSelect: (ticker: string) => void;
}

const CATEGORIES = [
  { key: "stocks", label: "Stocks", icon: BarChart2 },
  { key: "crypto", label: "Crypto", icon: Bitcoin },
  { key: "tokens", label: "Tokens", icon: Coins },
];

export default function MarketList({ onSelect }: MarketListProps) {
  const [activeTab, setActiveTab] = useState("stocks");
  const [items, setItems] = useState<MarketItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getWatchlistCategory(activeTab)
      .then((data) => {
        if (!cancelled) setItems(data.items);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeTab]);

  return (
    <div className="rounded-xl border border-gray-800 bg-[#0f1117]">
      {/* Category tabs */}
      <div className="flex border-b border-gray-800">
        {CATEGORIES.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex flex-1 items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition ${
              activeTab === key
                ? "border-b-2 border-blue-500 text-blue-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            <Icon size={13} />
            {label}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="max-h-[520px] overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-10">
            <Loader2 size={20} className="animate-spin text-gray-500" />
          </div>
        )}

        {error && (
          <p className="p-4 text-xs text-red-400">{error}</p>
        )}

        {!isLoading && !error && items.length > 0 && (
          <ul>
            {items.map((item) => (
              <li key={item.ticker}>
                <button
                  onClick={() => onSelect(item.ticker)}
                  className="flex w-full items-center justify-between px-4 py-2.5 text-left transition hover:bg-gray-800/50"
                >
                  {/* Left: Ticker + Name */}
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">
                      {item.ticker.replace("-USD", "")}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {item.name}
                    </p>
                  </div>

                  {/* Right: Price + Change % */}
                  <div className="flex flex-col items-end ml-2 shrink-0">
                    {item.price !== null ? (
                      <>
                        <span className="text-sm font-medium text-gray-200">
                          ${item.price.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </span>
                        <span
                          className={`flex items-center gap-0.5 text-xs font-medium ${
                            (item.change_pct ?? 0) >= 0
                              ? "text-green-400"
                              : "text-red-400"
                          }`}
                        >
                          {(item.change_pct ?? 0) >= 0 ? (
                            <TrendingUp size={11} />
                          ) : (
                            <TrendingDown size={11} />
                          )}
                          {(item.change_pct ?? 0) >= 0 ? "+" : ""}
                          {item.change_pct?.toFixed(2)}%
                        </span>
                      </>
                    ) : (
                      <span className="text-xs text-gray-600">N/A</span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
