"use client";

import { motion } from "framer-motion";
import { useRef, useEffect, useState } from "react";

const stats = [
  { value: "5", suffix: "", label: "Target S&P 500 Stocks", sub: "AAPL · TSLA · MSFT · NVDA · META" },
  { value: "85", suffix: "%+", label: "Sentiment Accuracy", sub: "FinBERT NLP Model" },
  { value: "60", suffix: "%+", label: "Directional Accuracy", sub: "LSTM Forecasting" },
  { value: "3", suffix: "s<", label: "API Response Time", sub: "FastAPI Backend" },
];

function Counter({ target, suffix }: { target: number; suffix: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          let start = 0;
          const step = target / 50;
          const timer = setInterval(() => {
            start += step;
            if (start >= target) { setCount(target); clearInterval(timer); }
            else setCount(Math.floor(start));
          }, 30);
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [target]);

  return <span ref={ref}>{count}{suffix}</span>;
}

export default function StatsBar() {
  return (
    <section className="bg-surface-2 border-y border-border py-14">
      <div className="max-w-7xl mx-auto px-6 md:px-10">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:divide-x lg:divide-border">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="flex flex-col items-center text-center lg:px-8"
            >
              <div className="text-4xl md:text-5xl font-extrabold text-primary font-mono mb-1 tracking-tight">
                <Counter target={parseInt(s.value)} suffix={s.suffix} />
              </div>
              <div className="text-sm font-semibold text-text-primary mb-1">{s.label}</div>
              <div className="text-xs text-text-muted">{s.sub}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
