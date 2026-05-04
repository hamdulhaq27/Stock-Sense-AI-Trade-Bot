"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { PredictionData, getHistory, HistoryData } from "@/lib/api";

interface PriceChartProps {
  data: PredictionData;
}

const tabs = ["1D", "1W", "1M", "3M"];
const tabDays: Record<string, number> = {
  "1D": 1,
  "1W": 5,
  "1M": 21,
  "3M": 63,
};

function generateIntraday1D(currentPrice: number): Array<{ time: string; close: number }> {
  const times = ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00"];
  const volatility = currentPrice * 0.005;
  let price = currentPrice * 0.98;

  return times.map(time => {
    price = price * (1 + (Math.random() - 0.5) * 0.01);
    price = Math.max(price, currentPrice * 0.95);
    price = Math.min(price, currentPrice * 1.05);
    return { time, close: parseFloat(price.toFixed(2)) };
  });
}

function buildPath(points: number[], w: number, h: number): string {
  if (points.length < 2) return "";
  const xStep = w / (points.length - 1);
  return points
    .map((p, i) => {
      const x = i * xStep;
      const y = h - (p / 100) * h;
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");
}

function buildArea(points: number[], w: number, h: number): string {
  if (points.length < 2) return "";
  return buildPath(points, w, h) + ` L ${w} ${h} L 0 ${h} Z`;
}

function normalizeData(history: HistoryData): { prices: number[]; sma20: number[]; sma50: number[]; dates: string[] } {
  const prices = history.data.map((p) => p.close);
  const sma20 = history.data.map((p) => p.sma_20);
  const sma50 = history.data.map((p) => p.sma_50);
  const dates = history.data.map((p) => p.date);

  if (prices.length === 0) {
    return { prices: [], sma20: [], sma50: [], dates: [] };
  }

  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice || 1;

  const normalized = (arr: number[]) =>
    arr.map((v) => ((v - minPrice) / range) * 100);

  return {
    prices: normalized(prices),
    sma20: normalized(sma20),
    sma50: normalized(sma50),
    dates,
  };
}

export default function PriceChart({ data }: PriceChartProps) {
  const [activeTab, setActiveTab] = useState("1D");
  const [history, setHistory] = useState<HistoryData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        if (activeTab === "1D") {
          const intraday1D = generateIntraday1D(data.technical.close);
          const mock: HistoryData = {
            symbol: data.symbol,
            period_days: 1,
            data: intraday1D.map((d) => ({
              date: new Date().toISOString().split("T")[0],
              open: d.close,
              high: d.close * 1.01,
              low: d.close * 0.99,
              close: d.close,
              volume: 1000000,
              rsi_14: 55,
              macd: 0.5,
              sma_20: d.close - 0.5,
              sma_50: d.close - 1,
              daily_return_pct: 0.5,
            })),
          };
          setHistory(mock);
        } else {
          const days = tabDays[activeTab];
          const result = await getHistory(data.symbol, days);
          setHistory(result);
        }
      } catch (error) {
        console.error("Failed to fetch history:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [activeTab, data.symbol, data.technical.close]);

  if (!history || loading) {
    return (
      <div className="bg-white border border-border rounded-xl shadow-sm p-8 h-96 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-text-muted text-sm">Loading chart data...</p>
        </div>
      </div>
    );
  }

  const W = 800,
    H = 220;

  const normalized = normalizeData(history);
  const linePath = buildPath(normalized.prices, W, H);
  const areaPath = buildArea(normalized.prices, W, H);
  const sma20Path = buildPath(normalized.sma20, W, H);
  const sma50Path = buildPath(normalized.sma50, W, H);

  const minPrice = history.data.length > 0 ? Math.min(...history.data.map((p) => p.close)) : data.technical.close * 0.98;
  const maxPrice = history.data.length > 0 ? Math.max(...history.data.map((p) => p.close)) : data.technical.close * 1.02;

  const priceLabels = [
    `$${maxPrice.toFixed(2)}`,
    `$${((maxPrice + minPrice) * 0.75).toFixed(2)}`,
    `$${((maxPrice + minPrice) / 2).toFixed(2)}`,
    `$${((maxPrice + minPrice) * 0.25).toFixed(2)}`,
    `$${minPrice.toFixed(2)}`,
  ];

  const timeLabels =
    normalized.dates.length > 0
      ? [
          normalized.dates[0],
          normalized.dates[Math.floor(normalized.dates.length / 4)],
          normalized.dates[Math.floor(normalized.dates.length / 2)],
          normalized.dates[Math.floor((normalized.dates.length * 3) / 4)],
          normalized.dates[normalized.dates.length - 1],
        ]
      : ["—", "—", "—", "—", "—"];

  return (
    <div className="bg-white border border-border rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border-light flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="text-lg font-bold text-text-primary">{data.symbol} Price & Sentiment</div>
          <div className="text-xs text-text-muted font-mono mt-0.5">
            {history.period_days} trading day{history.period_days > 1 ? "s" : ""} · Current: ${data.technical.close.toFixed(2)}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Legend */}
          <div className="hidden sm:flex items-center gap-4 text-xs text-text-muted font-medium">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-primary rounded" />
              Price
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-accent-amber rounded border-dashed border border-accent-amber" />
              SMA-20
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-accent rounded border-dashed border border-accent" />
              SMA-50
            </div>
          </div>
          {/* Tab switcher */}
          <div className="flex bg-surface-2 rounded-lg p-1 border border-border gap-0.5">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                disabled={loading}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all disabled:opacity-50 ${
                  activeTab === t
                    ? "bg-white text-primary shadow-sm border border-border"
                    : "text-text-muted hover:text-text-secondary"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart area */}
      <div className="flex">
        {/* Y-Axis */}
        <div className="w-14 shrink-0 flex flex-col justify-between py-4 pl-4 text-[10px] font-mono text-text-muted">
          {priceLabels.map((l, i) => (
            <span key={i}>{l}</span>
          ))}
        </div>

        {/* SVG Chart */}
        <div className="flex-1 relative h-64">
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1A56DB" stopOpacity="0.12" />
                <stop offset="100%" stopColor="#1A56DB" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            {/* Grid */}
            {[0, 0.25, 0.5, 0.75, 1].map((t) => (
              <line key={t} x1="0" x2={W} y1={H * t} y2={H * t} stroke="#E2DDD4" strokeWidth="1" strokeDasharray="4 4" />
            ))}

            {/* Area */}
            {areaPath && <path d={areaPath} fill="url(#areaGrad)" />}

            {/* SMA-50 */}
            {sma50Path && (
              <motion.path
                d={sma50Path}
                fill="none"
                stroke="#E53E3E"
                strokeWidth="1.5"
                strokeDasharray="6 4"
                opacity="0.6"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.5, ease: "easeInOut", delay: 0.3 }}
              />
            )}

            {/* SMA-20 */}
            {sma20Path && (
              <motion.path
                d={sma20Path}
                fill="none"
                stroke="#D97706"
                strokeWidth="1.5"
                strokeDasharray="6 4"
                opacity="0.7"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.5, ease: "easeInOut", delay: 0.15 }}
              />
            )}

            {/* Main price line */}
            {linePath && (
              <motion.path
                d={linePath}
                fill="none"
                stroke="#1A56DB"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 2, ease: "easeInOut" }}
              />
            )}

            {/* Last point dot */}
            {normalized.prices.length > 0 && (
              <circle cx={W} cy={H - (normalized.prices[normalized.prices.length - 1] / 100) * H} r="5" fill="#1A56DB" stroke="white" strokeWidth="2" />
            )}
          </svg>

          {/* Hover tooltip */}
          {history.data.length > 0 && (
            <div className="absolute top-6 right-[22%] pointer-events-none">
              <div className="bg-white border border-border rounded-xl shadow-lg p-3 text-xs w-40">
                <div className="font-mono text-text-muted mb-2">{history.data[history.data.length - 1].date}</div>
                <div className="flex justify-between mb-1">
                  <span className="text-text-muted">Close</span>
                  <span className="font-bold font-mono text-text-primary">${history.data[history.data.length - 1].close.toFixed(2)}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span className="text-text-muted">SMA-20</span>
                  <span className="font-mono text-text-secondary">${history.data[history.data.length - 1].sma_20.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Change</span>
                  <span className={`font-bold ${history.data[history.data.length - 1].daily_return_pct > 0 ? "text-accent-green" : "text-accent-red"}`}>
                    {history.data[history.data.length - 1].daily_return_pct > 0 ? "+" : ""}
                    {history.data[history.data.length - 1].daily_return_pct.toFixed(2)}%
                  </span>
                </div>
              </div>
              <div className="w-px h-16 bg-primary/30 mx-auto" />
              <div className="w-3 h-3 rounded-full bg-primary border-2 border-white shadow mx-auto -mt-1.5" />
            </div>
          )}
        </div>
      </div>

      {/* X-Axis */}
      <div className="flex pl-14 pr-4 pb-3 justify-between text-[10px] font-mono text-text-muted">
        {timeLabels.map((l, i) => (
          <span key={i}>{l}</span>
        ))}
      </div>
    </div>
  );
}
