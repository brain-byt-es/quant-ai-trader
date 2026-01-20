"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface FactorData {
  factor: string;
  A: number; // Fund
  B: number; // Benchmark (e.g., SPY)
  fullMark: number;
}

const BENCHMARK_DATA: Record<string, number> = {
  "Value": 110,
  "Quality": 130,
  "Momentum": 130,
  "Growth": 100,
  "Risk": 90,
};

export function FactorRadar({ ticker }: { ticker: string }) {
  const { data: factors, isLoading } = useQuery({
    queryKey: ['factors', ticker],
    queryFn: () => api.getFactorAnalysis(ticker),
    refetchInterval: 10000, // Refresh every 10s
  });

  const chartData: FactorData[] = [
    { factor: "Value", A: factors?.value_score ?? 100, B: BENCHMARK_DATA["Value"], fullMark: 150 },
    { factor: "Quality", A: factors?.quality_score ?? 100, B: BENCHMARK_DATA["Quality"], fullMark: 150 },
    { factor: "Momentum", A: factors?.momentum_score ?? 100, B: BENCHMARK_DATA["Momentum"], fullMark: 150 },
    { factor: "Growth", A: factors?.growth_score ?? 100, B: BENCHMARK_DATA["Growth"], fullMark: 150 },
    { factor: "Risk", A: factors?.risk_score ?? 100, B: BENCHMARK_DATA["Risk"], fullMark: 150 },
  ];

  return (
    <Card className="h-[400px] flex flex-col shadow-md">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-bold flex justify-between items-center">
          <span>Factor Radar: {ticker}</span>
          {isLoading && <span className="text-[10px] animate-pulse">Calculating...</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="factor" tick={{ fill: '#888888', fontSize: 10 }} />
            <PolarRadiusAxis angle={30} domain={[0, 150]} tick={false} axisLine={false} />
            <Radar
              name={`$${ticker}`}
              dataKey="A"
              stroke="#8b5cf6"
              strokeWidth={2}
              fill="#8b5cf6"
              fillOpacity={0.5}
            />
            <Radar
              name="S&P 500"
              dataKey="B"
              stroke="#94a3b8"
              strokeWidth={2}
              fill="#94a3b8"
              fillOpacity={0.2}
            />
            <Tooltip 
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}