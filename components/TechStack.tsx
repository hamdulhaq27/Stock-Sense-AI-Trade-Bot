"use client";

import { motion } from "framer-motion";

const techs = [
  { name: "FinBERT", detail: "Financial NLP" },
  { name: "HuggingFace", detail: "Model Hub" },
  { name: "TensorFlow", detail: "Deep Learning" },
  { name: "FastAPI", detail: "REST Backend" },
  { name: "Redis", detail: "Caching Layer" },
  { name: "PostgreSQL", detail: "Database" },
  { name: "LangChain", detail: "LLM Reasoning" },
];

export default function TechStack() {
  return (
    <section className="py-16 bg-surface-2 border-t border-border">
      <div className="max-w-7xl mx-auto px-6 md:px-10">
        <p className="text-center text-xs font-bold uppercase tracking-widest text-text-muted mb-10">
          Built with Industry-Leading Open Source
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          {techs.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              className="flex flex-col items-center gap-1 bg-white border border-border rounded-xl px-6 py-4 shadow-sm hover:shadow-md hover:border-primary/30 hover:-translate-y-1 transition-all cursor-default"
            >
              <span className="text-base font-bold text-text-primary">{t.name}</span>
              <span className="text-xs text-text-muted">{t.detail}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
