"use client";

import { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Position,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const initialNodes: Node[] = [
  { 
    id: '1', 
    position: { x: 50, y: 150 }, 
    data: { label: 'Data Ingestion' },
    type: 'input',
    sourcePosition: Position.Right,
    style: { background: '#fff', border: '1px solid #777', padding: 10, borderRadius: 5, width: 150, textAlign: 'center' }
  },
  { 
    id: '2', 
    position: { x: 300, y: 50 }, 
    data: { label: 'Analyst Debate (Buffett, Wood)' },
    targetPosition: Position.Left,
    sourcePosition: Position.Right,
    style: { background: '#eef', border: '1px solid #777', padding: 10, borderRadius: 5, width: 200, textAlign: 'center' }

  },
  { 
    id: '3', 
    position: { x: 300, y: 250 }, 
    data: { label: 'Risk Manager (Munger)' },
    targetPosition: Position.Left,
    sourcePosition: Position.Right,
    style: { background: '#fee', border: '1px solid #777', padding: 10, borderRadius: 5, width: 180, textAlign: 'center' }
  },
  { 
    id: '4', 
    position: { x: 600, y: 150 }, 
    data: { label: 'Final Decision' },
    type: 'output',
    targetPosition: Position.Left,
    style: { background: '#efe', border: '1px solid #777', padding: 10, borderRadius: 5, width: 150, textAlign: 'center', fontWeight: 'bold' }
  },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e1-3', source: '1', target: '3', animated: true },
  { id: 'e2-4', source: '2', target: '4', animated: true },
  { id: 'e3-4', source: '3', target: '4', animated: true },
];

export function LiveLogicGraph() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <Card className="h-[400px] flex flex-col">
      <CardHeader>
        <CardTitle>Live Logic Graph</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 p-0 h-full min-h-0">
        <div style={{ width: '100%', height: '100%' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
            attributionPosition="bottom-left"
          >
            <Controls />
            <MiniMap />
            <Background gap={12} size={1} />
          </ReactFlow>
        </div>
      </CardContent>
    </Card>
  );
}
