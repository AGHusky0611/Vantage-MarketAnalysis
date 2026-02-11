"use client";

import { useRef, useEffect, useState } from "react";
import {
  createChart,
  IChartApi,
  CandlestickData,
  Time,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  LineStyle,
} from "lightweight-charts";
import { OHLCVBar, ChartOverlays } from "@/lib/api";
import { TrendingUp } from "lucide-react";

/** Convert date strings: Unix timestamp strings → number, date strings → pass through */
function toTime(dateStr: string): Time {
  if (/^\d+$/.test(dateStr)) {
    return Number(dateStr) as unknown as Time;
  }
  return dateStr as Time;
}

interface StockChartProps {
  data: OHLCVBar[];
  ticker: string;
  overlays?: ChartOverlays | null;
}

type OverlayKey = "sma50" | "sma200" | "sar" | "prediction" | "macd";

const OVERLAY_LABELS: Record<OverlayKey, { label: string; color: string }> = {
  sma50: { label: "SMA 50", color: "#3b82f6" },
  sma200: { label: "SMA 200", color: "#f97316" },
  sar: { label: "SAR", color: "#a855f7" },
  prediction: { label: "Prediction", color: "#06b6d4" },
  macd: { label: "MACD", color: "#10b981" },
};

export default function StockChart({ data, ticker, overlays }: StockChartProps) {
  const priceContainerRef = useRef<HTMLDivElement>(null);
  const macdContainerRef = useRef<HTMLDivElement>(null);
  const priceChartRef = useRef<IChartApi | null>(null);
  const macdChartRef = useRef<IChartApi | null>(null);

  const [active, setActive] = useState<Record<OverlayKey, boolean>>({
    sma50: true,
    sma200: true,
    sar: true,
    prediction: true,
    macd: true,
  });

  const toggle = (key: OverlayKey) =>
    setActive((prev) => ({ ...prev, [key]: !prev[key] }));

  useEffect(() => {
    if (!priceContainerRef.current || data.length === 0) return;

    /* ── tear down previous charts ── */
    if (priceChartRef.current) {
      priceChartRef.current.remove();
      priceChartRef.current = null;
    }
    if (macdChartRef.current) {
      macdChartRef.current.remove();
      macdChartRef.current = null;
    }

    /* Detect intraday data (dates are Unix timestamps = all digits) */
    const isIntraday = /^\d+$/.test(data[0]?.date ?? "");

    /* ============================================================
       PRICE CHART
       ============================================================ */
    const chart = createChart(priceContainerRef.current, {
      layout: { background: { color: "#0f1117" }, textColor: "#9ca3af" },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#374151" },
      timeScale: { borderColor: "#374151", timeVisible: isIntraday },
      width: priceContainerRef.current.clientWidth,
      height: 420,
    });

    /* Candlesticks */
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderDownColor: "#ef4444",
      borderUpColor: "#22c55e",
      wickDownColor: "#ef4444",
      wickUpColor: "#22c55e",
    });

    const candleData: CandlestickData<Time>[] = data.map((b) => ({
      time: toTime(b.date),
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    candleSeries.setData(candleData);

    /* Volume */
    const volSeries = chart.addSeries(HistogramSeries, {
      color: "#4b5563",
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    volSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });
    volSeries.setData(
      data.map((b) => ({
        time: toTime(b.date),
        value: b.volume,
        color: b.close >= b.open ? "#22c55e40" : "#ef444440",
      }))
    );

    /* ── Overlays ── */
    if (overlays) {
      /* SMA 50 */
      if (active.sma50 && overlays.sma_50?.length) {
        const sma50 = chart.addSeries(LineSeries, {
          color: "#3b82f6",
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        sma50.setData(
          overlays.sma_50
            .filter((p) => p.value !== null)
            .map((p) => ({ time: toTime(p.date), value: p.value as number }))
        );
      }

      /* SMA 200 */
      if (active.sma200 && overlays.sma_200?.length) {
        const sma200 = chart.addSeries(LineSeries, {
          color: "#f97316",
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        sma200.setData(
          overlays.sma_200
            .filter((p) => p.value !== null)
            .map((p) => ({ time: toTime(p.date), value: p.value as number }))
        );
      }

      /* Parabolic SAR — rendered as a line series */
      if (active.sar && overlays.sar?.length) {
        const sarFiltered = overlays.sar.filter((p) => p.value !== null);
        if (sarFiltered.length > 0) {
          const sarSeries = chart.addSeries(LineSeries, {
            color: "#a855f7",
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
          });
          sarSeries.setData(
            sarFiltered.map((p) => ({
              time: toTime(p.date),
              value: p.value as number,
            }))
          );
        }
      }

      /* Prediction line */
      if (active.prediction && overlays.prediction?.length) {
        const predSeries = chart.addSeries(LineSeries, {
          color: "#06b6d4",
          lineWidth: 2,
          lineStyle: LineStyle.Dashed,
          priceLineVisible: false,
          lastValueVisible: true,
        });

        // connect to last real price so line is continuous
        const lastBar = data[data.length - 1];
        let predData = [
          { time: toTime(lastBar.date), value: lastBar.close },
          ...overlays.prediction
            .filter((p) => p.date !== lastBar.date)
            .map((p) => ({
              time: toTime(p.date),
              value: p.value as number,
            })),
        ];
        // Sort and remove duplicates to be safe
        predData.sort((a, b) => (a.time as number) - (b.time as number));
        predData = predData.filter(
          (p, i) => i === 0 || p.time !== predData[i - 1].time
        );
        predSeries.setData(predData);
      }
    }

    chart.timeScale().fitContent();

    /* Show last ~120 bars in view, allow scrolling left for history */
    const totalBars = candleData.length;
    const visibleBars = Math.min(120, totalBars);
    if (totalBars > visibleBars) {
      chart.timeScale().setVisibleLogicalRange({
        from: totalBars - visibleBars,
        to: totalBars,
      });
    }

    priceChartRef.current = chart;

    /* ============================================================
       MACD CHART (separate below)
       ============================================================ */
    if (
      active.macd &&
      overlays?.macd?.length &&
      macdContainerRef.current
    ) {
      const macdChart = createChart(macdContainerRef.current, {
        layout: { background: { color: "#0f1117" }, textColor: "#9ca3af" },
        grid: {
          vertLines: { color: "#1f2937" },
          horzLines: { color: "#1f293780" },
        },
        crosshair: { mode: 0 },
        rightPriceScale: { borderColor: "#374151" },
        timeScale: { borderColor: "#374151", timeVisible: isIntraday },
        width: macdContainerRef.current.clientWidth,
        height: 150,
      });

      /* MACD line */
      const macdLine = macdChart.addSeries(LineSeries, {
        color: "#3b82f6",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      macdLine.setData(
        overlays.macd
          .filter((p) => p.macd !== null)
          .map((p) => ({ time: toTime(p.date), value: p.macd as number }))
      );

      /* Signal line */
      const sigLine = macdChart.addSeries(LineSeries, {
        color: "#f97316",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      sigLine.setData(
        overlays.macd
          .filter((p) => p.signal !== null)
          .map((p) => ({ time: toTime(p.date), value: p.signal as number }))
      );

      /* Histogram */
      const histSeries = macdChart.addSeries(HistogramSeries, {
        priceFormat: { type: "price" },
        priceLineVisible: false,
        lastValueVisible: false,
      });
      histSeries.setData(
        overlays.macd
          .filter((p) => p.histogram !== null)
          .map((p) => ({
            time: toTime(p.date),
            value: p.histogram as number,
            color:
              (p.histogram as number) >= 0
                ? "#22c55e80"
                : "#ef444480",
          }))
      );

      macdChart.timeScale().fitContent();

      /* Match MACD visible range to price chart */
      const macdTotal = overlays.macd.filter((p) => p.macd !== null).length;
      const macdVisible = Math.min(120, macdTotal);
      if (macdTotal > macdVisible) {
        macdChart.timeScale().setVisibleLogicalRange({
          from: macdTotal - macdVisible,
          to: macdTotal,
        });
      }

      macdChartRef.current = macdChart;
    }

    /* ── Responsive resize ── */
    const handleResize = () => {
      const w = priceContainerRef.current?.clientWidth;
      if (w && priceChartRef.current) {
        priceChartRef.current.applyOptions({ width: w });
      }
      if (w && macdChartRef.current) {
        macdChartRef.current.applyOptions({ width: w });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (priceChartRef.current) {
        priceChartRef.current.remove();
        priceChartRef.current = null;
      }
      if (macdChartRef.current) {
        macdChartRef.current.remove();
        macdChartRef.current = null;
      }
    };
  }, [data, ticker, overlays, active]);

  return (
    <div className="rounded-xl border border-gray-800 bg-[#0f1117] p-4">
      {/* Header row */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium text-gray-400">
          {ticker} — Price Chart
        </h2>

        {/* Overlay toggles */}
        {overlays && (
          <div className="flex flex-wrap gap-1.5">
            {(Object.keys(OVERLAY_LABELS) as OverlayKey[]).map((key) => (
              <button
                key={key}
                onClick={() => toggle(key)}
                className={`rounded-md border px-2 py-0.5 text-xs font-medium transition-colors ${
                  active[key]
                    ? "border-transparent text-white"
                    : "border-gray-700 bg-transparent text-gray-500 hover:bg-gray-800"
                }`}
                style={
                  active[key]
                    ? {
                        backgroundColor: OVERLAY_LABELS[key].color + "20",
                        borderColor: OVERLAY_LABELS[key].color + "50",
                        color: OVERLAY_LABELS[key].color,
                      }
                    : {}
                }
              >
                {OVERLAY_LABELS[key].label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Prediction banner */}
      {overlays && active.prediction && overlays.prediction_target && (
        <div className="mb-3 flex items-center gap-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3 py-2">
          <TrendingUp size={14} className="text-cyan-400" />
          <span className="text-xs text-cyan-300">
            30-day prediction:{" "}
            <span className="font-semibold">
              ${overlays.prediction_target.toFixed(2)}
            </span>{" "}
            <span
              className={
                overlays.prediction_direction === "up"
                  ? "text-green-400"
                  : "text-red-400"
              }
            >
              ({(((overlays.prediction_target - data[data.length - 1].close) / data[data.length - 1].close) * 100).toFixed(2)}%)
            </span>
          </span>
        </div>
      )}

      {/* Price chart */}
      <div ref={priceContainerRef} />

      {/* MACD chart (below) */}
      {active.macd && overlays?.macd?.length ? (
        <div className="mt-1">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-gray-500">
            MACD (12, 26, 9)
          </p>
          <div ref={macdContainerRef} />
        </div>
      ) : null}
    </div>
  );
}
