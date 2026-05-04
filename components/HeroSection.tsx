"use client";

import { motion } from "framer-motion";
import Link from "next/link";

// ─── Mini SVG chart for the floating card ───────────────────────────────────
function MiniChart() {
  const pts = [55,52,58,50,45,42,39,35,30,27,22,25,20,18,15];
  const W = 280, H = 90;
  const xStep = W / (pts.length - 1);
  const minP = Math.min(...pts), maxP = Math.max(...pts);
  const y = (p: number) => H - ((p - minP) / (maxP - minP + 1)) * (H - 10) - 5;
  const linePath = pts.map((p,i) => `${i===0?"M":"L"}${i*xStep},${y(p)}`).join(" ");
  const areaPath = linePath + ` L${(pts.length-1)*xStep},${H} L0,${H} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id="hg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#16A34A" stopOpacity="0.2"/>
          <stop offset="100%" stopColor="#16A34A" stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#hg)"/>
      <motion.path d={linePath} fill="none" stroke="#16A34A" strokeWidth="2.5"
        strokeLinecap="round" strokeLinejoin="round"
        initial={{pathLength:0}} animate={{pathLength:1}}
        transition={{duration:2.2, ease:"easeInOut", delay:0.4}}/>
    </svg>
  );
}

// ─── Floating badge ──────────────────────────────────────────────────────────
function Badge({ label, value, color, delay, style }: {
  label: string; value: string; color: string; delay: number;
  style: React.CSSProperties;
}) {
  return (
    <motion.div
      initial={{opacity:0, y:12, scale:0.92}}
      animate={{opacity:1, y:0, scale:1}}
      transition={{delay, type:"spring", stiffness:120, damping:14}}
      className="absolute bg-white/90 backdrop-blur-md border border-border/60 rounded-2xl shadow-lg shadow-black/8 px-4 py-3 flex flex-col gap-0.5 min-w-[150px]"
      style={style}
    >
      <span className="text-[10px] font-semibold uppercase tracking-widest text-text-muted">{label}</span>
      <span className={`text-[15px] font-bold font-mono ${color}`}>{value}</span>
    </motion.div>
  );
}

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-background pt-20 pb-10">
      {/* ── decorative blobs ── */}
      <div className="pointer-events-none absolute -top-32 right-[-10%] w-[700px] h-[700px] rounded-full bg-primary/5 blur-[120px]"/>
      <div className="pointer-events-none absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] rounded-full bg-[#B45309]/5 blur-[100px]"/>

      <div className="relative max-w-7xl mx-auto px-6 xl:px-8 w-full grid lg:grid-cols-2 gap-12 xl:gap-20 items-center">

        {/* ══ LEFT ══════════════════════════════════════════════════════════ */}
        <motion.div
          initial={{opacity:0, y:30}}
          animate={{opacity:1, y:0}}
          transition={{duration:0.7, ease:"easeOut"}}
          className="flex flex-col gap-8"
        >
          {/* Eyebrow pill */}
          <span className="inline-flex items-center gap-2 bg-primary/8 border border-primary/20 text-primary text-[11px] font-bold uppercase tracking-[0.16em] px-4 py-2 rounded-full w-max">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-50"/>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"/>
            </span>
            AI-Powered S&P 500 Intelligence
          </span>

          {/* Headline */}
          <div className="flex flex-col gap-3">
            <h1 className="text-5xl sm:text-6xl xl:text-[68px] font-black text-text-primary leading-[1.04] tracking-tight">
              The Market<br/>Never Sleeps.
            </h1>
            <h2 className="text-4xl sm:text-5xl xl:text-[54px] font-black leading-[1.08] tracking-tight">
              <span className="text-primary">Neither Does</span>
              <br/>
              <span className="text-text-secondary font-extrabold">StockSense AI.</span>
            </h2>
          </div>

          <p className="text-[17px] text-text-secondary leading-[1.75] max-w-lg font-light">
            Fuses <strong className="font-semibold text-text-primary">FinBERT NLP</strong> sentiment from Reddit &amp; StockTwits
            with <strong className="font-semibold text-text-primary">LSTM forecasting</strong> to deliver institutional-grade
            signals on top S&amp;P 500 stocks — in under 3 seconds.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap gap-4 items-center">
            <Link href="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-4 bg-primary text-white text-[15px] font-bold rounded-2xl shadow-xl shadow-primary/30 hover:bg-primary-dark hover:-translate-y-0.5 hover:shadow-primary/40 transition-all">
              Explore Dashboard
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </Link>
            <Link href="#how-it-works"
              className="inline-flex items-center gap-2 px-8 py-4 bg-surface border border-border text-text-primary text-[15px] font-semibold rounded-2xl hover:bg-surface-2 hover:border-border transition-all">
              How It Works
            </Link>
          </div>

          {/* Trust row */}
          <div className="flex flex-wrap items-center gap-8 pt-2">
            {[
              { v:"85%+", l:"Sentiment Accuracy" },
              { v:"60%+", l:"Directional Accuracy" },
              { v:"<3s",  l:"API Response" },
            ].map(s => (
              <div key={s.l} className="flex flex-col">
                <span className="text-[22px] font-black text-primary font-mono">{s.v}</span>
                <span className="text-[12px] text-text-muted font-medium">{s.l}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* ══ RIGHT — floating dashboard mockup ═══════════════════════════ */}
        <div className="relative flex items-center justify-center h-[580px] lg:h-auto">
          {/* outer glow ring */}
          <div className="absolute inset-6 rounded-3xl bg-primary/8 blur-3xl"/>

          {/* Main card */}
          <motion.div
            initial={{opacity:0, y:24, scale:0.96}}
            animate={{opacity:1, y:0, scale:1}}
            transition={{duration:0.8, delay:0.25, ease:"easeOut"}}
            className="relative w-full max-w-[420px] bg-white rounded-3xl shadow-2xl shadow-black/12 border border-border/60 overflow-hidden animate-float"
          >
            {/* card top bar */}
            <div className="bg-surface-2 px-5 py-4 border-b border-border-light flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-bull"/>
                <span className="text-[11px] font-bold text-text-muted uppercase tracking-widest font-mono">AAPL · LIVE</span>
              </div>
              <span className="text-[11px] font-mono text-text-muted">13:42 EST</span>
            </div>

            {/* price row */}
            <div className="px-5 py-5 flex justify-between items-start border-b border-border-light">
              <div>
                <div className="text-[11px] text-text-muted font-medium mb-1">Current Price</div>
                <div className="text-[36px] font-black text-text-primary font-mono tracking-tight leading-none">$182.40</div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-text-muted mb-1">Today</div>
                <div className="text-[18px] font-black text-bull font-mono">+3.04% ↑</div>
                <div className="text-[11px] text-text-muted font-mono mt-0.5">+$5.32</div>
              </div>
            </div>

            {/* chart */}
            <div className="h-[100px] w-full px-3 pt-3">
              <MiniChart/>
            </div>

            {/* signal pills */}
            <div className="px-4 pb-5 pt-2 grid grid-cols-3 gap-2">
              {[
                { l:"FinBERT", v:"0.84 Bullish", c:"text-bull bg-bull/8 border-bull/20" },
                { l:"RSI 14", v:"58.3 Neutral", c:"text-neutral bg-neutral/8 border-neutral/20" },
                { l:"MACD", v:"↑ Cross", c:"text-primary bg-primary/8 border-primary/20" },
              ].map(p => (
                <div key={p.l} className={`${p.c} border rounded-xl p-2 flex flex-col gap-0.5 text-center`}>
                  <span className="text-[9px] font-bold uppercase tracking-wider opacity-70">{p.l}</span>
                  <span className="text-[11px] font-bold font-mono">{p.v}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Floating badges */}
          <Badge label="AI Prediction" value="UP ↑ 67%" color="text-bull"
            delay={1.0} style={{top:"8%", left:"-5%"}}/>
          <Badge label="Sentiment Score" value="92 / 100" color="text-primary"
            delay={1.2} style={{bottom:"20%", left:"-8%"}}/>
          <Badge label="SMA-20 Support" value="$182.40" color="text-neutral"
            delay={1.4} style={{top:"22%", right:"-5%"}}/>
        </div>

      </div>
    </section>
  );
}
