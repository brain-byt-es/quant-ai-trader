"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUniverseStore } from "@/store/useUniverseStore";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { SSEEventSchema } from "@/types/lean";

interface AgentLogEntry {
  id: string;
  timestamp: string;
  ticker: string;
  agentId: string;
  badge: string;
  signal: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence: number;
  magnitude: number;
  rationale: string;
}

const AGENTS = {
  System: { badge: "SYSTEM | CORE" },
  Buffett: { badge: "ALPHA | VALUE" },
  Wood: { badge: "ALPHA | GROWTH" },
  Munger: { badge: "ALPHA | QUALITY" },
  Fisher: { badge: "ALPHA | GROWTH" },
  Ackman: { badge: "ALPHA | ACTIVIST" },
  Burry: { badge: "ALPHA | CONTRARIAN" },
  Graham: { badge: "ALPHA | VALUE" },
  Lynch: { badge: "ALPHA | GARP" },
  Druckenmiller: { badge: "ALPHA | MACRO" },
  Damodaran: { badge: "ALPHA | VALUATION" },
  Pabrai: { badge: "ALPHA | CLONER" },
  Jhunjhunwala: { badge: "ALPHA | MOMENTUM" },
  PortfolioManager: { badge: "PCM | MVO" },
  RiskManager: { badge: "RMM | GATE" },
  TechnicalAnalyst: { badge: "INDICATOR | SWEEP" },
  FundamentalAnalyst: { badge: "DATA | AUDIT" },
  SentimentAnalyst: { badge: "SOCIAL | AGG" },
};

interface LiveDebateFloorProps {
  ticker?: string;
  market?: string;
  k?: number;
}

export function LiveDebateFloor({ ticker = "GLOBAL", market, k }: LiveDebateFloorProps) {
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [schemaError, setSchemaError] = useState<string | null>(null);
  const updateTicker = useUniverseStore((state) => state.updateTicker);

  const streamUrl = useMemo(() => {
    const baseUrl = `/api/py/analysis/stream/${ticker}`;
    const params = new URLSearchParams();
    if (market) params.append("market", market);
    if (k) params.append("k", k.toString());
    
    const queryString = params.toString();
    return queryString ? `${baseUrl}?${queryString}` : baseUrl;
  }, [ticker, market, k]);

  useEffect(() => {
    console.log(`Establishing SSE Connection to ${streamUrl}...`);
    const eventSource = new EventSource(streamUrl, { withCredentials: true }); 

    eventSource.onopen = () => {
      console.log("SSE Connection Opened");
      setIsConnected(true);
      setSchemaError(null);
    };

    // --- Institutional Fix: Listen for NAMED events from the backend ---
    
    const handleMessage = (event: MessageEvent) => {
      if (event.data === "[DONE]") {
        setIsConnected(false);
        return;
      }

      try {
        const rawData = JSON.parse(event.data);
        const result = SSEEventSchema.safeParse(rawData);
        
        if (!result.success) return;

        const data = result.data;
        const logTicker = data.ticker || "SYSTEM";
        const agentName = data.agent || "UNKNOWN";

        if (data.score || data.signal) {
          updateTicker(logTicker, {
            signal: (data.signal || "NEUTRAL").toUpperCase() as "BULLISH" | "BEARISH" | "NEUTRAL",
            score: data.score || 50,
          });
        }

        const newLog: AgentLogEntry = {
          id: crypto.randomUUID(),
          timestamp: new Date().toLocaleTimeString('en-GB', { hour12: false }),
          ticker: logTicker,
          agentId: agentName,
          badge: AGENTS[agentName as keyof typeof AGENTS]?.badge || "ALPHA MODEL",
          signal: (data.signal || "NEUTRAL").toUpperCase() as "BULLISH" | "BEARISH" | "NEUTRAL",
          confidence: data.confidence || 0,
          magnitude: data.magnitude || 0,
          rationale: data.content || "Processing...",
        };
        
        setLogs((prev) => {
          const isDuplicate = prev.some(l => l.agentId === newLog.agentId && l.rationale === newLog.rationale && l.ticker === newLog.ticker);
          if (isDuplicate) return prev;
          return [...prev.slice(-199), newLog];
        });
      } catch {}
    };

    const handleUniverse = (event: MessageEvent) => {
      console.log("SSE Universe Event:", event.data);
      const data = JSON.parse(event.data);
      useUniverseStore.getState().setScreenerResults(
        { base: data.base_count, eligible: data.eligible_count, selected: data.selected_symbols.length },
        useUniverseStore.getState().rankedCandidates
      );
    };

    const handleRanking = (event: MessageEvent) => {
      console.log("SSE Ranking Event:", event.data);
      const data = JSON.parse(event.data);
      useUniverseStore.getState().setScreenerResults(
        useUniverseStore.getState().universeCounts,
        data.top_k
      );
    };

    // Add listeners for both generic and named events
    eventSource.addEventListener("message", handleMessage);
    eventSource.addEventListener("progress", handleMessage);
    eventSource.addEventListener("universe", handleUniverse);
    eventSource.addEventListener("ranking", handleRanking);

    eventSource.onerror = (err) => {
      console.error("SSE Connection Error:", err);
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      console.log("Closing SSE Connection");
      eventSource.removeEventListener("message", handleMessage);
      eventSource.removeEventListener("progress", handleMessage);
      eventSource.removeEventListener("universe", handleUniverse);
      eventSource.removeEventListener("ranking", handleRanking);
      eventSource.close();
    };
  }, [streamUrl, updateTicker]);


  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "BULLISH": return "text-emerald-500";
      case "BEARISH": return "text-rose-500";
      default: return "text-amber-500";
    }
  };

  return (
    <Card className="h-full flex flex-col border-none shadow-none bg-background text-xs font-mono rounded-none border-l border-border">
      <CardHeader className="bg-card/50 py-2 border-b border-border">
        <CardTitle className="flex items-center justify-between text-muted-foreground text-[10px] uppercase tracking-widest font-bold">
          <span>Framework Execution Audit</span>
          <div className="flex items-center gap-2">
            <span className={`h-1.5 w-1.5 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground/30"}`} />
            <span className="text-[10px] uppercase">{isConnected ? "Streaming" : "Offline"}</span>
          </div>
        </CardTitle>
        {schemaError && (
          <div className="bg-destructive/20 text-destructive text-[9px] px-2 py-1 mt-2 rounded border border-destructive/30 animate-pulse">
            CRITICAL: {schemaError}
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-hidden bg-background">
        <ScrollArea className="h-full">
          <div ref={scrollRef} className="p-2 space-y-1">
            {logs.map((log) => (
              <div key={log.id} className="flex flex-col border-b border-border/40 pb-1.5 mb-1 leading-relaxed">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-muted-foreground/60 text-[9px]">{log.timestamp}</span>
                  <span className="text-blue-600 dark:text-blue-400 font-bold tracking-tighter">{log.ticker.toUpperCase()}</span>
                  <span className="bg-muted px-1 rounded text-[9px] text-muted-foreground">{log.badge}</span>
                  <span className={cn("font-bold text-[10px]", getSignalColor(log.signal))}>{log.signal}</span>
                  {log.confidence > 0 && (
                    <span className="text-muted-foreground text-[9px]">C:{Math.round(log.confidence * 100)}%</span>
                  )}
                  {log.magnitude !== 0 && (
                    <span className="text-muted-foreground text-[9px]">M:{(log.magnitude * 100).toFixed(1)}%</span>
                  )}
                </div>
                <span className="text-foreground/80 text-[11px] font-sans pl-2 border-l border-border/60 ml-1 line-clamp-2">{log.rationale}</span>
              </div>
            ))}
            {logs.length === 0 && (
              <div className="text-muted-foreground italic p-4 text-center">Awaiting framework signals...</div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}