import * as React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  Radar,
  RadarChart,
  XAxis,
  YAxis,
} from "recharts";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { cn } from "@/lib/utils";
import {
  boolean,
  className,
  list,
  text,
  type AdapterProps,
} from "@/shadlet/types";

type Row = Record<string, unknown>;

function chartConfig(props: Record<string, unknown>): ChartConfig {
  const config: ChartConfig = {};
  for (const item of list<Record<string, unknown>>(props.series)) {
    const key = text(item.key) ?? "";
    if (!key) continue;
    config[key] = {
      label: text(item.label) ?? key,
      color:
        text(item.color) ??
        `var(--chart-${(Object.keys(config).length % 5) + 1})`,
    };
  }
  return config;
}

export function ChartAdapter({ props }: AdapterProps) {
  const data = list<Row>(props.data);
  const series = list<Record<string, unknown>>(props.series);
  const kind = text(props.kind) ?? "bar";
  const xKey = text(props.xKey) ?? "name";
  const stacked = boolean(props.stacked);
  const height = (props.height as string | number | undefined) ?? 300;
  const config = chartConfig(props);
  const common = (
    <>
      <CartesianGrid vertical={false} />
      <XAxis dataKey={xKey} tickLine={false} axisLine={false} tickMargin={8} />
      <YAxis tickLine={false} axisLine={false} tickMargin={8} />
      <ChartTooltip content={<ChartTooltipContent />} />
      {props.showLegend !== false ? (
        <ChartLegend content={<ChartLegendContent />} />
      ) : null}
    </>
  );

  let chart: React.ReactNode;
  if (kind === "line") {
    chart = (
      <LineChart data={data} margin={{ left: 12, right: 12 }}>
        {common}
        {series.map((item) => (
          <Line
            key={text(item.key)}
            type="monotone"
            dataKey={text(item.key)}
            stroke={`var(--color-${text(item.key)})`}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    );
  } else if (kind === "area") {
    chart = (
      <AreaChart data={data} margin={{ left: 12, right: 12 }}>
        {common}
        {series.map((item) => (
          <Area
            key={text(item.key)}
            type="monotone"
            dataKey={text(item.key) ?? ""}
            fill={`var(--color-${text(item.key)})`}
            fillOpacity={0.2}
            stroke={`var(--color-${text(item.key)})`}
            stackId={stacked ? "stack" : undefined}
          />
        ))}
      </AreaChart>
    );
  } else if (kind === "pie") {
    const first = text(series[0]?.key) ?? "";
    chart = (
      <PieChart>
        <ChartTooltip content={<ChartTooltipContent />} />
        <Pie data={data} dataKey={first} nameKey={xKey}>
          {data.map((_, index) => (
            <Cell key={index} fill={`var(--chart-${(index % 5) + 1})`} />
          ))}
        </Pie>
        {props.showLegend !== false ? (
          <ChartLegend content={<ChartLegendContent />} />
        ) : null}
      </PieChart>
    );
  } else if (kind === "radar") {
    chart = (
      <RadarChart data={data}>
        {common}
        {series.map((item) => (
          <Radar
            key={text(item.key)}
            dataKey={text(item.key)}
            stroke={`var(--color-${text(item.key)})`}
            fill={`var(--color-${text(item.key)})`}
            fillOpacity={0.2}
          />
        ))}
      </RadarChart>
    );
  } else {
    chart = (
      <BarChart data={data} margin={{ left: 12, right: 12 }}>
        {common}
        {series.map((item) => (
          <Bar
            key={text(item.key)}
            dataKey={text(item.key) ?? ""}
            fill={`var(--color-${text(item.key)})`}
            radius={4}
            stackId={stacked ? "stack" : undefined}
          />
        ))}
      </BarChart>
    );
  }

  return (
    <ChartContainer
      config={config}
      className={cn("w-full", className(props))}
      style={
        {
          height: (typeof height === "number"
            ? height
            : Number(height) ||
              300) as unknown as React.CSSProperties["height"],
        } as React.CSSProperties
      }
    >
      {chart}
    </ChartContainer>
  );
}
