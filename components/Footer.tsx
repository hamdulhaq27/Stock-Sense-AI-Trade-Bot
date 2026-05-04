import Link from "next/link";
import { ExternalLink, Globe, Share2 } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-text-primary text-white">
      {/* Top CTA band */}
      <div className="border-b border-white/10 py-16">
        <div className="max-w-7xl mx-auto px-6 md:px-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="max-w-xl">
            <h3 className="text-3xl font-extrabold tracking-tight mb-2">
              Ready to trade smarter?
            </h3>
            <p className="text-white/60 text-base font-light">
              Get instant access to AI-powered S&P 500 signals — no setup required.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="shrink-0 px-8 py-4 bg-primary rounded-xl font-bold text-white text-base shadow-lg shadow-primary/30 hover:bg-primary-light hover:-translate-y-0.5 transition-all"
          >
            Launch Dashboard →
          </Link>
        </div>
      </div>

      {/* Main Footer */}
      <div className="max-w-7xl mx-auto px-6 md:px-10 py-14">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {/* Brand */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                  <path d="M3 12h4l3-9 5 18 3-9h3" />
                </svg>
              </div>
              <div>
                <span className="font-bold text-lg leading-none">StockSense<span className="text-primary">AI</span></span>
                <div className="text-[10px] text-white/40 uppercase tracking-widest">S&P 500 Intelligence</div>
              </div>
            </div>
            <p className="text-white/50 text-sm leading-relaxed font-light">
              AI-powered stock analysis combining FinBERT NLP, LSTM forecasting, and multi-source sentiment aggregation for the US market.
            </p>
            <div className="flex items-center gap-3 mt-2">
              {[ExternalLink, Globe, Share2].map((Icon, i) => (
                <a key={i} href="#" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                  <Icon className="w-4 h-4 text-white/60" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          <div className="flex flex-col gap-3">
            <h4 className="text-sm font-bold uppercase tracking-widest text-white/40 mb-1">Platform</h4>
            {[
              { label: "Live Dashboard", href: "/dashboard" },
              { label: "Features", href: "#features" },
              { label: "How It Works", href: "#how-it-works" },
              { label: "Documentation", href: "#docs" },
            ].map((link) => (
              <Link key={link.label} href={link.href} className="text-sm text-white/60 hover:text-white transition-colors">
                {link.label}
              </Link>
            ))}
          </div>

          {/* Coverage */}
          <div className="flex flex-col gap-3">
            <h4 className="text-sm font-bold uppercase tracking-widest text-white/40 mb-1">Stock Coverage</h4>
            {["AAPL — Apple Inc.", "TSLA — Tesla Inc.", "AMZN — Amazon.com", "MSFT — Microsoft", "NVDA — NVIDIA"].map((s) => (
              <span key={s} className="text-sm text-white/60 font-mono">{s}</span>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-white/10 mt-12 pt-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-white/30">
          <span>&copy; {new Date().getFullYear()} StockSense AI. All rights reserved.</span>
          <span className="font-mono bg-white/5 px-3 py-1.5 rounded-lg">CS4063 NLP · Spring 2025 · S&P 500 Research Platform</span>
        </div>
      </div>
    </footer>
  );
}
