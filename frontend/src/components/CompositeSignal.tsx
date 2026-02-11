"use client";

import { IndicatorSignals } from "@/lib/api";
import { ShieldCheck, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface CompositeSignalProps {
  indicators: IndicatorSignals;
  price: number;
  priceChange: number;
  priceChangePct: number;
  companyName: string;
  ticker: string;
}

export default function CompositeSignal({
  indicators,
  price,
  priceChange,
  priceChangePct,
  companyName,
  ticker,
}: CompositeSignalProps) {
  const signal = indicators.composite_signal;
  const confidence = indicators.confidence;

  let signalColor = "text-gray-400";
  let signalBg = "bg-gray-500/10 border-gray-700";
  let SignalIcon = Minus;

  if (signal === "BUY") {
    signalColor = "text-green-400";
    signalBg = "bg-green-500/10 border-green-500/30";
    SignalIcon = TrendingUp;
  } else if (signal === "SELL") {
    signalColor = "text-red-400";
    signalBg = "bg-red-500/10 border-red-500/30";
    SignalIcon = TrendingDown;
  }

  const isPositive = priceChange >= 0;

  return (
    <div className={`rounded-xl border ${signalBg} p-5`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Left: Price info */}
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white">{ticker}</h1>
            <span className="text-sm text-gray-400">{companyName}</span>
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">
              ${price.toFixed(2)}
            </span>
            <span
              className={`text-sm font-medium ${
                isPositive ? "text-green-400" : "text-red-400"
              }`}
            >
              {isPositive ? "+" : ""}
              {priceChange.toFixed(2)} ({isPositive ? "+" : ""}
              {priceChangePct.toFixed(2)}%)
            </span>
          </div>
        </div>

        {/* Right: Signal badge */}
        <div className="flex flex-col items-center gap-1">
          <div
            className={`flex items-center gap-2 rounded-xl px-5 py-3 ${signalBg}`}
          >
            <SignalIcon size={24} className={signalColor} />
            <span className={`text-2xl font-bold ${signalColor}`}>
              {signal}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <ShieldCheck size={12} />
            Confidence: {(confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}
