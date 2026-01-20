"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface TradeProposal {
  action: "BUY" | "SELL";
  ticker: string;
  consensus_summary: string;
  confidence: number;
}

interface ApprovalModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tradeProposal: TradeProposal | null;
  onApprove: () => void;
  onReject: () => void;
}

export function ApprovalModal({
  open,
  onOpenChange,
  tradeProposal,
  onApprove,
  onReject,
}: ApprovalModalProps) {
  if (!tradeProposal) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Trade Recommendation</DialogTitle>
          <DialogDescription>
             AI Agents have reached a consensus.
          </DialogDescription>
        </DialogHeader>
        <div className="p-4 border-l-4 border-yellow-500 bg-secondary/50 rounded-r-md">
          <h3 className="font-bold text-lg">
            AI Recommendation: <span className={tradeProposal.action === 'BUY' ? 'text-green-600' : 'text-red-600'}>{tradeProposal.action}</span> {tradeProposal.ticker}
          </h3>
          <p className="text-sm mt-2 text-muted-foreground">
            <span className="font-semibold text-foreground">Consensus Rationale:</span> {tradeProposal.consensus_summary}
          </p>
          <div className="mt-2 text-xs font-mono">
            Confidence Score: {(tradeProposal.confidence * 100).toFixed(1)}%
          </div>
          <div className="flex gap-2 mt-6 justify-end">
            <Button variant="destructive" onClick={onReject}>
              Reject
            </Button>
            <Button 
              variant="default" 
              className="bg-green-600 hover:bg-green-700 text-white"
              onClick={onApprove}
            >
              Approve & Execute Live
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
