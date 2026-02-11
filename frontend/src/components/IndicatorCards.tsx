"use client";

import { IndicatorSignals } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus, Activity, BarChart3, ArrowUpDown, Volume2 } from "lucide-react";

interface IndicatorCardsProps {
  indicators: IndicatorSignals;
}

function SignalBadge({ signal }: { signal: string }) {
  const normalized = signal.toUpperCase();

  if (["BUY", "BULLISH", "CONFIRMED"].includes(normalized)) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-500/15 px-2.5 py-0.5 text-xs font-semibold text-green-400">
        <TrendingUp size={12} />
        {signal}
      </span>
    );
  }
  if (["SELL", "BEARISH", "DIVERGENCE"].includes(normalized)) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2.5 py-0.5 text-xs font-semibold text-red-400">
        <TrendingDown size={12} />
        {signal}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-500/15 px-2.5 py-0.5 text-xs font-semibold text-gray-400">
      <Minus size={12} />
      {signal}
    </span>
  );
}

const indicatorConfig = [
  { key: "trend" as const, detail: "trend_detail" as const, label: "SMA Trend", icon: Activity },
  { key: "sar_signal" as const, detail: "sar_detail" as const, label: "Parabolic SAR", icon: ArrowUpDown },
  { key: "macd_signal" as const, detail: "macd_detail" as const, label: "MACD", icon: BarChart3 },
  { key: "obv_signal" as const, detail: "obv_detail" as const, label: "OBV Volume", icon: Volume2 },
];

export default function IndicatorCards({ indicators }: IndicatorCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {indicatorConfig.map(({ key, detail, label, icon: Icon }) => (
        <div
          key={key}
          className="rounded-xl border border-gray-800 bg-[#0f1117] p-4"
        >
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
              <Icon size={16} className="text-gray-500" />
              {label}
            </div>
            <SignalBadge signal={indicators[key]} />
          </div>
          <p className="text-xs leading-relaxed text-gray-500">
            {indicators[detail]}
          </p>
        </div>
      ))}
    </div>
  );
}
