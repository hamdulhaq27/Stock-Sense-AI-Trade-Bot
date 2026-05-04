"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, TrendingUp, TrendingDown } from "lucide-react";

interface TickerData {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  latest_close: number | null;
  daily_return_pct: number | null;
  rsi_14: number | null;
  macd: number | null;
  sma_20: number | null;
  sma_50: number | null;
  volume_ratio: number | null;
}

const ITEMS_PER_PAGE = 20;

export default function TickersTable() {
  const [tickers, setTickers] = useState<TickerData[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllTickers();
  }, []);

  const fetchAllTickers = async () => {
    try {
      setLoading(true);
      const symbolsRes = await fetch("http://localhost:8000/stocks/");
      if (!symbolsRes.ok) throw new Error("Failed to fetch symbols");

      const { symbols } = await symbolsRes.json();

      const tickerData: TickerData[] = [];
      for (const symbol of symbols) {
        try {
          const res = await fetch(`http://localhost:8000/stocks/${symbol}`);
          if (res.ok) {
            const data = await res.json();
            tickerData.push(data);
          }
        } catch {
          console.log(`Failed to fetch ${symbol}`);
        }
      }

      setTickers(tickerData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tickers");
      setTickers([]);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(tickers.length / ITEMS_PER_PAGE);
  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedTickers = tickers.slice(startIdx, startIdx + ITEMS_PER_PAGE);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"/>
          <p className="text-text-secondary">Loading tickers...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-bear mb-4">Error: {error}</p>
          <button
            onClick={fetchAllTickers}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Table */}
      <div className="overflow-x-auto border border-border rounded-2xl bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Symbol</th>
              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Company</th>
              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Sector</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Price</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Return %</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">RSI 14</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">MACD</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">SMA 20</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">SMA 50</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Vol Ratio</th>
            </tr>
          </thead>
          <tbody>
            {paginatedTickers.length > 0 ? (
              paginatedTickers.map((ticker, idx) => (
                <tr
                  key={ticker.symbol}
                  className={`border-b border-border-light hover:bg-surface-2 transition cursor-pointer ${
                    idx % 2 === 0 ? "bg-surface" : "bg-surface/50"
                  }`}
                >
                  <td colSpan={10}>
                    <Link href={`/dashboard?symbol=${ticker.symbol}`} className="block">
                      <div className="px-4 py-3 flex items-center gap-3">
                        <span className="font-bold text-primary w-20">{ticker.symbol}</span>
                        <span className="text-text-primary">{ticker.company_name || "—"}</span>
                        <span className="text-text-secondary text-xs ml-auto">{ticker.sector || "—"}</span>
                        <span className="font-mono text-text-primary w-20 text-right">
                          ${ticker.latest_close ? ticker.latest_close.toFixed(2) : "—"}
                        </span>
                        <span className={`font-mono font-semibold w-20 text-right ${
                          ticker.daily_return_pct === null
                            ? "text-text-secondary"
                            : ticker.daily_return_pct > 0
                              ? "text-bull"
                              : ticker.daily_return_pct < 0
                                ? "text-bear"
                                : "text-neutral"
                        }`}>
                          <div className="flex items-center justify-end gap-1">
                            {ticker.daily_return_pct !== null && (
                              ticker.daily_return_pct > 0 ? (
                                <TrendingUp className="w-4 h-4"/>
                              ) : ticker.daily_return_pct < 0 ? (
                                <TrendingDown className="w-4 h-4"/>
                              ) : null
                            )}
                            {ticker.daily_return_pct ? ticker.daily_return_pct.toFixed(2) : "—"}%
                          </div>
                        </span>
                        <span className="font-mono text-text-secondary w-16 text-right">
                          {ticker.rsi_14 ? ticker.rsi_14.toFixed(1) : "—"}
                        </span>
                        <span className="font-mono text-text-secondary w-20 text-right">
                          {ticker.macd ? ticker.macd.toFixed(4) : "—"}
                        </span>
                        <span className="font-mono text-text-secondary w-20 text-right">
                          ${ticker.sma_20 ? ticker.sma_20.toFixed(2) : "—"}
                        </span>
                        <span className="font-mono text-text-secondary w-20 text-right">
                          ${ticker.sma_50 ? ticker.sma_50.toFixed(2) : "—"}
                        </span>
                        <span className="font-mono text-text-secondary w-16 text-right">
                          {ticker.volume_ratio ? ticker.volume_ratio.toFixed(2) : "—"}x
                        </span>
                      </div>
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-text-secondary">
                  No tickers available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-secondary">
            Showing {startIdx + 1} to {Math.min(startIdx + ITEMS_PER_PAGE, tickers.length)} of {tickers.length} tickers
          </p>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-border hover:bg-surface-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-5 h-5"/>
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter(page => {
                  if (totalPages <= 7) return true;
                  if (page === 1 || page === totalPages) return true;
                  if (Math.abs(page - currentPage) <= 1) return true;
                  return false;
                })
                .map((page, idx, arr) => {
                  if (idx > 0 && arr[idx - 1] !== page - 1) {
                    return <span key={`dots-${page}`} className="px-2">...</span>;
                  }
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-10 h-10 rounded-lg font-semibold transition ${
                        currentPage === page
                          ? "bg-primary text-white"
                          : "border border-border hover:bg-surface-2"
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
            </div>

            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-border hover:bg-surface-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <ChevronRight className="w-5 h-5"/>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
