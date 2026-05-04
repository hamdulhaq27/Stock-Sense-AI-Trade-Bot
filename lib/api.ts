const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Technical {
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  sma_20: number;
  sma_50: number;
  close: number;
  bb_pct: number;
  volume_ratio: number;
  rsi_signal: string;
  macd_cross: string;
  trend_signal: string;
}

export interface Headline {
  headline: string;  // backend returns 'headline', not 'title'
  source: string;
  date: string;
  sentiment: number; // backend returns -1 | 0 | 1 as integer, not a string
  score: number;     // FinBERT confidence 0..1
}

export interface Sentiment {
  news_score: number;
  news_count: number;
  reddit_score: number;
  reddit_count: number;
  twit_score: number;
  twit_count: number;
  composite: number;
  top_headlines: Headline[];
}

export interface PredictionData {
  symbol: string;
  direction: string;
  confidence: number;
  raw_score: number;
  as_of_date: string;
  explanation: string;
  technical: Technical;
  sentiment: Sentiment;
}

export async function getPrediction(symbol: string): Promise<PredictionData> {
  const response = await fetch(`${API_URL}/predict/${symbol.toUpperCase()}`, {
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch prediction for ${symbol}`);
  }

  return response.json();
}

export async function getSentiment(
  symbol: string,
  windowDays: number = 7
): Promise<{ symbol: string; as_of_date: string; sentiment: Sentiment }> {
  const response = await fetch(
    `${API_URL}/sentiment/${symbol.toUpperCase()}?window_days=${windowDays}`,
    {
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch sentiment for ${symbol}`);
  }

  return response.json();
}

export interface HistoryPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi_14: number;
  macd: number;
  sma_20: number;
  sma_50: number;
  daily_return_pct: number;
}

export interface HistoryData {
  symbol: string;
  period_days: number;
  data: HistoryPoint[];
}

export async function getHistory(
  symbol: string,
  days: number = 30
): Promise<HistoryData> {
  const response = await fetch(
    `${API_URL}/stocks/${symbol.toUpperCase()}/history?days=${days}`,
    {
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch history for ${symbol}`);
  }

  return response.json();
}