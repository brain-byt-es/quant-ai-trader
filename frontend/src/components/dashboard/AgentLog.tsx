"use client";

import { useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Rocket, ShieldAlert, Search, Banknote } from "lucide-react";

interface AgentMessage {
  id: string;
  agentName: string;
  message: string;
  timestamp: string;
  role: "analyst" | "critic" | "executor";
}

const AGENTS = {
  Buffett: { color: "bg-yellow-500", role: "analyst", icon: TrendingUp },
  Wood: { color: "bg-purple-500", role: "analyst", icon: Rocket },
  Munger: { color: "bg-gray-500", role: "critic", icon: ShieldAlert },
  Fisher: { color: "bg-blue-500", role: "analyst", icon: Search },
  Cohen: { color: "bg-green-600", role: "executor", icon: Banknote },
};

export function AgentLog() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Mock SSE connection
    const interval = setInterval(() => {
      const agents = Object.keys(AGENTS);
      const randomAgent = agents[Math.floor(Math.random() * agents.length)];
      const newMessage: AgentMessage = {
        id: crypto.randomUUID(),
        agentName: randomAgent,
        message: `Analyzing market data point #${Math.floor(Math.random() * 1000)}...`,
        timestamp: new Date().toLocaleTimeString(),
        role: AGENTS[randomAgent as keyof typeof AGENTS].role as "analyst" | "critic" | "executor",
      };

      setMessages((prev) => [...prev.slice(-49), newMessage]); // Keep last 50
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Card className="h-[400px] flex flex-col">
      <CardHeader>
        <CardTitle>Agent Log (Live Floor)</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full p-4">
          <div className="space-y-4">
            {messages.map((msg) => {
              const AgentIcon = AGENTS[msg.agentName as keyof typeof AGENTS].icon;
              return (
                <div key={msg.id} className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <Badge 
                      className={`${AGENTS[msg.agentName as keyof typeof AGENTS].color} text-white hover:${AGENTS[msg.agentName as keyof typeof AGENTS].color} flex items-center gap-1`}
                    >
                      <AgentIcon className="h-3 w-3" />
                      {msg.agentName}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{msg.timestamp}</span>
                  </div>
                  <p className="text-sm font-mono pl-2 border-l-2 border-muted">
                    {msg.message}
                  </p>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
