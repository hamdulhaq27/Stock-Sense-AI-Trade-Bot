"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Lock, TrendingUp, TrendingDown, Minus } from "lucide-react";

const signals = [
  { symbol: "AAPL", name: "Apple Inc.", sentiment: "Bullish", score: 92, change: "+5.2%", dir: "up" },
  { symbol: "NVDA", name: "NVIDIA Corp.", sentiment: "Bullish", score: 95, change: "+7.1%", dir: "up" },
  { symbol: "TSLA", name: "Tesla Inc.", sentiment: "Bullish", score: 88, change: "+3.8%", dir: "up" },
  { symbol: "MSFT", name: "Microsoft Corp.", sentiment: "Neutral", score: 52, change: "+0.5%", dir: "neutral" },
  { symbol: "META", name: "Meta Platforms", sentiment: "Bearish", score: 35, change: "-2.3%", dir: "down" },
];

const sentimentStyle: Record<string, string> = {
  Bullish: "bg-accent-green/10 text-accent-green border-accent-green/20",
  Neutral: "bg-accent-amber/10 text-accent-amber border-accent-amber/20",
  Bearish: "bg-accent/10 text-accent border-accent/20",
};

const changeColor: Record<string, string> = {
  up: "text-accent-green",
  down: "text-accent",
  neutral: "text-text-muted",
};

export default function LiveSignalsPreview() {
  return (
    <section className="py-24 bg-background">
      <div className="max-w-5xl mx-auto px-6 md:px-10">
        <div className="text-center mb-12">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-block text-xs font-bold uppercase tracking-widest text-primary bg-primary/8 border border-primary/15 px-3 py-1.5 rounded-full mb-4"
          >
            Live Signals Preview
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-4xl font-extrabold text-text-primary tracking-tight mb-3"
          >
            Real-Time Sentiment Signals
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-text-secondary text-lg font-light"
          >
            A live preview of the AI intelligence powering the platform.
          </motion.p>
        </div>

        <div className="relative rounded-2xl border border-border bg-white shadow-xl shadow-black/5 overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-5 px-6 py-4 border-b border-border bg-surface-2 text-xs font-bold text-text-muted uppercase tracking-wider">
            <div className="col-span-2">Company</div>
            <div>Sentiment</div>
            <div className="text-center">Score</div>
            <div className="text-right">Change</div>
          </div>

          {/* Table Rows */}
          <div className="divide-y divide-border">
            {signals.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="grid grid-cols-5 items-center px-6 py-4 hover:bg-surface-2/60 transition-colors"
              >
                <div className="col-span-2">
                  <div className="font-bold text-text-primary font-mono">{s.symbol}</div>
                  <div className="text-xs text-text-muted">{s.name}</div>
                </div>
                <div>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${sentimentStyle[s.sentiment]}`}>
                    {s.sentiment}
                  </span>
                </div>
                <div className="text-center font-mono text-sm font-bold text-text-secondary">{s.score}</div>
                <div className={`text-right font-mono text-sm font-bold flex items-center justify-end gap-1 ${changeColor[s.dir]}`}>
                  {s.dir === "up" ? <TrendingUp className="w-3.5 h-3.5" /> : s.dir === "down" ? <TrendingDown className="w-3.5 h-3.5" /> : <Minus className="w-3.5 h-3.5" />}
                  {s.change}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Blur Overlay */}
          <div className="absolute bottom-0 left-0 right-0 h-36 bg-gradient-to-t from-white via-white/70 to-transparent flex items-end justify-center pb-5">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white font-semibold rounded-xl shadow-md shadow-primary/20 hover:bg-primary-dark hover:-translate-y-0.5 transition-all text-sm"
            >
              <Lock className="w-4 h-4" />
              Unlock Full Dashboard Access
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
