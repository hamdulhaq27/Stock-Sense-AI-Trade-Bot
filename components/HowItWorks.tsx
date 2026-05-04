"use client";

import { motion } from "framer-motion";

const STEPS = [
  { n:"01", title:"Collect",     color:"bg-primary",  ring:"ring-primary/30",  desc:"Live ingestion from Reddit WallStreetBets, StockTwits, and financial news APIs across all 5 target S&P 500 stocks." },
  { n:"02", title:"Preprocess",  color:"bg-bull",     ring:"ring-bull/30",    desc:"Noise removal, deduplication and financial-domain tokenization — preparing clean inputs for FinBERT classification." },
  { n:"03", title:"Analyze",     color:"bg-neutral",  ring:"ring-neutral/30", desc:"FinBERT scores raw sentiment. RSI, MACD, SMA-20 and SMA-50 computed in real-time per ticker." },
  { n:"04", title:"Predict",     color:"bg-bear",     ring:"ring-bear/30",    desc:"LSTM model forecasts directional movement. LangChain + GPT generates a plain-English explanation for every signal." },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-28 bg-surface-2">
      <div className="max-w-7xl mx-auto px-6 xl:px-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-20">
          <motion.span
            initial={{opacity:0}} whileInView={{opacity:1}} viewport={{once:true}}
            className="inline-block text-[11px] font-bold uppercase tracking-[0.16em] text-primary bg-primary/8 border border-primary/20 px-4 py-2 rounded-full mb-5"
          >
            The Process
          </motion.span>
          <motion.h2
            initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:0.1}}
            className="text-4xl sm:text-5xl font-black text-text-primary tracking-tight mb-5 leading-tight"
          >
            From Noise to Signal<br className="hidden sm:block"/> in 4 Steps
          </motion.h2>
          <motion.p
            initial={{opacity:0,y:16}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:0.2}}
            className="text-[17px] text-text-secondary font-light leading-relaxed"
          >
            A streamlined AI pipeline that transforms raw social media data into actionable trading intelligence in under 3 seconds.
          </motion.p>
        </div>

        {/* Steps */}
        <div className="relative grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Connector line */}
          <div className="hidden lg:block absolute top-10 left-[12.5%] right-[12.5%] h-0.5 bg-gradient-to-r from-primary via-bull to-bear opacity-20"/>

          {STEPS.map((s, i) => (
            <motion.div
              key={i}
              initial={{opacity:0, y:28}}
              whileInView={{opacity:1, y:0}}
              viewport={{once:true}}
              transition={{delay: i * 0.15, duration:0.55}}
              className="flex flex-col items-center text-center relative z-10"
            >
              {/* circle */}
              <div className={`w-20 h-20 ${s.color} text-white rounded-full flex items-center justify-center text-[26px] font-black font-mono shadow-xl ring-4 ${s.ring} mb-7 border-4 border-white`}>
                {s.n}
              </div>
              <div className="bg-white rounded-2xl border border-border p-6 shadow-sm w-full">
                <h3 className="text-[18px] font-black text-text-primary mb-3">{s.title}</h3>
                <p className="text-[13px] text-text-secondary font-light leading-relaxed">{s.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
