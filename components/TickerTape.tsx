const stocks = [
  { symbol: "AAPL", price: "$182.40", change: "+3.04%", dir: "up" },
  { symbol: "TSLA", price: "$175.22", change: "+1.8%", dir: "up" },
  { symbol: "NVDA", price: "$854.10", change: "+7.1%", dir: "up" },
  { symbol: "MSFT", price: "$415.50", change: "+0.5%", dir: "neutral" },
  { symbol: "META", price: "$485.20", change: "-2.3%", dir: "down" },
  { symbol: "AMZN", price: "$178.15", change: "+2.1%", dir: "up" },
  { symbol: "GOOGL", price: "$178.89", change: "+1.4%", dir: "up" },
  { symbol: "JPM", price: "$210.32", change: "-0.4%", dir: "down" },
  { symbol: "BRK.B", price: "$413.60", change: "+0.2%", dir: "neutral" },
  { symbol: "V", price: "$278.45", change: "+0.9%", dir: "up" },
];

const doubled = [...stocks, ...stocks];

export default function TickerTape() {
  return (
    <div className="w-full bg-text-primary border-y border-text-primary/10 py-3 overflow-hidden">
      <div className="flex w-max animate-ticker">
        {doubled.map((s, i) => (
          <div key={i} className="flex items-center gap-2 px-6 border-r border-white/10 last:border-none">
            <span className="text-xs font-bold text-white font-mono">{s.symbol}</span>
            <span className="text-xs text-white/60 font-mono">{s.price}</span>
            <span
              className={`text-xs font-semibold font-mono ${
                s.dir === "up" ? "text-accent-green-light" : s.dir === "down" ? "text-accent-light" : "text-white/50"
              }`}
            >
              {s.dir === "up" ? "↑" : s.dir === "down" ? "↓" : "→"} {s.change}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
