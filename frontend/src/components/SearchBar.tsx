"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  onSearch: (ticker: string, period: string, interval: string) => void;
  isLoading: boolean;
  currentTicker?: string;
}

const PERIODS = [
  { value: "5m",  label: "5m",  yfPeriod: "1d",  yfInterval: "5m"  },
  { value: "1d",  label: "1D",  yfPeriod: "5d",  yfInterval: "30m" },
  { value: "1mo", label: "1M",  yfPeriod: "1mo", yfInterval: "1d"  },
  { value: "3mo", label: "3M",  yfPeriod: "3mo", yfInterval: "1d"  },
  { value: "6mo", label: "6M",  yfPeriod: "6mo", yfInterval: "1d"  },
  { value: "1y",  label: "1Y",  yfPeriod: "1y",  yfInterval: "1d"  },
  { value: "2y",  label: "2Y",  yfPeriod: "2y",  yfInterval: "1d"  },
  { value: "5y",  label: "5Y",  yfPeriod: "5y",  yfInterval: "1wk" },
];

export default function SearchBar({ onSearch, isLoading, currentTicker }: SearchBarProps) {
  const [ticker, setTicker] = useState("");
  const [period, setPeriod] = useState("2y");
  const isFirstRender = useRef(true);

  // Sync ticker from parent (e.g., when user clicks from MarketList)
  useEffect(() => {
    if (currentTicker) {
      setTicker(currentTicker);
    }
  }, [currentTicker]);

  const getActiveTicker = () => ticker.trim().toUpperCase() || currentTicker || "";

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const cleaned = getActiveTicker();
    if (cleaned) {
      const p = PERIODS.find((x) => x.value === period) ?? PERIODS[5];
      onSearch(cleaned, p.yfPeriod, p.yfInterval);
    }
  };

  const handlePeriodClick = (value: string) => {
    setPeriod(value);
    const cleaned = getActiveTicker();
    if (cleaned) {
      const p = PERIODS.find((x) => x.value === value)!;
      onSearch(cleaned, p.yfPeriod, p.yfInterval);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="relative flex-1">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
        />
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Enter ticker (e.g. AAPL, TSLA, MSFT)"
          className="w-full rounded-lg border border-gray-700 bg-[#0f1117] py-2.5 pl-10 pr-4 text-sm text-gray-200 placeholder-gray-600 outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          disabled={isLoading}
        />
      </div>

      {/* Period selector */}
      <div className="flex gap-1 rounded-lg border border-gray-700 bg-[#0f1117] p-1">
        {PERIODS.map((p) => (
          <button
            key={p.value}
            type="button"
            onClick={() => handlePeriodClick(p.value)}
            className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition ${
              period === p.value
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <button
        type="submit"
        disabled={isLoading || !getActiveTicker()}
        className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}
