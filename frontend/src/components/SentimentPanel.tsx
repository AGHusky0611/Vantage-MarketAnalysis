"use client";

import { SentimentResult } from "@/lib/api";
import { Newspaper, AlertTriangle, Flame, Meh } from "lucide-react";

interface SentimentPanelProps {
  sentiment: SentimentResult | null;
}

function getSentimentStyle(label: string) {
  switch (label) {
    case "Panic":
      return { color: "text-red-400", bg: "bg-red-500/15", icon: AlertTriangle };
    case "Bearish":
      return { color: "text-orange-400", bg: "bg-orange-500/15", icon: AlertTriangle };
    case "Hype":
      return { color: "text-green-400", bg: "bg-green-500/15", icon: Flame };
    case "Bullish":
      return { color: "text-emerald-400", bg: "bg-emerald-500/15", icon: Flame };
    default:
      return { color: "text-gray-400", bg: "bg-gray-500/15", icon: Meh };
  }
}

export default function SentimentPanel({ sentiment }: SentimentPanelProps) {
  if (!sentiment || sentiment.headline_count === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#0f1117] p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Newspaper size={16} className="text-gray-500" />
          News Sentiment
        </div>
        <p className="mt-2 text-xs text-gray-500">No news data available.</p>
      </div>
    );
  }

  const style = getSentimentStyle(sentiment.label);
  const Icon = style.icon;
  const pct = ((sentiment.score + 1) / 2) * 100; // normalize -1..1 to 0..100

  return (
    <div className="rounded-xl border border-gray-800 bg-[#0f1117] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Newspaper size={16} className="text-gray-500" />
          News Sentiment
        </div>
        <span
          className={`inline-flex items-center gap-1 rounded-full ${style.bg} px-2.5 py-0.5 text-xs font-semibold ${style.color}`}
        >
          <Icon size={12} />
          {sentiment.label}
        </span>
      </div>

      {/* Score bar */}
      <div className="mb-3">
        <div className="mb-1 flex justify-between text-xs text-gray-500">
          <span>Panic</span>
          <span>Score: {sentiment.score.toFixed(2)}</span>
          <span>Hype</span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-800">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-red-500 via-gray-500 to-green-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Headlines */}
      <div>
        <p className="mb-1.5 text-xs font-medium text-gray-400">
          Top Headlines ({sentiment.headline_count} analyzed)
        </p>
        <ul className="space-y-1">
          {sentiment.top_headlines.map((headline, i) => (
            <li key={i} className="text-xs leading-relaxed text-gray-500">
              • {headline}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
