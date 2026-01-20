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
  MarkerType,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const initialNodes: Node[] = [
  // Data Layer
  { 
    id: 'data-1', 
    position: { x: 50, y: 50 }, 
    data: { label: 'News Sentiment API' }, 
    sourcePosition: Position.Right,
    style: { background: '#f0f9ff', border: '1px solid #bae6fd', fontSize: '12px' }
  },
  { 
    id: 'data-2', 
    position: { x: 50, y: 150 }, 
    data: { label: 'Market Price Feed' }, 
    sourcePosition: Position.Right,
    style: { background: '#f0f9ff', border: '1px solid #bae6fd', fontSize: '12px' }
  },
  { 
    id: 'data-3', 
    position: { x: 50, y: 250 }, 
    data: { label: '10-K Filings' }, 
    sourcePosition: Position.Right,
    style: { background: '#f0f9ff', border: '1px solid #bae6fd', fontSize: '12px' }
  },

  // Agent Layer
  { 
    id: 'agent-wood', 
    position: { x: 300, y: 50 }, 
    data: { label: 'C. Wood (Growth)' }, 
    targetPosition: Position.Left,
    sourcePosition: Position.Right,
    style: { background: '#f3e8ff', border: '1px solid #d8b4fe', fontWeight: 'bold' }
  },
  { 
    id: 'agent-buffett', 
    position: { x: 300, y: 150 }, 
    data: { label: 'W. Buffett (Value)' }, 
    targetPosition: Position.Left,
    sourcePosition: Position.Right,
    style: { background: '#fef9c3', border: '1px solid #fde047', fontWeight: 'bold' }
  },
  { 
    id: 'agent-munger', 
    position: { x: 300, y: 250 }, 
    data: { label: 'C. Munger (Risk)' }, 
    targetPosition: Position.Left,
    sourcePosition: Position.Right,
    style: { background: '#f3f4f6', border: '1px solid #d1d5db', fontWeight: 'bold' }
  },

  // Decision Layer
  { 
    id: 'decision', 
    position: { x: 550, y: 150 }, 
    data: { label: 'Portfolio Manager' }, 
    targetPosition: Position.Left,
    type: 'output',
    style: { background: '#dcfce7', border: '1px solid #86efac', fontWeight: 'bold', width: 160 }
  },
];

const initialEdges = [
  { id: 'e1-wood', source: 'data-1', target: 'agent-wood', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-wood', source: 'data-2', target: 'agent-wood', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-buffett', source: 'data-2', target: 'agent-buffett', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-buffett', source: 'data-3', target: 'agent-buffett', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e1-munger', source: 'data-1', target: 'agent-munger', animated: true, stroke: 'red', markerEnd: { type: MarkerType.ArrowClosed } },
  
  { id: 'wood-pm', source: 'agent-wood', target: 'decision', animated: true, label: 'Buy Signal', style: { stroke: 'green' } },
  { id: 'buffett-pm', source: 'agent-buffett', target: 'decision', animated: true, label: 'Hold' },
  { id: 'munger-pm', source: 'agent-munger', target: 'decision', animated: true, label: 'Risk Alert', style: { stroke: 'red' } },
];

export function LogicalFlowGraph() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <Card className="h-[400px] flex flex-col shadow-md">
      <CardHeader>
        <CardTitle>Quant Logical Flow</CardTitle>
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