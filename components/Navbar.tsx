"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";

const NAV_LINKS = [
  { label: "Features",    href: "#features" },
  { label: "How It Works",href: "#how-it-works" },
  { label: "Signals",    href: "#signals" },
  { label: "List of Tickers", href: "/tickers" },
  { label: "Dashboard",  href: "/dashboard" },
];

export default function Navbar() {
  const [scrolled, setScrolled]     = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-400 ${
        scrolled
          ? "bg-white/90 backdrop-blur-xl border-b border-border shadow-sm shadow-black/[0.04]"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 xl:px-8 h-[72px] flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/30 group-hover:shadow-primary/50 transition-shadow">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" className="w-5 h-5">
              <path d="M3 13h4l3-10 4 20 3-10h4" />
            </svg>
          </div>
          <div className="flex flex-col leading-none">
            <span className="text-[17px] font-bold tracking-tight text-text-primary">StockSense <span className="text-primary">AI</span></span>
            <span className="text-[9px] font-semibold uppercase tracking-[0.18em] text-text-muted">S&P 500 Intelligence</span>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(l => (
            <Link key={l.label} href={l.href}
              className="px-4 py-2 text-[14px] font-medium text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-2 transition-all">
              {l.label}
            </Link>
          ))}
        </nav>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link href="/dashboard"
            className="px-5 py-2.5 bg-primary text-white text-[14px] font-semibold rounded-xl hover:bg-primary-dark transition-all shadow-lg shadow-primary/25 hover:-translate-y-px hover:shadow-primary/40">
            Try for Free →
          </Link>
        </div>

        {/* Mobile toggle */}
        <button onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-lg hover:bg-surface-2 transition-colors">
          {mobileOpen ? <X className="w-5 h-5"/> : <Menu className="w-5 h-5"/>}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-border px-6 py-4 flex flex-col gap-2">
          {NAV_LINKS.map(l => (
            <Link key={l.label} href={l.href} onClick={() => setMobileOpen(false)}
              className="py-3 text-[14px] font-medium text-text-secondary hover:text-primary border-b border-border-light last:border-0">
              {l.label}
            </Link>
          ))}
          <Link href="/dashboard" onClick={() => setMobileOpen(false)}
            className="mt-2 py-3 bg-primary text-white font-semibold rounded-xl text-center text-sm">
            Try for Free →
          </Link>
        </div>
      )}
    </header>
  );
}
