import { Technical } from "@/lib/api";

interface TechIndicatorsProps {
  technical: Technical;
}

export default function TechIndicators({ technical }: TechIndicatorsProps) {
  const rsiLevel = technical.rsi_14 ?? 50;
  const rsiPct = Math.min(100, Math.max(0, rsiLevel));
  const rsiStatus = rsiLevel > 70 ? "Overbought" : rsiLevel < 30 ? "Oversold" : "Neutral";
  const rsiColor = rsiLevel > 70 ? "text-accent-red" : rsiLevel < 30 ? "text-accent-red" : "text-accent-amber";

  const macdValue = technical.macd ?? 0;
  const macdStatus = macdValue > 0 ? "bullish" : "bearish";
  const macdColor = macdStatus === "bullish" ? "text-accent-green" : "text-accent-red";

  const closePrice = technical.close ?? 0;
  const sma20Price = technical.sma_20 ?? closePrice;
  const sma50Price = technical.sma_50 ?? closePrice;

  const sma20Support = closePrice > sma20Price ? "Support" : "Resistance";
  const sma20Color = sma20Support === "Support" ? "text-primary" : "text-accent-red";

  const sma50Support = closePrice > sma50Price ? "Support" : "Resistance";
  const sma50Color = sma50Support === "Support" ? "text-primary" : "text-accent-red";

  const indicators = [
    {
      name: "RSI (14)",
      value: rsiLevel.toFixed(1),
      badge: rsiStatus,
      badgeColor: rsiStatus === "Overbought" || rsiStatus === "Oversold" ? "text-accent-red bg-accent-red/10 border-accent-red/20" : "text-accent-amber bg-accent-amber/10 border-accent-amber/20",
      barPct: rsiPct,
      barColor: rsiLevel > 70 ? "bg-accent-red" : rsiLevel < 30 ? "bg-accent-red" : "bg-accent-amber",
      sub: "Overbought >70 · Oversold <30",
    },
    {
      name: "MACD",
      value: macdValue.toFixed(2),
      badge: macdStatus === "bullish" ? "Bullish Cross" : "Bearish Cross",
      badgeColor: macdColor === "text-accent-green" ? "text-accent-green bg-accent-green/10 border-accent-green/20" : "text-accent-red bg-accent-red/10 border-accent-red/20",
      barPct: Math.min(100, Math.abs(macdValue) * 10),
      barColor: macdColor === "text-accent-green" ? "bg-accent-green" : "bg-accent-red",
      sub: "Signal line crossover " + (macdStatus === "bullish" ? "↑" : "↓"),
    },
    {
      name: "SMA-20",
      value: `$${sma20Price.toFixed(2)}`,
      badge: sma20Support,
      badgeColor: sma20Color === "text-primary" ? "text-primary bg-primary/10 border-primary/20" : "text-accent-red bg-accent-red/10 border-accent-red/20",
      barPct: Math.min(100, (closePrice / sma20Price) * 50),
      barColor: sma20Color === "text-primary" ? "bg-primary" : "bg-accent-red",
      sub: "Price " + (closePrice > sma20Price ? "above" : "below") + " 20-day avg",
    },
    {
      name: "SMA-50",
      value: `$${sma50Price.toFixed(2)}`,
      badge: sma50Support,
      badgeColor: sma50Color === "text-primary" ? "text-primary bg-primary/10 border-primary/20" : "text-accent-red bg-accent-red/10 border-accent-red/20",
      barPct: Math.min(100, (closePrice / sma50Price) * 50),
      barColor: sma50Color === "text-primary" ? "bg-primary" : "bg-accent-red",
      sub: "Price " + (closePrice > sma50Price ? "above" : "below") + " 50-day avg",
    },
  ];

  return (
    <div className="bg-white border border-border rounded-xl shadow-sm p-5 flex flex-col h-full">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-bold text-text-primary">Technical Indicators</h3>
        <span className="text-xs text-text-muted font-mono bg-surface-2 px-2 py-1 rounded">Real-time</span>
      </div>

      <div className="flex-1 flex flex-col gap-4">
        {indicators.map((ind) => (
          <div key={ind.name} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-text-muted">{ind.name}</span>
                <span className="ml-2 text-sm font-extrabold font-mono text-text-primary">{ind.value}</span>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${ind.badgeColor}`}>
                {ind.badge}
              </span>
            </div>
            <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${ind.barColor} opacity-70`}
                style={{ width: `${ind.barPct}%` }}
              />
            </div>
            <span className="text-[10px] text-text-muted">{ind.sub}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
