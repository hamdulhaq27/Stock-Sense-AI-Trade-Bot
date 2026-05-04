"use client";

import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, X } from "lucide-react";
import { useState } from "react";
import { Sentiment } from "@/lib/api";

interface SignalsTableProps {
  sentiment: Sentiment;
  symbol: string;
}

// Threshold for classifying a -1..+1 score
const BULL_THRESH = 0.05;
const BEAR_THRESH = -0.05;

function scoreToLabel(score: number): "Bullish" | "Neutral" | "Bearish" {
  if (score > BULL_THRESH) return "Bullish";
  if (score < BEAR_THRESH) return "Bearish";
  return "Neutral";
}

function scoreToDir(score: number): "up" | "down" | "neutral" {
  if (score > BULL_THRESH) return "up";
  if (score < BEAR_THRESH) return "down";
  return "neutral";
}

/** Map a -1..+1 score to a 0–100 display value for the progress bar */
function toBarPct(score: number): number {
  return Math.round(((score + 1) / 2) * 100);
}

const sentimentDescriptions: Record<string, Record<string, string>> = {
  "News Sentiment": {
    Bullish:
      "Financial news outlets are reporting positive developments — earnings beats, analyst upgrades, or favourable macro news. FinBERT confidence-weighted score is above the bullish threshold.",
    Bearish:
      "Negative news coverage is dominating headlines. Bearish score indicates concerns about earnings, analyst downgrades, or unfavourable market conditions.",
    Neutral:
      "Mixed news coverage with roughly balanced positive and negative stories. Markets remain indecisive — watch for a breakout catalyst.",
  },
  "Reddit Sentiment": {
    Bullish:
      "Reddit communities (r/wallstreetbets, r/investing) are enthusiastic. Post-count weighted compound score normalised via tanh is positive, indicating genuine community interest.",
    Bearish:
      "Reddit discussions are predominantly negative. Community sentiment may signal underlying concern about fundamentals or a recent negative catalyst.",
    Neutral:
      "Mixed Reddit opinions with balanced bull/bear arguments. Check relevant subreddits for the leading narrative.",
  },
  "StockTwits Sentiment": {
    Bullish:
      "StockTwits traders are posting bullish messages. Post-count weighted average sentiment is above neutral — active buying interest.",
    Bearish:
      "Bearish StockTwits sentiment suggests traders are cautious or positioning short. Watch for volume spikes that may accelerate the move.",
    Neutral:
      "Balanced StockTwits activity. High volume with neutral sentiment can precede a significant directional move.",
  },
};

export default function SignalsTable({ sentiment, symbol }: SignalsTableProps) {
  const [selectedSignal, setSelectedSignal] = useState<number | null>(null);

  const signals = [
    {
      name: "News Sentiment",
      score: sentiment.news_score,          // -1..+1
      count: sentiment.news_count,
      countLabel: `${sentiment.news_count} sources`,
    },
    {
      name: "Reddit Sentiment",
      score: sentiment.reddit_score,        // -1..+1
      count: sentiment.reddit_count,
      countLabel: `${sentiment.reddit_count} posts`,
    },
    {
      name: "StockTwits Sentiment",
      score: sentiment.twit_score,          // -1..+1
      count: sentiment.twit_count,
      countLabel: `${sentiment.twit_count} posts`,
    },
  ].map((s) => ({
    ...s,
    sentiment: scoreToLabel(s.score),
    dir: scoreToDir(s.score),
    direction: scoreToDir(s.score) === "up" ? "UP" : scoreToDir(s.score) === "down" ? "DOWN" : "STABLE",
    barPct: toBarPct(s.score),
    displayScore: Math.round(toBarPct(s.score)), // 0–100 for display
  }));

  const sentimentStyle: Record<string, string> = {
    Bullish: "bg-accent-green/10 text-accent-green border-accent-green/25",
    Neutral:  "bg-accent-amber/10 text-accent-amber border-accent-amber/25",
    Bearish:  "bg-accent/10 text-accent border-accent/25",
  };

  const dirStyle: Record<string, string> = {
    up:      "text-accent-green",
    down:    "text-accent",
    neutral: "text-text-muted",
  };

  const barColor: Record<string, string> = {
    up:      "bg-accent-green",
    down:    "bg-accent-red",
    neutral: "bg-accent-amber",
  };

  function DirIcon({ dir }: { dir: string }) {
    if (dir === "up")   return <TrendingUp  className="w-4 h-4" />;
    if (dir === "down") return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  }

  const selected = selectedSignal !== null ? signals[selectedSignal] : null;

  return (
    <>
      <div className="bg-white border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-text-primary">
              Sentiment Signals · {symbol}
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Click any row for detailed analysis · Scores in (−1, +1)
            </p>
          </div>
          {/* Composite badge */}
          <div className="text-xs font-mono bg-surface-2 border border-border px-3 py-1.5 rounded-lg">
            Composite{" "}
            <span className={sentiment.composite >= 0 ? "text-accent-green font-bold" : "text-accent-red font-bold"}>
              {sentiment.composite >= 0 ? "+" : ""}
              {sentiment.composite.toFixed(3)}
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-surface-2 text-[11px] font-bold text-text-muted uppercase tracking-wider border-b border-border">
                <th className="text-left  px-6 py-3.5">Source</th>
                <th className="text-left  px-4 py-3.5">Sentiment</th>
                <th className="text-center px-4 py-3.5">Score (0–100)</th>
                <th className="text-center px-4 py-3.5">Direction</th>
                <th className="text-right  px-6 py-3.5">Data Points</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-light">
              {signals.map((s, i) => (
                <motion.tr
                  key={i}
                  onClick={() => setSelectedSignal(i)}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07, duration: 0.3 }}
                  className="group hover:bg-surface-2/50 transition-colors cursor-pointer"
                >
                  {/* Source name */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-extrabold text-text-primary font-mono text-sm group-hover:text-primary transition-colors">
                      {s.name}
                    </div>
                    <div className="text-[10px] text-text-muted font-mono mt-0.5">
                      raw {s.score >= 0 ? "+" : ""}{s.score.toFixed(4)}
                    </div>
                  </td>

                  {/* Badge */}
                  <td className="px-4 py-4 whitespace-nowrap">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-md border ${sentimentStyle[s.sentiment]}`}>
                      {s.sentiment}
                    </span>
                  </td>

                  {/* Bar + number (0–100 scale) */}
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-16 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${barColor[s.dir]}`}
                          style={{ width: `${s.barPct}%` }}
                        />
                      </div>
                      <span className="font-mono text-sm font-bold text-text-secondary w-7">
                        {s.displayScore}
                      </span>
                    </div>
                  </td>

                  {/* Direction */}
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center gap-1 text-xs font-bold font-mono ${dirStyle[s.dir]}`}>
                      <DirIcon dir={s.dir} />
                      {s.direction}
                    </span>
                  </td>

                  {/* Count */}
                  <td className={`px-6 py-4 whitespace-nowrap text-right font-mono text-sm font-extrabold ${dirStyle[s.dir]}`}>
                    {s.countLabel}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Detail modal ── */}
      <AnimatePresence>
        {selected !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedSignal(null)}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            >
              {/* Modal header */}
              <div className="px-6 py-5 border-b border-border-light flex items-start justify-between sticky top-0 bg-white">
                <div>
                  <h2 className="text-lg font-bold text-text-primary">{selected.name}</h2>
                  <p className="text-sm text-text-muted mt-1">{symbol} · Detailed Analysis</p>
                </div>
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="p-2 rounded-lg hover:bg-surface-2 transition-colors"
                >
                  <X className="w-5 h-5 text-text-muted" />
                </button>
              </div>

              {/* Modal body */}
              <div className="px-6 py-5 space-y-5">
                {/* Badge + scores */}
                <div className="flex items-center gap-6">
                  <span className={`text-sm font-bold px-3 py-1.5 rounded-lg border ${sentimentStyle[selected.sentiment]}`}>
                    {selected.sentiment}
                  </span>
                  <div className="flex gap-6 text-center">
                    <div>
                      <div className="text-2xl font-extrabold text-text-primary font-mono">
                        {selected.displayScore}
                      </div>
                      <div className="text-[10px] text-text-muted">out of 100</div>
                    </div>
                    <div>
                      <div className={`text-2xl font-extrabold font-mono ${selected.score >= 0 ? "text-accent-green" : "text-accent-red"}`}>
                        {selected.score >= 0 ? "+" : ""}{selected.score.toFixed(4)}
                      </div>
                      <div className="text-[10px] text-text-muted">raw (−1..+1)</div>
                    </div>
                  </div>
                </div>

                {/* Analysis text */}
                <div className="bg-surface-2 rounded-lg p-4 border border-border-light">
                  <h3 className="text-sm font-bold text-text-primary mb-3">Analysis</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {sentimentDescriptions[selected.name]?.[selected.sentiment] ??
                      "Sentiment analysis indicates mixed market opinion."}
                  </p>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-surface-2 rounded-lg p-4 border border-border-light">
                    <span className="text-xs font-semibold text-text-muted uppercase">Data Points</span>
                    <span className="text-2xl font-bold text-text-primary font-mono block mt-1">
                      {selected.count}
                    </span>
                  </div>
                  <div className="bg-surface-2 rounded-lg p-4 border border-border-light">
                    <span className="text-xs font-semibold text-text-muted uppercase">Direction</span>
                    <div className={`flex items-center gap-2 mt-2 ${dirStyle[selected.dir]}`}>
                      <DirIcon dir={selected.dir} />
                      <span className="text-lg font-bold font-mono">{selected.direction}</span>
                    </div>
                  </div>
                </div>

                {/* Headlines (only on News row) */}
                {selected.name === "News Sentiment" && (
                  <div>
                    <h3 className="text-sm font-bold text-text-primary mb-3">
                      Top Headlines Driving Sentiment
                    </h3>
                    <div className="space-y-3">
                      {sentiment.top_headlines && sentiment.top_headlines.length > 0 ? (
                        sentiment.top_headlines.slice(0, 5).map((h, idx) => (
                          <div
                            key={idx}
                            className="bg-surface-2 rounded-lg p-4 border border-border-light"
                          >
                            <p className="text-sm font-semibold text-text-primary leading-relaxed mb-2">
                              {h.headline}
                            </p>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3 text-xs text-text-muted">
                                <span className="font-mono">{h.source || "Unknown"}</span>
                                <span>·</span>
                                <span>{h.date}</span>
                                <span>·</span>
                                <span className="font-mono">conf {h.score.toFixed(3)}</span>
                              </div>
                              <span className={`text-xs font-bold px-2 py-1 rounded-md border ${
                                h.sentiment === 1
                                  ? "bg-accent-green/10 text-accent-green border-accent-green/25"
                                  : h.sentiment === -1
                                  ? "bg-accent/10 text-accent border-accent/25"
                                  : "bg-accent-amber/10 text-accent-amber border-accent-amber/25"
                              }`}>
                                {h.sentiment === 1 ? "Bullish" : h.sentiment === -1 ? "Bearish" : "Neutral"}
                              </span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-6 text-text-muted text-sm">
                          No headline data available for this window.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}