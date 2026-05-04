"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string;
  subValue: string;
  subLabel?: string;
  subColor: string;
  icon: LucideIcon;
  iconColor: string;
  delay?: number;
}

export default function KPICard({ title, value, subValue, subLabel, subColor, icon: Icon, iconColor, delay = 0 }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      whileHover={{ y: -2, transition: { duration: 0.18 } }}
      className="group bg-white border border-border rounded-xl p-5 shadow-sm hover:shadow-md hover:border-border transition-all relative overflow-hidden"
    >
      {/* Top accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${iconColor} opacity-60 group-hover:opacity-100 transition-opacity`} />

      <div className="flex items-start justify-between mb-4">
        <span className="text-sm font-medium text-text-muted">{title}</span>
        <div className={`p-2 rounded-lg bg-${iconColor}/10`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
      </div>

      <div className="text-3xl font-extrabold text-text-primary font-mono tracking-tight mb-1">
        {value}
      </div>

      <div className="flex items-center gap-1.5 text-sm">
        <span className={`font-bold font-mono ${subColor}`}>{subValue}</span>
        {subLabel && <span className="text-text-muted font-light">{subLabel}</span>}
      </div>
    </motion.div>
  );
}
