"use client";

import Link from "next/link";
import { Search, Bell } from "lucide-react";
import { useState } from "react";

interface TopBarProps {
  activeSymbol: string;
  onSymbolChange: (symbol: string) => void;
}

const stocks = ["AAPL", "TSLA", "AMZN", "MSFT", "NVDA", "GOOGL", "META", "NFLX", "UBER", "JPM", "JNJ", "BA", "AMD", "ORCL", "GE", "PYPL", "SPOT", "PLTR", "SNOW", "DASH", "ADBE"];

export default function TopBar({ activeSymbol, onSymbolChange }: TopBarProps) {
  const [searchInput, setSearchInput] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSymbolChange(searchInput.toUpperCase());
      setSearchInput("");
    }
  };

  return (
    <header className="h-auto bg-white border-b border-border sticky top-0 z-50 shadow-sm shadow-black/[0.04]">
      {/* Main bar */}
      <div className="px-6 md:px-8 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
              <path d="M3 12h4l3-9 5 18 3-9h3" />
            </svg>
          </div>
          <span className="font-bold text-base text-text-primary hidden sm:block">
            StockSense<span className="text-primary">AI</span>
          </span>
        </Link>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex-1 max-w-sm">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search ticker... e.g. AAPL"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full bg-surface-2 border border-border rounded-lg pl-9 pr-4 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all"
            />
          </div>
        </form>

        {/* Right side */}
        <div className="flex items-center gap-3 shrink-0">
          <button className="p-2 rounded-lg border border-border bg-surface hover:bg-surface-2 transition-colors relative">
            <Bell className="w-4 h-4 text-text-secondary" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-accent rounded-full" />
          </button>
          <div className="flex items-center gap-2 bg-accent-green/8 border border-accent-green/20 px-3 py-1.5 rounded-full">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-green opacity-60"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-green"></span>
            </span>
            <span className="text-xs font-semibold text-accent-green hidden sm:block">FinBERT + LSTM Live</span>
          </div>
        </div>
      </div>

      {/* Stock selector tabs */}
      <div className="px-6 md:px-8 pb-0 flex items-center gap-1 overflow-x-auto scrollbar-none border-t border-border-light">
        {stocks.map((s) => (
          <button
            key={s}
            onClick={() => onSymbolChange(s)}
            className={`px-4 py-2.5 text-sm font-bold font-mono whitespace-nowrap border-b-2 transition-all ${
              activeSymbol === s
                ? "border-primary text-primary"
                : "border-transparent text-text-muted hover:text-text-secondary hover:border-border"
            }`}
          >
            {s}
          </button>
        ))}
      </div>
    </header>
  );
}
