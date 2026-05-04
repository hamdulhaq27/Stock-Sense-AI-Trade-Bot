"use client";

import { motion } from "framer-motion";
import { Layers, BrainCircuit, TrendingUp, ActivitySquare, Zap, MessageSquareText } from "lucide-react";

const FEATURES = [
  {
    icon: Layers,
    color: "text-primary",
    bg: "bg-primary/10",
    glow: "shadow-primary/20",
    title: "Multi-Source Sentiment Fusion",
    desc: "Aggregates signals from Reddit WallStreetBets, StockTwits, and live financial news — unified into one score per stock.",
  },
  {
    icon: BrainCircuit,
    color: "text-bull",
    bg: "bg-bull/10",
    glow: "shadow-bull/20",
    title: "FinBERT Financial NLP",
    desc: "Domain-trained BERT understands financial lexicon, corporate earnings tone, and analyst sentiment that generic models miss.",
  },
  {
    icon: TrendingUp,
    color: "text-primary",
    bg: "bg-primary/10",
    glow: "shadow-primary/20",
    title: "LSTM Forecasting",
    desc: "Long Short-Term Memory networks predict short-horizon direction on AAPL, TSLA, AMZN, MSFT and NVDA with 60%+ accuracy.",
  },
  {
    icon: ActivitySquare,
    color: "text-neutral",
    bg: "bg-neutral/10",
    glow: "shadow-neutral/20",
    title: "Real-Time Technical Analysis",
    desc: "Live RSI, MACD, SMA-20 and SMA-50 — calculated per ticker and combined with sentiment for true confluence signals.",
  },
  {
    icon: Zap,
    color: "text-bear",
    bg: "bg-bear/10",
    glow: "shadow-bear/20",
    title: "FastAPI REST Backend",
    desc: "Fully async Python API serving predictions in under 3 seconds. Redis cache + PostgreSQL persistence for production reliability.",
  },
  {
    icon: MessageSquareText,
    color: "text-primary",
    bg: "bg-primary/10",
    glow: "shadow-primary/20",
    title: "AI Plain-English Explanations",
    desc: "LangChain + GPT generates a clear, readable rationale for every signal — so you always know the 'why' behind a rating.",
  },
];

export default function FeaturesGrid() {
  return (
    <section id="features" className="py-28 bg-background">
      <div className="max-w-7xl mx-auto px-6 xl:px-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-20">
          <motion.span
            initial={{opacity:0}} whileInView={{opacity:1}} viewport={{once:true}}
            className="inline-block text-[11px] font-bold uppercase tracking-[0.16em] text-primary bg-primary/8 border border-primary/20 px-4 py-2 rounded-full mb-5"
          >
            Platform Capabilities
          </motion.span>
          <motion.h2
            initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:0.1,duration:0.6}}
            className="text-4xl sm:text-5xl font-black text-text-primary tracking-tight mb-5 leading-tight"
          >
            Every Edge You Need<br className="hidden sm:block"/> to Trade Smarter
          </motion.h2>
          <motion.p
            initial={{opacity:0,y:16}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:0.2,duration:0.5}}
            className="text-[17px] text-text-secondary font-light leading-relaxed"
          >
            We stack AI, NLP and real-time technical analysis into one fast, explainable pipeline — so you never fly blind.
          </motion.p>
        </div>

        {/* Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={i}
              initial={{opacity:0, y:28}}
              whileInView={{opacity:1, y:0}}
              viewport={{once:true}}
              transition={{delay: i * 0.07, duration:0.5, ease:"easeOut"}}
              whileHover={{y:-6, transition:{duration:0.2}}}
              className="group bg-surface rounded-2xl border border-border p-7 flex flex-col gap-5 hover:shadow-xl hover:shadow-black/[0.06] hover:border-border transition-all cursor-default"
            >
              <div className={`w-13 h-13 ${f.bg} rounded-2xl flex items-center justify-center shadow-lg ${f.glow} group-hover:scale-110 transition-transform`}>
                <f.icon className={`w-6 h-6 ${f.color}`} strokeWidth={1.8}/>
              </div>
              <div>
                <h3 className="text-[17px] font-bold text-text-primary mb-2 leading-snug">{f.title}</h3>
                <p className="text-[14px] text-text-secondary leading-relaxed font-light">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
