"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight, Activity, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

const INITIAL_DATA = [
  { name: '09:30', fund: 0, spy: 0 },
  { name: '10:00', fund: 0.5, spy: 0.2 },
  { name: '10:30', fund: 1.2, spy: 0.4 },
  { name: '11:00', fund: 0.8, spy: 0.6 },
  { name: '11:30', fund: 1.5, spy: 0.9 },
  { name: '12:00', fund: 2.1, spy: 1.1 },
  { name: '12:30', fund: 2.4, spy: 1.3 },
  { name: '13:00', fund: 2.2, spy: 1.5 },
  { name: '13:30', fund: 2.8, spy: 1.4 },
  { name: '14:00', fund: 3.2, spy: 1.8 },
];

interface Metric {
  label: string;
  value: string;
  color: string;
  icon: React.ElementType;
}

export function ProfitLossChart() {
  const [data, setData] = useState(INITIAL_DATA);
  const [metrics, setMetrics] = useState<Metric[]>([
    { label: "Alpha", value: "Loading...", color: "text-zinc-500", icon: Activity },
    { label: "Sharpe Ratio", value: "Loading...", color: "text-zinc-500", icon: Activity },
    { label: "Max Drawdown", value: "Loading...", color: "text-zinc-500", icon: Activity },
    { label: "Info Ratio", value: "Loading...", color: "text-zinc-500", icon: Activity },
  ]);

  useEffect(() => {
    // Simulate fetching real-time metrics
    const fetchMetrics = async () => {
      try {
        // const res = await fetch("http://localhost:8000/api/v1/metrics");
        // const data = await res.json();
        
        // Mock response
        await new Promise(r => setTimeout(r, 1000));
        
        setMetrics([
          { label: "Alpha", value: "+1.84", color: "text-green-600", icon: ArrowUpRight },
          { label: "Sharpe Ratio", value: "3.12", color: "text-blue-600", icon: Activity },
          { label: "Max Drawdown", value: "-2.4%", color: "text-red-600", icon: ArrowDownRight },
          { label: "Info Ratio", value: "1.45", color: "text-purple-600", icon: TrendingUp },
        ]);
        
        // Simulate live chart updates
        const interval = setInterval(() => {
            setData(prev => {
                // Just for visual effect, wiggle the last point or add a new one
                // Keeping the array static length for simplicity in this prototype
                return prev.map((p, i) => {
                    if (i === prev.length - 1) return { ...p, fund: p.fund + (Math.random() - 0.4) * 0.1 };
                    return p;
                });
            });
        }, 1000);
        
        return () => clearInterval(interval);

      } catch (e) {
        console.error("Failed to fetch metrics", e);
      }
    };

    fetchMetrics();
  }, []);

  return (
    <Card className="h-[500px] flex flex-col shadow-md">
      <CardHeader className="pb-4 border-b">
        <div className="flex items-center justify-between">
          <CardTitle>Real-Time Performance (Intraday)</CardTitle>
          <div className="flex gap-6">
             {metrics.map((m) => (
                <div key={m.label} className="flex flex-col items-end">
                   <span className="text-[10px] uppercase text-muted-foreground font-semibold">{m.label}</span>
                   <div className={`flex items-center gap-1 font-mono font-bold ${m.color}`}>
                      <m.icon className="h-3 w-3" />
                      {m.value}
                   </div>
                </div>
             ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 10,
              right: 10,
              left: 0,
              bottom: 0,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis unit="%" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip 
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Legend verticalAlign="top" height={36} />
            <Line
              type="monotone"
              dataKey="fund"
              stroke="#8b5cf6"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6 }}
              name="My Fund"
              isAnimationActive={false}
            />
            <Line 
              type="monotone" 
              dataKey="spy" 
              stroke="#94a3b8" 
              strokeWidth={2}
              dot={false}
              name="S&P 500"
              strokeDasharray="4 4"
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
