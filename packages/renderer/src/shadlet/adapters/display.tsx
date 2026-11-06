import * as React from "react";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnFiltersState,
  type ColumnDef,
  type SortingState,
  type VisibilityState,
} from "@tanstack/react-table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

function filterRecord(filters: ColumnFiltersState): Record<string, string> {
  return Object.fromEntries(
    filters.flatMap((filter) =>
      typeof filter.value === "string" && filter.value
        ? [[filter.id, filter.value]]
        : [],
    ),
  );
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
  const rowKey = text(props.rowKey);
  const loading = boolean(props.loading);
  const error = text(props.error);
  const unavailable = loading || Boolean(error);
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
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    () =>
      Object.entries(record(props.filters)).flatMap(([id, value]) =>
        typeof value === "string" ? [{ id, value }] : [],
      ),
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [selectedKeys, setSelectedKeys] = React.useState<Set<string>>(
    () => new Set(list<string>(props.selectedKeys)),
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
    setColumnFilters(
      Object.entries(record(props.filters)).flatMap(([id, value]) =>
        typeof value === "string" ? [{ id, value }] : [],
      ),
    );
    setSelectedKeys(new Set(list<string>(props.selectedKeys)));
  }, [
    props.filters,
    props.pageIndex,
    props.search,
    props.selectedKeys,
    props.sorting,
  ]);

  const changeSelection = React.useCallback(
    (key: string, checked: boolean) => {
      const next = new Set(selectedKeys);
      if (checked) next.add(key);
      else next.delete(key);
      setSelectedKeys(next);
      dispatch("selection_change", { values: { keys: [...next] } });
    },
    [dispatch, selectedKeys],
  );

  const dispatchQuery = React.useCallback(
    (
      nextPage: number,
      nextSorting: SortingState,
      nextSearch: string,
      nextFilters: ColumnFiltersState,
    ) => {
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
          filters: filterRecord(nextFilters),
        },
      });
    },
    [dispatch, events.query_change, pageSize, serverSide],
  );

  const definitions = React.useMemo<ColumnDef<Row>[]>(
    () =>
      cols.map((column) => ({
        accessorKey: column.key,
        header: column.header,
        enableSorting: column.sortable,
        enableColumnFilter: column.filterable,
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
      columnFilters,
      columnVisibility,
      pagination: { pageIndex, pageSize: number(props.pageSize) ?? 10 },
    },
    onSortingChange: (updater) => {
      const next = typeof updater === "function" ? updater(sorting) : updater;
      setSorting(next);
      setPageIndex(0);
      dispatchQuery(0, next, globalFilter, columnFilters);
    },
    onGlobalFilterChange: (updater) => {
      const next =
        typeof updater === "function" ? updater(globalFilter) : updater;
      setGlobalFilter(next);
      setPageIndex(0);
      dispatchQuery(0, sorting, next, columnFilters);
    },
    onColumnFiltersChange: (updater) => {
      const next =
        typeof updater === "function" ? updater(columnFilters) : updater;
      setColumnFilters(next);
      setPageIndex(0);
      dispatchQuery(0, sorting, globalFilter, next);
    },
    onColumnVisibilityChange: setColumnVisibility,
    onPaginationChange: (updater) => {
      const next =
        typeof updater === "function"
          ? updater({ pageIndex, pageSize })
          : updater;
      setPageIndex(next.pageIndex);
      dispatchQuery(next.pageIndex, sorting, globalFilter, columnFilters);
    },
    getCoreRowModel: getCoreRowModel(),
    getRowId: rowKey
      ? (row, index) => {
          const value = row[rowKey];
          return typeof value === "string" || typeof value === "number"
            ? String(value)
            : String(index);
        }
      : undefined,
    getSortedRowModel: serverSide ? undefined : getSortedRowModel(),
    getFilteredRowModel: serverSide ? undefined : getFilteredRowModel(),
    getPaginationRowModel: serverSide ? undefined : getPaginationRowModel(),
    manualSorting: serverSide,
    manualFiltering: serverSide,
    manualPagination: serverSide,
    pageCount: serverSide ? Math.ceil(totalRows / pageSize) : undefined,
    globalFilterFn: "includesString",
  });
  const visibleRows = table.getRowModel().rows;
  const selectedVisibleCount = visibleRows.filter((row) =>
    selectedKeys.has(rowKey ? String(row.original[rowKey]) : ""),
  ).length;

  return (
    <div className={cn("flex flex-col gap-3", className(props))}>
      <div className="flex flex-wrap gap-3">
        {props.searchable !== false ? (
          <Input
            value={globalFilter}
            onChange={(event) => table.setGlobalFilter(event.target.value)}
            placeholder={text(props.searchPlaceholder) ?? "filter rows..."}
            className="max-w-sm"
            aria-label="filter rows"
            disabled={unavailable}
          />
        ) : null}
        {cols
          .filter((column) => column.filterable)
          .map((column) => (
            <Input
              key={column.key}
              value={String(
                columnFilters.find((filter) => filter.id === column.key)
                  ?.value ?? "",
              )}
              onChange={(event) =>
                table.getColumn(column.key)?.setFilterValue(event.target.value)
              }
              placeholder={`filter ${column.header.toLowerCase()}...`}
              aria-label={`filter ${column.header}`}
              className="max-w-sm"
              disabled={unavailable}
            />
          ))}
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={unavailable}
                aria-label="choose visible columns"
              >
                columns
              </Button>
            }
          />
          <DropdownMenuContent align="end">
            <DropdownMenuGroup>
              <DropdownMenuLabel>visible columns</DropdownMenuLabel>
              {table.getAllLeafColumns().map((column) => (
                <DropdownMenuCheckboxItem
                  key={column.id}
                  checked={column.getIsVisible()}
                  onCheckedChange={(checked) =>
                    column.toggleVisibility(checked)
                  }
                >
                  {column.id}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div
        className="overflow-x-auto rounded-md border"
        aria-busy={loading || undefined}
      >
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id}>
                {events.selection_change ? (
                  <TableHead className="w-10">
                    <Checkbox
                      aria-label="select all rows on this page"
                      checked={
                        visibleRows.length > 0 &&
                        selectedVisibleCount === visibleRows.length
                      }
                      indeterminate={
                        selectedVisibleCount > 0 &&
                        selectedVisibleCount < visibleRows.length
                      }
                      disabled={unavailable}
                      onCheckedChange={(checked) => {
                        const next = new Set(selectedKeys);
                        for (const row of visibleRows) {
                          const key = rowKey
                            ? String(row.original[rowKey])
                            : "";
                          if (checked) next.add(key);
                          else next.delete(key);
                        }
                        setSelectedKeys(next);
                        dispatch("selection_change", {
                          values: { keys: [...next] },
                        });
                      }}
                    />
                  </TableHead>
                ) : null}
                {group.headers.map((header) => {
                  const meta = header.column.columnDef.meta as
                    | { align?: Column["align"]; width?: string | null }
                    | undefined;
                  return (
                    <TableHead
                      key={header.id}
                      className={alignClass(meta?.align ?? "left")}
                      style={meta?.width ? { width: meta.width } : undefined}
                      aria-sort={
                        header.column.getIsSorted() === "asc"
                          ? "ascending"
                          : header.column.getIsSorted() === "desc"
                            ? "descending"
                            : undefined
                      }
                    >
                      {header.column.getCanSort() ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="-ml-2 h-8"
                          disabled={unavailable}
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
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={Math.max(
                    1,
                    cols.length + (events.selection_change ? 1 : 0),
                  )}
                  className="h-24 text-center text-muted-foreground"
                  role="status"
                >
                  loading...
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell
                  colSpan={Math.max(1, cols.length)}
                  className="h-24 text-center text-destructive"
                  role="alert"
                >
                  {error}
                  {events.retry ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="ml-3"
                      onClick={() => dispatch("retry", {})}
                    >
                      retry
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={cols.length + (events.selection_change ? 1 : 0)}
                  className="h-24 text-center text-muted-foreground"
                >
                  {globalFilter
                    ? `${text(props.emptyText) ?? "no results"} for "${globalFilter}"`
                    : (text(props.emptyText) ?? "no results")}
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className={
                    events.row_click
                      ? "cursor-pointer focus-visible:outline"
                      : undefined
                  }
                  tabIndex={events.row_click ? 0 : undefined}
                  aria-label={
                    events.row_click
                      ? `row ${rowKey ? String(row.original[rowKey]) : row.id}`
                      : undefined
                  }
                  onClick={
                    events.row_click
                      ? () => dispatch("row_click", { value: row.original })
                      : undefined
                  }
                  onKeyDown={
                    events.row_click
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            dispatch("row_click", { value: row.original });
                          }
                        }
                      : undefined
                  }
                >
                  {events.selection_change ? (
                    <TableCell>
                      <Checkbox
                        aria-label={`select row ${rowKey ? String(row.original[rowKey]) : row.id}`}
                        checked={selectedKeys.has(
                          rowKey ? String(row.original[rowKey]) : "",
                        )}
                        disabled={unavailable}
                        onClick={(event) => event.stopPropagation()}
                        onKeyDown={(event) => event.stopPropagation()}
                        onCheckedChange={(checked) =>
                          changeSelection(
                            rowKey ? String(row.original[rowKey]) : "",
                            checked === true,
                          )
                        }
                      />
                    </TableCell>
                  ) : null}
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
              disabled={unavailable || !table.getCanPreviousPage()}
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
              disabled={unavailable || !table.getCanNextPage()}
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
