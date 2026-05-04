"use client";
export const dynamic = "force-dynamic";

import { useContext, useEffect, useState } from "react";
import { SymbolContext } from "./layout";
import KPICard from "@/components/dashboard/KPICard";
import PriceChart from "@/components/dashboard/PriceChart";
import SentimentDonut from "@/components/dashboard/SentimentDonut";
import TechIndicators from "@/components/dashboard/TechIndicators";
import AIExplanation from "@/components/dashboard/AIExplanation";
import SignalsTable from "@/components/dashboard/SignalsTable";
import { getPrediction, PredictionData, getSentiment } from "@/lib/api";
import { DollarSign, Activity, TrendingUp, BarChart2, AlertCircle } from "lucide-react";

export default function Dashboard() {
  const context = useContext(SymbolContext);

  if (!context) {
    return <div>Loading...</div>;
  }

  const { activeSymbol, setActiveSymbol } = context;
  const [inputValue, setInputValue] = useState(activeSymbol);
  const [data, setData] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setInputValue(activeSymbol);
  }, [activeSymbol]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [predictionResult, sentimentResult] = await Promise.all([
          getPrediction(activeSymbol),
          getSentiment(activeSymbol, 7),
        ]);

        setData({
          ...predictionResult,
          sentiment: sentimentResult.sentiment,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeSymbol]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveSymbol(inputValue.toUpperCase());
  };

  const directionColor = data
    ? data.direction === "UP"
      ? "text-accent-green"
      : data.direction === "DOWN"
        ? "text-accent-red"
        : "text-accent-amber"
    : "text-text-muted";

  const directionArrow = data
    ? data.direction === "UP"
      ? "↑"
      : data.direction === "DOWN"
        ? "↓"
        : "→"
    : "";

  const confidencePercent = data ? Math.round(data.confidence * 100) : 0;

  return (
    <div className="flex flex-col gap-6 py-8 pb-14">
      {/* Page heading with search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-text-primary tracking-tight">Dashboard</h1>
          <p className="text-sm text-text-muted mt-0.5">AI-powered S&P 500 intelligence · FinBERT + LSTM</p>
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Enter symbol (e.g., AAPL)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="px-4 py-2 border border-border rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-accent-red" />
          <span className="text-sm text-accent-red">{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mb-3"></div>
            <p className="text-text-muted text-sm">Loading {activeSymbol} data...</p>
          </div>
        </div>
      )}

      {/* KPI row */}
      {!loading && data && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              title="Current Price"
              value={`$${data.technical.close.toFixed(2)}`}
              subValue={`${data.raw_score > 0 ? "+" : ""}${data.raw_score.toFixed(2)}`}
              subLabel={`(${((data.raw_score / data.technical.close) * 100).toFixed(2)}%)`}
              subColor="text-accent-green"
              icon={DollarSign}
              iconColor="text-primary"
              delay={0.05}
            />
            <KPICard
              title="Sentiment Score"
              value={`${Math.round(((data.sentiment.composite + 1) / 2) * 100)} / 100`}
              subValue={data.sentiment.composite > 0.05 ? "Bullish" : data.sentiment.composite < -0.05 ? "Bearish" : "Neutral"}
              subLabel={confidencePercent > 70 ? "High confidence" : "Low confidence"}
              subColor={data.sentiment.composite > 0.05 ? "text-accent-green" : data.sentiment.composite < -0.05 ? "text-accent-red" : "text-accent-amber"}
              icon={Activity}
              iconColor={data.sentiment.composite > 0.05 ? "text-accent-green" : data.sentiment.composite < -0.05 ? "text-accent-red" : "text-accent-amber"}
              delay={0.12}
            />
            <KPICard
              title="AI Prediction"
              value={`${data.direction} ${directionArrow}`}
              subValue={`${confidencePercent}%`}
              subLabel="probability"
              subColor={directionColor}
              icon={TrendingUp}
              iconColor={directionColor}
              delay={0.19}
            />
            <KPICard
              title="Data Points"
              value={`${data.sentiment.news_count + data.sentiment.reddit_count + data.sentiment.twit_count}`}
              subValue="signals analyzed"
              subColor="text-text-muted"
              icon={BarChart2}
              iconColor="text-accent-amber"
              delay={0.26}
            />
          </div>

          {/* Main chart */}
          <PriceChart data={data} />

          {/* Signal analysis grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <SentimentDonut sentiment={data.sentiment} />
            <TechIndicators technical={data.technical} />
            <AIExplanation explanation={data.explanation} />
          </div>

          {/* Signals table */}
          <SignalsTable sentiment={data.sentiment} symbol={data.symbol} />
        </>
      )}
    </div>
  );
}