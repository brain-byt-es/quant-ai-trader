"use client";

import { useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter, SheetClose } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { executeTradeAction } from "@/app/actions";
import { toast } from "sonner";
import { Loader2, TrendingUp, TrendingDown, AlertTriangle, Calculator, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface TradeProposal {
  action: "BUY" | "SELL";
  ticker: string;
  price: number;
  bullCase: string[];
  bearCase: string[];
  confidence: number;
  // Execution Math
  altmanZScore: number;
  kellyCriterion: number;
  riskManagerCap: number;
  projectedVaR: number;
}

interface TradeCommandDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  proposal: TradeProposal | null;
}

export function TradeCommandDrawer({ open, onOpenChange, proposal }: TradeCommandDrawerProps) {
  const [isExecuting, setIsExecuting] = useState(false);

  const handleExecute = async () => {
    if (!proposal) return;
    
    setIsExecuting(true);
    try {
      // In a real flow, the proposal would contain a unique token from the backend
      const token = (proposal as TradeProposal & { token?: string }).token || "SIMULATED_TOKEN";
      const result = await executeTradeAction(token, proposal);
      
      if (result.success) {
        toast.success(result.message);
        onOpenChange(false);
      } else {
        toast.error(result.message);
      }
    } catch {
      toast.error("Network error during execution");
    } finally {
      setIsExecuting(false);
    }
  };

  if (!proposal) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[600px] w-full overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-2xl flex items-center gap-2">
            <AlertTriangle className="text-yellow-500 h-6 w-6" />
            Trade Command Center
          </SheetTitle>
          <SheetDescription>
            Review consensus and execute live market orders.
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6">
          {/* Header Summary */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border">
            <div>
              <h3 className="text-4xl font-bold tracking-tighter">{proposal.ticker}</h3>
              <p className="text-sm text-muted-foreground">Current Price: ${proposal.price.toFixed(2)}</p>
            </div>
            <div className="text-right">
              <Badge variant={proposal.action === "BUY" ? "default" : "destructive"} className="text-lg px-4 py-1 mb-1">
                {proposal.action}
              </Badge>
              <div className="text-sm font-mono text-muted-foreground">
                Conf: {(proposal.confidence * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Execution Math Section */}
          <Card className="border-blue-200 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-950/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2 text-blue-700 dark:text-blue-400">
                <Calculator className="h-4 w-4" />
                Execution Math
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex flex-col">
                  <span className="text-muted-foreground text-xs">Kelly Criterion Recommended</span>
                  <span className="font-mono font-medium">{proposal.kellyCriterion.toFixed(2)}%</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-muted-foreground text-xs">Risk Manager Cap</span>
                  <span className="font-mono font-medium text-amber-600">{proposal.riskManagerCap.toFixed(2)}%</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-muted-foreground text-xs">Altman Z-Score</span>
                  <span className={`font-mono font-medium ${proposal.altmanZScore > 1.8 ? 'text-green-600' : 'text-red-600'}`}>
                    {proposal.altmanZScore.toFixed(2)}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-muted-foreground text-xs">Projected VaR Impact</span>
                  <span className="font-mono font-medium">+{proposal.projectedVaR.toFixed(2)}%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Separator />

          {/* Side-by-Side Arguments */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-green-200 dark:border-green-900 bg-green-50/50 dark:bg-green-950/10">
              <CardContent className="pt-6">
                <h4 className="flex items-center gap-2 font-semibold text-green-700 dark:text-green-400 mb-3">
                  <TrendingUp className="h-4 w-4" />
                  Bull Case
                </h4>
                <ul className="list-disc pl-4 space-y-2 text-sm text-muted-foreground">
                  {proposal.bullCase.map((arg, i) => (
                    <li key={i}>{arg}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/10">
              <CardContent className="pt-6">
                <h4 className="flex items-center gap-2 font-semibold text-red-700 dark:text-red-400 mb-3">
                  <TrendingDown className="h-4 w-4" />
                  Bear Case
                </h4>
                <ul className="list-disc pl-4 space-y-2 text-sm text-muted-foreground">
                  {proposal.bearCase.map((arg, i) => (
                    <li key={i}>{arg}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Risk Warning */}
          <div className="p-4 rounded-md bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200 text-sm flex items-start gap-3">
             <ShieldCheck className="h-5 w-5 shrink-0 mt-0.5" />
             <div className="space-y-1">
                <span className="font-semibold block">Order Verification</span>
                <span className="block opacity-90">Executing this trade will commit capital. Ensure compliance with portfolio concentration limits.</span>
             </div>
          </div>
        </div>

        <SheetFooter className="mt-8 gap-2 sm:gap-0">
          <SheetClose asChild>
            <Button variant="outline" disabled={isExecuting}>Cancel</Button>
          </SheetClose>
          <Button 
            className="w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white" 
            onClick={handleExecute}
            disabled={isExecuting}
          >
            {isExecuting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Confirm & Execute Live"
            )}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
