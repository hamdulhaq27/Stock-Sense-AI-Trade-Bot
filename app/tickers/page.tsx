import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import TickersTable from "@/components/TickersTable";
import { motion } from "framer-motion";

export const metadata = {
  title: "List of Tickers | StockSense AI",
  description: "Browse all S&P 500 tickers with real-time price data, technical indicators, and market statistics.",
};

export default function TickersPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-32 pb-20 bg-background">
        <div className="max-w-7xl mx-auto px-6 xl:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="inline-block text-[11px] font-bold uppercase tracking-[0.16em] text-primary bg-primary/8 border border-primary/20 px-4 py-2 rounded-full mb-5">
              Market Data
            </span>
            <h1 className="text-4xl sm:text-5xl font-black text-text-primary tracking-tight mb-5 leading-tight">
              S&P 500 Tickers
            </h1>
            <p className="text-[17px] text-text-secondary font-light leading-relaxed">
              Real-time price data, technical indicators, and market statistics for all tracked tickers.
            </p>
          </div>

          {/* Table */}
          <div>
            <TickersTable />
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
