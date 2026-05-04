"use client";
export const dynamic = "force-dynamic";
import { createContext, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import TopBar from "@/components/dashboard/TopBar";

export const SymbolContext = createContext({
  activeSymbol: "AAPL",
  setActiveSymbol: (symbol: string) => {},
});

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();
  const [activeSymbol, setActiveSymbol] = useState("AAPL");

  useEffect(() => {
    const symbol = searchParams.get("symbol");
    if (symbol) setActiveSymbol(symbol);
  }, [searchParams]);

  return (
    <SymbolContext.Provider value={{ activeSymbol, setActiveSymbol }}>
      <TopBar 
        activeSymbol={activeSymbol} 
        onSymbolChange={setActiveSymbol} 
      />
      {children}
    </SymbolContext.Provider>
  );
}
