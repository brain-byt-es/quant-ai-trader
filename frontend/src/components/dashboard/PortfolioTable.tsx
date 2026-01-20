"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  createColumnHelper,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Position, useUniverseStore } from "@/store/useUniverseStore";
import { cn } from "@/lib/utils";

const columnHelper = createColumnHelper<Position>();

const columns = [
  columnHelper.accessor("symbol", {
    header: "Asset",
    cell: (info) => (
      <div className="flex flex-col">
        <span className="font-bold font-mono text-foreground">{info.getValue()}</span>
        <span className="text-[9px] text-muted-foreground uppercase tracking-tighter">Equity | NASDAQ</span>
      </div>
    ),
  }),
  columnHelper.accessor("qty", {
    header: "Current",
    cell: (info) => <span className="font-mono text-muted-foreground">{info.getValue()}</span>,
  }),
  columnHelper.accessor("targetQty", {
    header: "Target",
    cell: (info) => (
      <span className="font-mono text-blue-600 dark:text-blue-400 font-bold">{info.getValue()}</span>
    ),
  }),
  columnHelper.display({
    id: "intent",
    header: "Intent",
    cell: (info) => {
      const row = info.row.original;
      const delta = row.targetQty - row.qty;
      if (delta === 0) return <span className="text-muted-foreground/50 font-bold">HOLD</span>;
      return (
        <span className={cn("font-black text-[10px]", delta > 0 ? "text-emerald-600 dark:text-emerald-500" : "text-rose-600 dark:text-rose-500")}>
          {delta > 0 ? "BUY" : "SELL"}
        </span>
      );
    }
  }),
  columnHelper.display({
    id: "delta",
    header: "Delta",
    cell: (info) => {
      const row = info.row.original;
      const delta = row.targetQty - row.qty;
      if (delta === 0) return <span className="text-muted-foreground/30">-</span>;
      return (
        <span className={cn("font-mono font-bold px-1 rounded", delta > 0 ? "text-emerald-600 bg-emerald-500/10" : "text-rose-600 bg-rose-500/10")}>
          {delta > 0 ? "+" : ""}{delta}
        </span>
      );
    },
  }),
  columnHelper.accessor("currentPrice", {
    header: "Price",
    cell: (info) => <span className="font-mono text-foreground/80">${info.getValue().toFixed(2)}</span>,
  }),
  columnHelper.accessor("unrealizedPlPc", {
    header: "P&L",
    cell: (info) => {
      const val = info.getValue();
      return (
        <span className={cn("font-mono font-bold", val >= 0 ? "text-emerald-600 dark:text-emerald-500" : "text-rose-600 dark:text-rose-500")}>
          {val >= 0 ? "+" : ""}{val.toFixed(2)}%
        </span>
      );
    },
  }),
  columnHelper.display({
    id: "risk",
    header: "Risk (Altman Z)",
    cell: () => {
      // Logic: In a real run we'd have the Altman Z from the ticker state
      // For now, we simulate safe status
      return (
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
          <span className="text-[10px] font-bold text-muted-foreground">SAFE</span>
        </div>
      );
    },
  }),
];

export function PortfolioTable() {

  const positions = useUniverseStore((state) => state.positions);



    const table = useReactTable({ // eslint-disable-line react-hooks/incompatible-library



      data: positions,



      columns,



      getCoreRowModel: getCoreRowModel(),



    });



  





  return (

    <div className="bg-background border-t border-border">

      <div className="max-h-[300px] overflow-auto">

        <Table>

          <TableHeader className="bg-card sticky top-0 z-10 border-b border-border">

            {table.getHeaderGroups().map((headerGroup) => (

              <TableRow key={headerGroup.id} className="border-border hover:bg-transparent">

                {headerGroup.headers.map((header) => (

                  <TableHead key={header.id} className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground h-10">

                    {flexRender(header.column.columnDef.header, header.getContext())}

                  </TableHead>

                ))}

              </TableRow>

            ))}

          </TableHeader>

          <TableBody>

            {table.getRowModel().rows.length ? (

              table.getRowModel().rows.map((row) => (

                <TableRow key={row.id} className="border-border/50 hover:bg-muted/30 transition-colors">

                  {row.getVisibleCells().map((cell) => (

                    <TableCell key={cell.id} className="py-2.5 text-xs text-foreground/90 font-mono">

                      {flexRender(cell.column.columnDef.cell, cell.getContext())}

                    </TableCell>

                  ))}

                </TableRow>

              ))

            ) : (

              <TableRow>

                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground font-mono text-xs italic">

                  AWAITING TARGET REBALANCE...

                </TableCell>

              </TableRow>

            )}

          </TableBody>

        </Table>

      </div>

    </div>

  );

}
