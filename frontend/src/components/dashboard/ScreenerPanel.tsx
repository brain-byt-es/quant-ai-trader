"use client";

import { useUniverseStore } from "@/store/useUniverseStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  BarChart3, 
  Database
} from "lucide-react";

export function ScreenerPanel() {
  const { universeCounts, rankedCandidates } = useUniverseStore();

  return (
    <Card className="h-full flex flex-col border-none shadow-none bg-background text-xs font-mono rounded-none">
      <CardHeader className="bg-card/50 py-2 border-b border-border">
        <CardTitle className="flex items-center justify-between text-muted-foreground text-[10px] uppercase tracking-widest font-bold">
          <span>Market Screener</span>
          <div className="flex items-center gap-2">
            <Database className="h-3 w-3 text-blue-500" />
            <span className="text-[10px] uppercase">Ready</span>
          </div>
        </CardTitle>
        
        <div className="grid grid-cols-3 gap-2 mt-2">
          <div className="flex flex-col bg-muted/30 p-1.5 rounded border border-border">
            <span className="text-[8px] text-muted-foreground uppercase">Base</span>
            <span className="text-sm font-bold">{universeCounts.base}</span>
          </div>
          <div className="flex flex-col bg-muted/30 p-1.5 rounded border border-border">
            <span className="text-[8px] text-muted-foreground uppercase">Eligible</span>
            <span className="text-sm font-bold text-emerald-500">{universeCounts.eligible}</span>
          </div>
          <div className="flex flex-col bg-muted/30 p-1.5 rounded border border-border">
            <span className="text-[8px] text-muted-foreground uppercase">Selected</span>
            <span className="text-sm font-bold text-blue-500">{universeCounts.selected}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-hidden bg-background">
        <div className="bg-muted/20 px-3 py-1.5 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-3 w-3 text-muted-foreground" />
            <span className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">Ranked Candidates (Top K)</span>
          </div>
          <Badge variant="outline" className="text-[8px] h-4 uppercase">Multi-Factor</Badge>
        </div>

        <ScrollArea className="h-full">
          <div className="p-0">
            <table className="w-full text-left border-collapse">
              <thead className="bg-muted/30 sticky top-0 z-10">
                <tr className="border-b border-border">
                  <th className="px-3 py-2 text-[8px] uppercase text-muted-foreground">Symbol</th>
                  <th className="px-3 py-2 text-[8px] uppercase text-muted-foreground text-right">Score</th>
                  <th className="px-3 py-2 text-[8px] uppercase text-muted-foreground text-right">Momentum</th>
                </tr>
              </thead>
              <tbody>
                {rankedCandidates.map((candidate) => (
                  <tr key={candidate.symbol} className="border-b border-border/40 hover:bg-muted/20 transition-colors">
                    <td className="px-3 py-2 font-bold text-blue-600 dark:text-blue-400">{candidate.symbol}</td>
                    <td className="px-3 py-2 text-right font-bold">{candidate.score.toFixed(2)}</td>
                    <td className="px-3 py-2 text-right text-muted-foreground">
                      {(candidate.factors.momentum_12_1 * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
                {rankedCandidates.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-12 text-center text-muted-foreground italic">
                      No screening data available...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
