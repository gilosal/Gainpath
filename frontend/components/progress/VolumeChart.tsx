"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { WeeklyTrendPoint } from "@/lib/types";

interface VolumeChartProps {
  title: string;
  data: WeeklyTrendPoint[];
  dataKey: keyof WeeklyTrendPoint;
  color: string;
  unit?: string;
  height?: number;
}

// Format "2025-W03" → "W3"
function formatWeekLabel(week: string): string {
  const parts = week.split("-W");
  return parts[1] ? `W${parseInt(parts[1])}` : week;
}

export function VolumeChart({
  title,
  data,
  dataKey,
  color,
  unit = "",
  height = 200,
}: VolumeChartProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="hsl(var(--border))"
            vertical={false}
          />
          <XAxis
            dataKey="week"
            tickFormatter={formatWeekLabel}
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
              color: "hsl(var(--foreground))",
            }}
            labelStyle={{ color: "hsl(var(--muted-foreground))" }}
            formatter={(value: number) => [`${value}${unit}`, title]}
            labelFormatter={formatWeekLabel}
          />
          <Area
            type="monotone"
            dataKey={dataKey as string}
            stroke={color}
            strokeWidth={2}
            fill={`url(#grad-${dataKey})`}
            dot={false}
            activeDot={{ r: 4, fill: color, strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
