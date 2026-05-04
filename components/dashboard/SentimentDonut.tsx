import { Sentiment } from "@/lib/api";

interface SentimentDonutProps {
  sentiment: Sentiment;
}

export default function SentimentDonut({ sentiment }: SentimentDonutProps) {
  const C = 238.76; // SVG circle circumference (2π × r where r=38)

  /**
   * Backend returns composite in (-1, +1).
   * Convert to a 0..100 bullish percentage:
   *   composite = +1.0  →  bullish = 100%, bearish = 0%
   *   composite =  0.0  →  bullish = 50%,  bearish = 25%, neutral = 25%
   *   composite = -1.0  →  bullish = 0%,   bearish = 100%
   *
   * We split the non-bullish remainder evenly between neutral and bearish
   * so the donut always sums to 100%.
   */
  const rawComposite = sentiment.composite ?? 0; // -1..+1
  const bullishPct = Math.round(((rawComposite + 1) / 2) * 100); // 0..100
  const remainder = 100 - bullishPct;
  // Skew neutral vs bearish based on which side of zero we're on:
  // When slightly negative, more neutral than bearish; when very negative, more bearish.
  const bearishPct = Math.round(remainder * (0.5 - rawComposite * 0.15));
  const neutralPct = remainder - bearishPct;

  const bullishArc = (bullishPct / 100) * C;
  const neutralArc = (neutralPct / 100) * C;
  const bearishArc = (bearishPct / 100) * C;

  const dominantSentiment =
    bullishPct > 55 ? "Bullish" : bearishPct > 45 ? "Bearish" : "Neutral";
  const dominantColor =
    dominantSentiment === "Bullish"
      ? "text-accent-green"
      : dominantSentiment === "Bearish"
      ? "text-accent-red"
      : "text-accent-amber";

  // Individual source scores are also -1..+1, convert for display
  const toDisplayPct = (score: number) =>
    Math.round(((score + 1) / 2) * 100);

  const newsDisplay = toDisplayPct(sentiment.news_score ?? 0);
  const redditDisplay = toDisplayPct(sentiment.reddit_score ?? 0);
  const twitDisplay = toDisplayPct(sentiment.twit_score ?? 0);

  return (
    <div className="bg-white border border-border rounded-xl shadow-sm p-5 flex flex-col h-full">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-bold text-text-primary">Sentiment Breakdown</h3>
        <span className="text-xs text-text-muted font-mono bg-surface-2 px-2 py-1 rounded">
          composite {rawComposite >= 0 ? "+" : ""}{rawComposite.toFixed(3)}
        </span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center gap-5">
        {/* Donut chart */}
        <div className="relative w-40 h-40">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            {/* Track */}
            <circle cx="50" cy="50" r="38" fill="none" stroke="#F4F1EC" strokeWidth="14" />

            {/* Bearish segment (drawn first, at offset 0) */}
            <circle
              cx="50" cy="50" r="38" fill="none"
              stroke="#E53E3E" strokeWidth="14"
              strokeDasharray={`${bearishArc} ${C - bearishArc}`}
              strokeDashoffset="0"
              strokeLinecap="butt"
            />

            {/* Neutral segment */}
            <circle
              cx="50" cy="50" r="38" fill="none"
              stroke="#D97706" strokeWidth="14"
              strokeDasharray={`${neutralArc} ${C - neutralArc}`}
              strokeDashoffset={`-${bearishArc}`}
              strokeLinecap="butt"
            />

            {/* Bullish segment */}
            <circle
              cx="50" cy="50" r="38" fill="none"
              stroke="#16A34A" strokeWidth="14"
              strokeDasharray={`${bullishArc} ${C - bullishArc}`}
              strokeDashoffset={`-${bearishArc + neutralArc}`}
              strokeLinecap="butt"
            />
          </svg>

          {/* Centre label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold text-text-primary font-mono leading-none">
              {bullishPct}%
            </span>
            <span className={`text-[10px] font-bold uppercase tracking-wider mt-0.5 ${dominantColor}`}>
              {dominantSentiment}
            </span>
          </div>
        </div>

        {/* Pct pills */}
        <div className="w-full grid grid-cols-3 gap-2 text-center">
          {[
            { label: "Bullish",  pct: bullishPct,  color: "bg-accent-green", text: "text-accent-green" },
            { label: "Neutral",  pct: neutralPct,  color: "bg-accent-amber", text: "text-accent-amber" },
            { label: "Bearish",  pct: bearishPct,  color: "bg-accent-red",   text: "text-accent-red"   },
          ].map((s) => (
            <div key={s.label} className="flex flex-col items-center gap-1.5 p-2 rounded-lg bg-surface-2">
              <div className={`w-2.5 h-2.5 rounded-full ${s.color}`} />
              <span className="text-[10px] text-text-muted font-medium">{s.label}</span>
              <span className={`text-sm font-extrabold font-mono ${s.text}`}>{s.pct}%</span>
            </div>
          ))}
        </div>

        {/* Per-source breakdown */}
        <div className="w-full space-y-2 pt-1 border-t border-border-light">
          {[
            { label: "News",       pct: newsDisplay,   count: sentiment.news_count,   raw: sentiment.news_score },
            { label: "Reddit",     pct: redditDisplay, count: sentiment.reddit_count, raw: sentiment.reddit_score },
            { label: "StockTwits", pct: twitDisplay,   count: sentiment.twit_count,   raw: sentiment.twit_score },
          ].map((src) => (
            <div key={src.label} className="flex items-center gap-2">
              <span className="text-[10px] text-text-muted w-20 shrink-0">{src.label}</span>
              <div className="flex-1 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    src.raw > 0.05 ? "bg-accent-green" : src.raw < -0.05 ? "bg-accent-red" : "bg-accent-amber"
                  }`}
                  style={{ width: `${src.pct}%` }}
                />
              </div>
              <span className="text-[10px] font-mono text-text-muted w-8 text-right">
                {src.raw >= 0 ? "+" : ""}{src.raw.toFixed(2)}
              </span>
              <span className="text-[10px] text-text-muted w-10 text-right">{src.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}