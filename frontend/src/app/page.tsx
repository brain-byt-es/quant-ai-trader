"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useUniverseStore } from "@/store/useUniverseStore";
import { StrategyCard } from "@/components/dashboard/StrategyCard";
import { LiveDebateFloor } from "@/components/dashboard/LiveDebateFloor";
import { PortfolioTable } from "@/components/dashboard/PortfolioTable";
import { Button } from "@/components/ui/button";
import { 
  Wifi, 
  ShieldAlert, 
  ChevronUp, 
  ChevronDown, 
  Activity, 
  LayoutGrid,
  Zap,
  Bot,
  User,
  Search
} from "lucide-react";
import { Toaster, toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import { ModeToggle } from "@/components/theme/theme-toggle";
import { useTheme } from "next-themes";
import { ScreenerPanel } from "@/components/dashboard/ScreenerPanel";

const DEFAULT_TICKERS = [
  "NVDA", "AAPL", "MSFT", "TSLA", "AMD", 
  "GOOGL", "META", "AMZN", "NFLX", "PLTR",
  "COIN", "MARA", "MSTR", "SQ", "PYPL",
  "AVGO", "SMCI", "ARM", "ASML", "ORCL"
];

export default function ExecutionTerminal() {
  const { 
    tickers, 
    netEquity, 
    buyingPower, 
    activePositions, 
    updateTicker, 
    setGlobalMetrics, 
    isAutoMode, 
    setIsAutoMode
  } = useUniverseStore();
  const [isPortfolioOpen, setIsPortfolioOpen] = useState(true);
  const { theme } = useTheme();
  
  // State for active scan
  const [scanConfig, setScanConfig] = useState<{ market?: string; k?: number }>({});
  const [isScanning, setIsScanning] = useState(false);
  const [isLiquidating, setIsLiquidating] = useState(false);

  const handleScanMarket = async () => {
    setIsScanning(true);
    toast.info("MARKET SCAN INITIALIZED", {
      description: "Screening symbols for multi-factor mispricing...",
    });
    
    // Clear current tickers to show screener results
    useUniverseStore.setState({ tickers: {}, rankedCandidates: [] });
    
    // Trigger reconnection in LiveDebateFloor by updating scanConfig
    setScanConfig({ market: "US", k: 10 });
    
    // Scanning state is purely visual here, the actual work happens in the SSE stream
    setTimeout(() => setIsScanning(false), 2000);
  };

  // Initialize universe
  useEffect(() => {
    // 1. Initial Ticker State
    DEFAULT_TICKERS.forEach(ticker => {
      updateTicker(ticker, {
        ticker,
        price: 0,
        score: 50,
        signal: 'NEUTRAL',
        altmanZ: 3.0,
        targetWeight: 0,
        rsi: 50,
        factors: { value: 50, quality: 50, momentum: 50, growth: 50, risk: 50 }
      });
    });

    // 2. Fetch Real Portfolio Stats & Positions
    const fetchData = async () => {
      try {
        const [stats, positionsData] = await Promise.all([
          api.getPortfolioStats(),
          api.getPositions()
        ]);

        setGlobalMetrics({
          netEquity: stats.equity,
          buyingPower: stats.buying_power,
          activePositions: positionsData.positions.length
        });

        const mappedPositions = positionsData.positions.map((p) => ({
          symbol: p.ticker,
          qty: p.qty,
          targetQty: p.qty, 
          entryPrice: p.qty !== 0 ? p.cost_basis / p.qty : 0,
          currentPrice: p.qty !== 0 ? p.market_value / p.qty : 0,
          unrealizedPlPc: p.unrealized_plpc * 100,
          exitSignal: "N/A",
          riskStatus: 'SAFE' as const
        }));

        useUniverseStore.getState().setPositions(mappedPositions);

      } catch (error) {
        console.error("Failed to fetch portfolio data:", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); 

    return () => clearInterval(interval);
  }, [updateTicker, setGlobalMetrics]);

  const handleKillSwitch = async () => {
    if (confirm("🚨 WARNING: Are you sure you want to trigger MASS LIQUIDATION? All open orders will be cancelled and all positions will be closed immediately.")) {
      setIsLiquidating(true);
      try {
        const result = await api.triggerKillSwitch();
        toast.error("MASS LIQUIDATION SUCCESSFUL", {
          description: result.message,
          duration: 10000,
        });
        // Clear local state
        useUniverseStore.getState().setPositions([]);
      } catch (error: any) {
        toast.error("KILL SWITCH FAILED", {
          description: error.message || "An unexpected error occurred during liquidation.",
        });
      } finally {
        setIsLiquidating(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground overflow-hidden font-sans">
      <div className="bg-primary text-primary-foreground text-[10px] py-0.5 px-4 text-center font-bold tracking-widest uppercase shrink-0">
        QuantTrader Framework v2.0.1 (Institutional Build) | {isAutoMode ? "Autonomous Mode" : "Manual Gate"} | Connection: Active
      </div>
      
      <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-card shrink-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500 fill-yellow-500" />
            <h1 className="text-sm font-black uppercase tracking-tighter">QuantTrader <span className="text-muted-foreground font-medium">v2.0</span></h1>
          </div>
          
          <div className="hidden lg:flex items-center gap-4 border-l border-border pl-6 h-8">
            <div className="flex flex-col">
              <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-widest leading-none">Net Equity</span>
              <span className="text-sm font-mono font-bold leading-none mt-1">${netEquity.toLocaleString()}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-widest leading-none">Buying Power</span>
              <span className="text-sm font-mono font-bold leading-none mt-1 text-emerald-600 dark:text-emerald-500">${buyingPower.toLocaleString()}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-widest leading-none">Positions</span>
              <span className="text-sm font-mono font-bold leading-none mt-1 text-blue-600 dark:text-blue-400">{activePositions}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-muted/50 rounded-md border border-border h-9">
            <Bot className={cn("h-4 w-4 transition-colors", isAutoMode ? "text-emerald-500" : "text-muted-foreground")} />
            <Switch 
              id="bot-mode" 
              checked={isAutoMode} 
              onCheckedChange={setIsAutoMode}
              className="data-[state=checked]:bg-emerald-500 scale-75"
            />
            <User className={cn("h-4 w-4 transition-colors", !isAutoMode ? "text-blue-500" : "text-muted-foreground")} />
            <span className="text-[10px] font-black uppercase tracking-widest ml-1 min-w-[70px] text-muted-foreground">
              {isAutoMode ? "AUTO-BOT" : "MANUAL"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-muted rounded border border-border h-9">
              <Wifi className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-[10px] font-mono font-bold text-muted-foreground">12MS</span>
            </div>
            
            <ModeToggle />

            <Button 
              variant="destructive" 
              size="sm" 
              onClick={handleKillSwitch}
              disabled={isLiquidating}
              className={cn(
                "h-9 bg-destructive hover:bg-destructive/90 text-[10px] font-black uppercase tracking-widest gap-2 px-4 shadow-sm border-none transition-all",
                isLiquidating && "animate-pulse opacity-70 cursor-not-allowed"
              )}
            >
              <ShieldAlert className="h-4 w-4" />
              <span className="hidden md:inline">{isLiquidating ? "LIQUIDATING..." : "Kill Switch"}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <section className="w-[70%] flex flex-col h-full overflow-hidden border-r border-border">
          <div className="flex items-center justify-between p-4 border-b border-border bg-card/50 shrink-0">
            <div className="flex items-center gap-2">
              <LayoutGrid className="h-4 w-4 text-blue-500" />
              <h2 className="text-xs font-black uppercase tracking-widest">Active Universe</h2>
              <Badge variant="outline" className="text-[9px] h-4 bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400">
                {Object.keys(tickers).length} TICKERS
              </Badge>
            </div>
            
            <div className="flex items-center gap-4">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleScanMarket}
                disabled={isScanning}
                className="h-7 text-[9px] font-black uppercase tracking-widest gap-2 bg-blue-600/10 border-blue-500/30 text-blue-500 hover:bg-blue-600 hover:text-white transition-all"
              >
                <Search className="h-3 w-3" />
                {isScanning ? "Scanning..." : "Scan Market"}
              </Button>

              <div className="h-4 w-px bg-border" />

              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Bullish</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Bearish</span>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 scrollbar-hide bg-muted/20">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {Object.values(tickers).map((tickerData) => (
                <StrategyCard key={tickerData.ticker} data={tickerData} />
              ))}
              {Object.keys(tickers).length === 0 && (
                <div className="col-span-full h-64 flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed border-border rounded-xl">
                  <Search className="h-8 w-8 mb-2 opacity-20" />
                  <p className="text-xs font-bold uppercase tracking-widest opacity-50">Universe Empty</p>
                  <p className="text-[10px] opacity-40">Run market scan to discover candidates</p>
                </div>
              )}
            </div>
          </div>

          <footer className={cn(
            "border-t border-border bg-card transition-all duration-300 ease-in-out shrink-0",
            isPortfolioOpen ? "h-[300px]" : "h-10"
          )}>
            <div 
              className="h-10 flex items-center justify-between px-4 cursor-pointer hover:bg-muted/50 transition-colors border-b border-border"
              onClick={() => setIsPortfolioOpen(!isPortfolioOpen)}
            >
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-[10px] font-black uppercase tracking-widest">Live Portfolio Positions</span>
              </div>
              {isPortfolioOpen ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronUp className="h-4 w-4 text-muted-foreground" />}
            </div>
            {isPortfolioOpen && <PortfolioTable />}
          </footer>
        </section>

        <aside className="w-[30%] h-full shrink-0 border-l border-border flex flex-col">
          <div className="flex-1 overflow-hidden">
            <ScreenerPanel />
          </div>
          <div className="h-1/2 border-t border-border overflow-hidden">
            <LiveDebateFloor 
              ticker="GLOBAL" 
              market={scanConfig.market} 
              k={scanConfig.k} 
            />
          </div>
        </aside>
      </main>

      <Toaster theme={theme as "light" | "dark" | "system"} position="top-right" />
    </div>
  );
}