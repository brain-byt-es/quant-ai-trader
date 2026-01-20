import { create } from 'zustand';

export interface InsightEntry {
  symbol: string;
  agentId: string;
  direction: 'UP' | 'DOWN' | 'FLAT';
  confidence: number;
  magnitude: number;
  timestamp: string;
}

export interface TickerState {
  ticker: string;
  price: number;
  score: number;
  signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  rsi: number;
  altmanZ: number; // Institutional distress gate
  targetWeight: number; // MVO Target %
  factors: {
    value: number;
    quality: number;
    momentum: number;
    growth: number;
    risk: number;
  };
}

export interface Position {
  symbol: string;
  qty: number;
  targetQty: number; // LEAN target state
  entryPrice: number;
  currentPrice: number;
  unrealizedPlPc: number;
  exitSignal: string;
  riskStatus: 'SAFE' | 'DISTRESS' | 'LIQUIDATE';
}

interface UniverseState {
  tickers: Record<string, TickerState>;
  positions: Position[];
  insights: InsightEntry[];
  buyingPower: number;
  netEquity: number;
  activePositions: number;
  isAutoMode: boolean;
  universeCounts: {
    base: number;
    eligible: number;
    selected: number;
  };
  rankedCandidates: Array<{
    symbol: string;
    score: number;
    factors: Record<string, number>;
  }>;
  
  updateTicker: (ticker: string, updates: Partial<TickerState>) => void;
  addInsight: (insight: InsightEntry) => void;
  setPositions: (positions: Position[]) => void;
  setGlobalMetrics: (metrics: { buyingPower: number; netEquity: number; activePositions: number }) => void;
  setIsAutoMode: (isAutoMode: boolean) => void;
  setScreenerResults: (counts: { base: number; eligible: number; selected: number }, candidates: Array<{ symbol: string; score: number; factors: Record<string, number> }>) => void;
}

export const useUniverseStore = create<UniverseState>((set) => ({
  tickers: {},
  positions: [],
  insights: [],
  buyingPower: 0,
  netEquity: 0,
  activePositions: 0,
  isAutoMode: false,
  universeCounts: { base: 0, eligible: 0, selected: 0 },
  rankedCandidates: [],

  updateTicker: (ticker, updates) => set((state) => ({
    tickers: {
      ...state.tickers,
      [ticker]: {
        ...(state.tickers[ticker] || {
          ticker,
          price: 0,
          score: 50,
          signal: 'NEUTRAL',
          rsi: 50,
          altmanZ: 3.0,
          targetWeight: 0,
          factors: { value: 50, quality: 50, momentum: 50, growth: 50, risk: 50 }
        }),
        ...updates
      }
    }
  })),

  addInsight: (insight) => set((state) => ({
    insights: [insight, ...state.insights].slice(0, 100)
  })),

  setPositions: (positions) => set({ 
    positions,
    activePositions: positions.length 
  }),

  setGlobalMetrics: (metrics) => set({
    buyingPower: metrics.buyingPower,
    netEquity: metrics.netEquity,
    activePositions: metrics.activePositions
  }),

  setIsAutoMode: (isAutoMode) => set({ isAutoMode }),

  setScreenerResults: (counts, candidates) => set({
    universeCounts: counts,
    rankedCandidates: candidates
  }),
}));