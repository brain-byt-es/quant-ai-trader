"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { TickerState } from "@/store/useUniverseStore";
import { cn } from "@/lib/utils";

export function StrategyCard({ data }: { data: TickerState }) {
  const chartData = [
    { factor: "V", value: data.factors.value },
    { factor: "Q", value: data.factors.quality },
    { factor: "M", value: data.factors.momentum },
    { factor: "G", value: data.factors.growth },
    { factor: "R", value: data.factors.risk },
  ];

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "BULLISH": return "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)]";
      case "BEARISH": return "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.6)]";
      default: return "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.6)]";
    }
  };

  const getPriceColor = (signal: string) => {
    switch (signal) {
      case "BULLISH": return "text-emerald-600 dark:text-emerald-500";
      case "BEARISH": return "text-rose-600 dark:text-rose-500";
      default: return "text-muted-foreground";
    }
  };

  return (
    <Card className="bg-card border-border hover:border-accent transition-colors group overflow-hidden relative">
      {/* Institutional Risk Overlays */}
      {data.altmanZ < 1.8 && data.altmanZ !== 0 ? (
        <div className="absolute inset-0 bg-destructive/10 backdrop-blur-[1px] z-10 flex flex-col items-center justify-center border border-destructive/50 pointer-events-none">
          <span className="bg-destructive text-destructive-foreground text-[10px] font-black px-2 py-0.5 rounded shadow-lg transform -rotate-12 uppercase tracking-tighter mb-1">
            Distress Veto
          </span>
          <span className="text-[8px] text-destructive font-bold uppercase">Z-Score: {data.altmanZ.toFixed(2)}</span>
        </div>
      ) : data.targetWeight > 0.19 ? (
        <div className="absolute top-2 right-2 z-10">
          <Badge className="bg-amber-500/20 text-amber-600 dark:text-amber-500 border-amber-500/30 text-[8px] font-black uppercase">
            Capped @ 20%
          </Badge>
        </div>
      ) : null}

      <CardHeader className="p-3 pb-0 space-y-0">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <CardTitle className="text-lg font-black font-mono tracking-tighter text-foreground flex items-center gap-2">
              {data.ticker}
              <div className={cn("h-2 w-2 rounded-full", getSignalColor(data.signal))} />
              <span className="text-[9px] text-muted-foreground font-bold ml-auto bg-muted px-1 rounded border border-border">
                3 ALPHAS
              </span>
            </CardTitle>
            <div className={cn("text-xl font-bold font-mono tracking-tight", getPriceColor(data.signal))}>
              ${data.price.toFixed(2)}
            </div>
          </div>
          
          <div className="h-[60px] w-[60px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                <PolarGrid stroke="var(--border)" opacity={0.5} />
                <PolarAngleAxis dataKey="factor" tick={false} />
                <Radar
                  dataKey="value"
                  stroke={data.signal === 'BULLISH' ? "#10b981" : data.signal === 'BEARISH' ? "#f43f5e" : "#f59e0b"}
                  fill={data.signal === 'BULLISH' ? "#10b981" : data.signal === 'BEARISH' ? "#f43f5e" : "#f59e0b"}
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-3 space-y-3">
        <div className="grid grid-cols-3 gap-2 py-2 border-y border-border/50">
          <div className="flex flex-col items-center">
            <span className="text-[9px] text-muted-foreground uppercase font-black tracking-widest">Altman Z</span>
            <span className={cn("text-xs font-mono font-bold", data.altmanZ < 1.8 ? "text-destructive" : "text-foreground/80")}>
              {data.altmanZ.toFixed(2)}
            </span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[9px] text-muted-foreground uppercase font-black tracking-widest">RSI</span>
            <span className={cn("text-xs font-mono font-bold", data.rsi > 70 ? "text-rose-500" : data.rsi < 30 ? "text-emerald-500" : "text-foreground/80")}>
              {data.rsi.toFixed(0)}
            </span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[9px] text-muted-foreground uppercase font-black tracking-widest">MVO %</span>
            <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">{(data.targetWeight * 100).toFixed(1)}%</span>
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 h-7 bg-transparent border-border hover:bg-muted hover:text-foreground text-[10px] font-black uppercase tracking-wider">
            Halt
          </Button>
          <Button size="sm" className={cn("flex-1 h-7 text-[10px] font-black uppercase tracking-wider border-none", 
            data.signal === 'BULLISH' ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm" : 
            data.signal === 'BEARISH' ? "bg-rose-600 hover:bg-rose-700 text-white shadow-sm" : "bg-muted hover:bg-muted/80 text-foreground")}>
            Trade
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}