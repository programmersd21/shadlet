import * as React from "react";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
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
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  boolean,
  className,
  list,
  number,
  record,
  text,
  type AdapterProps,
} from "@/shadlet/types";

type Row = Record<string, unknown>;
type Column = {
  key: string;
  header: string;
  align: "left" | "center" | "right";
  width: string | null;
  sortable: boolean;
  filterable: boolean;
};

function columns(value: unknown): Column[] {
  return list<Record<string, unknown>>(value).map((column) => ({
    key: text(column.key) ?? "",
    header: text(column.header) ?? "",
    align:
      column.align === "center" || column.align === "right"
        ? column.align
        : "left",
    width: text(column.width) ?? null,
    sortable: boolean(column.sortable),
    filterable: boolean(column.filterable),
  }));
}

function cellText(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function alignClass(align: Column["align"]): string {
  return align === "center"
    ? "text-center"
    : align === "right"
      ? "text-right"
      : "";
}

export function CardAdapter({ props, children, slots }: AdapterProps) {
  return (
    <Card className={className(props)}>
      {text(props.title) || text(props.description) || slots.action ? (
        <CardHeader>
          {text(props.title) ? (
            <CardTitle>{text(props.title)}</CardTitle>
          ) : null}
          {text(props.description) ? (
            <CardDescription>{text(props.description)}</CardDescription>
          ) : null}
          {slots.action ? <CardAction>{slots.action}</CardAction> : null}
        </CardHeader>
      ) : null}
      <CardContent>{children}</CardContent>
      {slots.footer ? <CardFooter>{slots.footer}</CardFooter> : null}
    </Card>
  );
}

export function TableAdapter({ props }: AdapterProps) {
  const cols = columns(props.columns);
  const rows = list<Row>(props.rows);
  return (
    <Table className={className(props)}>
      {text(props.caption) ? (
        <TableCaption>{text(props.caption)}</TableCaption>
      ) : null}
      <TableHeader>
        <TableRow>
          {cols.map((column) => (
            <TableHead
              key={column.key}
              className={alignClass(column.align)}
              style={column.width ? { width: column.width } : undefined}
            >
              {column.header}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row, index) => (
          <TableRow key={index}>
            {cols.map((column) => (
              <TableCell key={column.key} className={alignClass(column.align)}>
                {cellText(row[column.key])}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
      {text(props.footer) ? (
        <TableFooter>
          <TableRow>
            <TableCell colSpan={Math.max(1, cols.length)}>
              {text(props.footer)}
            </TableCell>
          </TableRow>
        </TableFooter>
      ) : null}
    </Table>
  );
}

export function DataTableAdapter({ props, events, dispatch }: AdapterProps) {
  const cols = columns(props.columns);
  const rows = list<Row>(props.rows);
  const serverSide = boolean(props.serverSide);
  const pageSize = number(props.pageSize) ?? 10;
  const totalRows = number(props.totalRows) ?? rows.length;
  const [sorting, setSorting] = React.useState<SortingState>(
    list<Record<string, unknown>>(props.sorting).flatMap((item) =>
      typeof item.id === "string" && typeof item.desc === "boolean"
        ? [{ id: item.id, desc: item.desc }]
        : [],
    ),
  );
  const [globalFilter, setGlobalFilter] = React.useState(
    text(props.search) ?? "",
  );
  const [pageIndex, setPageIndex] = React.useState(
    number(props.pageIndex) ?? 0,
  );

  React.useEffect(() => {
    setSorting(
      list<Record<string, unknown>>(props.sorting).flatMap((item) =>
        typeof item.id === "string" && typeof item.desc === "boolean"
          ? [{ id: item.id, desc: item.desc }]
          : [],
      ),
    );
    setGlobalFilter(text(props.search) ?? "");
    setPageIndex(number(props.pageIndex) ?? 0);
  }, [props.pageIndex, props.search, props.sorting]);

  const dispatchQuery = React.useCallback(
    (nextPage: number, nextSorting: SortingState, nextSearch: string) => {
      if (!serverSide || !events.query_change) return;
      dispatch("query_change", {
        values: {
          page_index: nextPage,
          page_size: pageSize,
          sorting: nextSorting.map((item) => ({
            key: item.id,
            direction: item.desc ? "desc" : "asc",
          })),
          search: nextSearch,
          filters: record(props.filters),
        },
      });
    },
    [dispatch, events.query_change, pageSize, props.filters, serverSide],
  );

  const definitions = React.useMemo<ColumnDef<Row>[]>(
    () =>
      cols.map((column) => ({
        accessorKey: column.key,
        header: column.header,
        enableSorting: column.sortable,
        enableGlobalFilter: column.filterable || props.searchable !== false,
        meta: { align: column.align, width: column.width },
      })),
    [cols, props.searchable],
  );

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: rows,
    columns: definitions,
    state: {
      sorting,
      globalFilter,
      pagination: { pageIndex, pageSize: number(props.pageSize) ?? 10 },
    },
    onSortingChange: (updater) => {
      const next = typeof updater === "function" ? updater(sorting) : updater;
      setSorting(next);
      setPageIndex(0);
      dispatchQuery(0, next, globalFilter);
    },
    onGlobalFilterChange: (updater) => {
      const next =
        typeof updater === "function" ? updater(globalFilter) : updater;
      setGlobalFilter(next);
      setPageIndex(0);
      dispatchQuery(0, sorting, next);
    },
    onPaginationChange: (updater) => {
      const next =
        typeof updater === "function"
          ? updater({ pageIndex, pageSize })
          : updater;
      setPageIndex(next.pageIndex);
      dispatchQuery(next.pageIndex, sorting, globalFilter);
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: serverSide ? undefined : getSortedRowModel(),
    getFilteredRowModel: serverSide ? undefined : getFilteredRowModel(),
    getPaginationRowModel: serverSide ? undefined : getPaginationRowModel(),
    manualSorting: serverSide,
    manualFiltering: serverSide,
    manualPagination: serverSide,
    pageCount: serverSide ? Math.ceil(totalRows / pageSize) : undefined,
    globalFilterFn: "includesString",
  });

  return (
    <div className={cn("flex flex-col gap-3", className(props))}>
      {props.searchable !== false ? (
        <Input
          value={globalFilter}
          onChange={(event) => {
            setGlobalFilter(event.target.value);
            setPageIndex(0);
          }}
          placeholder={text(props.searchPlaceholder) ?? "filter rows..."}
          className="max-w-sm"
          aria-label="filter rows"
        />
      ) : null}
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id}>
                {group.headers.map((header) => {
                  const meta = header.column.columnDef.meta as
                    | { align?: Column["align"]; width?: string | null }
                    | undefined;
                  return (
                    <TableHead
                      key={header.id}
                      className={alignClass(meta?.align ?? "left")}
                      style={meta?.width ? { width: meta.width } : undefined}
                    >
                      {header.column.getCanSort() ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="-ml-2 h-8"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                          {header.column.getIsSorted() === "asc"
                            ? " ↑"
                            : header.column.getIsSorted() === "desc"
                              ? " ↓"
                              : ""}
                        </Button>
                      ) : (
                        flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={cols.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  {text(props.emptyText) ?? "no results"}
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className={events.row_click ? "cursor-pointer" : undefined}
                  onClick={
                    events.row_click
                      ? () => dispatch("row_click", { value: row.original })
                      : undefined
                  }
                >
                  {row.getVisibleCells().map((cell) => {
                    const meta = cell.column.columnDef.meta as
                      { align?: Column["align"] } | undefined;
                    return (
                      <TableCell
                        key={cell.id}
                        className={alignClass(meta?.align ?? "left")}
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      {table.getPageCount() > 1 ? (
        <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
          <span>
            page {pageIndex + 1} of {table.getPageCount()}
          </span>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!table.getCanPreviousPage()}
              onClick={() => {
                table.previousPage();
                if (events.page_change) {
                  dispatch("page_change", { value: pageIndex });
                }
              }}
            >
              previous
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!table.getCanNextPage()}
              onClick={() => {
                table.nextPage();
                if (events.page_change) {
                  dispatch("page_change", { value: pageIndex + 2 });
                }
              }}
            >
              next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

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

export function CarouselAdapter({ props, children }: AdapterProps) {
  const slides = React.Children.toArray(children);
  return (
    <Carousel
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      opts={{ loop: boolean(props.loop) }}
      className={cn("w-full", className(props))}
    >
      <CarouselContent>
        {slides.map((slide, index) => (
          <CarouselItem key={index}>{slide}</CarouselItem>
        ))}
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  );
}

export function AccordionAdapter({
  props,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const multiple = props.type === "multiple";
  const raw = props.value ?? props.defaultValue;
  const value = Array.isArray(raw)
    ? raw.map(String)
    : raw === null || raw === undefined || raw === ""
      ? []
      : [String(raw)];
  return (
    <Accordion
      multiple={multiple}
      value={value}
      onValueChange={
        events.value_change
          ? (next) =>
              dispatch("value_change", {
                value: multiple ? next : (next[0] ?? null),
              })
          : undefined
      }
      className={className(props)}
    >
      {list(props.items).map((item, index) => {
        const itemValue = text(item.value) ?? "";
        return (
          <AccordionItem
            key={itemValue}
            value={itemValue}
            disabled={boolean(item.disabled)}
          >
            <AccordionTrigger>{text(item.title)}</AccordionTrigger>
            <AccordionContent>
              {slots[text(item.panel) ?? `panel_${index}`]}
            </AccordionContent>
          </AccordionItem>
        );
      })}
    </Accordion>
  );
}

export function CollapsibleAdapter({
  props,
  children,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = React.isValidElement(slots.trigger)
    ? slots.trigger
    : undefined;
  const open = props.open;
  const controlled = open !== null && open !== undefined;
  return (
    <Collapsible
      open={controlled ? boolean(open) : undefined}
      defaultOpen={controlled ? undefined : boolean(props.defaultOpen)}
      onOpenChange={
        events.open_change
          ? (next) => dispatch("open_change", { open: next })
          : undefined
      }
      className={className(props)}
    >
      {trigger ? <CollapsibleTrigger render={trigger} /> : null}
      <CollapsibleContent>{children}</CollapsibleContent>
    </Collapsible>
  );
}

export function ResizableAdapter({ props, children }: AdapterProps) {
  const panels = React.Children.toArray(children);
  const sizes = list<number>(props.sizes);
  const minSizes = list<number>(props.minSizes);
  return (
    <ResizablePanelGroup
      orientation={props.direction === "vertical" ? "vertical" : "horizontal"}
      className={className(props)}
    >
      {panels.map((panel, index) => (
        <React.Fragment key={index}>
          <ResizablePanel defaultSize={sizes[index]} minSize={minSizes[index]}>
            {panel}
          </ResizablePanel>
          {index < panels.length - 1 ? <ResizableHandle withHandle /> : null}
        </React.Fragment>
      ))}
    </ResizablePanelGroup>
  );
}
