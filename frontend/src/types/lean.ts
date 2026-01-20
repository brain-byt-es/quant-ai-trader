import { z } from "zod";

/**
 * Single source of truth for the LEAN-faithful pipeline data.
 */

export const InsightDirectionSchema = z.union([
  z.literal(1),
  z.literal(0),
  z.literal(-1)
]);

export const InsightSchema = z.object({
  symbol: z.string(),
  time: z.string().datetime().optional(),
  periodSec: z.number().positive(),
  direction: InsightDirectionSchema,
  magnitude: z.number().finite(),
  confidence: z.number().min(0).max(1),
  source_model: z.string(),
  tag: z.string().optional()
});

export const TargetSchema = z.object({
  symbol: z.string(),
  targetQty: z.number(),
  targetWeight: z.number().min(-1).max(1),
  tag: z.string().optional()
});

export const RiskSchema = z.object({
  symbol: z.string(),
  altmanZ: z.number(),
  vetoed: z.boolean(),
  capApplied: z.boolean(),
  capMaxWeight: z.number().optional()
});

export const ExecutionSchema = z.object({
  symbol: z.string(),
  currentQty: z.number(),
  targetQty: z.number(),
  deltaQty: z.number(),
  intent: z.enum(["BUY", "SELL", "HOLD", "COVER", "SHORT"])
});

export const SSEEventSchema = z.object({
  schema_version: z.literal("1.0"),
  agent: z.string(),
  ticker: z.string().optional(),
  content: z.string().optional(),
  signal: z.string().optional(),
  score: z.number().optional(),
  confidence: z.number().optional(),
  magnitude: z.number().optional(),
  timestamp: z.string(),
  // LEAN Payload extensions
  insight: InsightSchema.optional(),
  target: TargetSchema.optional(),
  risk: RiskSchema.optional(),
  execution: ExecutionSchema.optional()
});

export type InsightDTO = z.infer<typeof InsightSchema>;
export type TargetDTO = z.infer<typeof TargetSchema>;
export type RiskDTO = z.infer<typeof RiskSchema>;
export type ExecutionDTO = z.infer<typeof ExecutionSchema>;
export type SSEEvent = z.infer<typeof SSEEventSchema>;
