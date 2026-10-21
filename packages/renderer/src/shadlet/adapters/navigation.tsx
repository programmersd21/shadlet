import * as React from "react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { iconFor } from "@/shadlet/icons";
import {
  boolean,
  className,
  list,
  number,
  text,
  type AdapterProps,
} from "@/shadlet/types";

export function TabsAdapter({ props, slots, events, dispatch }: AdapterProps) {
  const value = props.value;
  const controlled = value !== null && value !== undefined;
  return (
    <Tabs
      value={controlled ? String(value) : undefined}
      defaultValue={controlled ? undefined : text(props.defaultValue)}
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      onValueChange={
        events.value_change
          ? (next) => dispatch("value_change", { value: next })
          : undefined
      }
      className={className(props)}
    >
      <TabsList>
        {list(props.items).map((item) => (
          <TabsTrigger
            key={text(item.value)}
            value={text(item.value) ?? ""}
            disabled={boolean(item.disabled)}
          >
            {item.icon ? iconFor(item.icon) : null}
            {text(item.label)}
          </TabsTrigger>
        ))}
      </TabsList>
      {list(props.items).map((item, index) => {
        const panel = text(item.panel) ?? `panel_${index}`;
        return (
          <TabsContent key={text(item.value)} value={text(item.value) ?? ""}>
            {slots[panel]}
          </TabsContent>
        );
      })}
    </Tabs>
  );
}

export function BreadcrumbAdapter({ props, events, dispatch, navigate }: AdapterProps) {
  const items = list<Record<string, unknown>>(props.items);
  return (
    <Breadcrumb className={className(props)}>
      <BreadcrumbList>
        {items.map((item, index) => {
          const href = text(item.href);
          const last = index === items.length - 1;
          const hasClick = Boolean(events?.click);
          return (
            <React.Fragment key={`${text(item.label)}-${index}`}>
              <BreadcrumbItem>
                {!last && (href || hasClick) ? (
                  <BreadcrumbLink
                    href={href || "#"}
                    onClick={(event) => {
                      event.preventDefault();
                      if (hasClick) {
                        dispatch("click", {
                          index,
                          label: text(item.label),
                          href,
                        });
                      } else if (href && href.startsWith("/")) {
                        navigate(href);
                      }
                    }}
                  >
                    {text(item.label)}
                  </BreadcrumbLink>
                ) : (
                  <BreadcrumbPage>{text(item.label)}</BreadcrumbPage>
                )}
              </BreadcrumbItem>
              {!last ? (
                <BreadcrumbSeparator>
                  {text(props.separator) ?? "/"}
                </BreadcrumbSeparator>
              ) : null}
            </React.Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}

function pageItems(
  current: number,
  total: number,
  siblings: number,
): (number | "ellipsis")[] {
  const pages = new Set<number>([1, total]);
  for (let page = current - siblings; page <= current + siblings; page += 1) {
    if (page >= 1 && page <= total) pages.add(page);
  }
  const sorted = [...pages].sort((a, b) => a - b);
  const result: (number | "ellipsis")[] = [];
  for (let index = 0; index < sorted.length; index += 1) {
    const page = sorted[index];
    const previous = sorted[index - 1];
    if (previous !== undefined && page - previous > 1) result.push("ellipsis");
    result.push(page);
  }
  return result;
}

export function PaginationAdapter({ props, dispatch }: AdapterProps) {
  const page = Math.max(1, number(props.page) ?? 1);
  const total = Math.max(1, number(props.totalPages) ?? 1);
  const siblings = number(props.siblingCount) ?? 1;
  const go = (next: number) => {
    if (next < 1 || next > total || next === page) return;
    dispatch("change", { value: next });
  };
  return (
    <Pagination className={className(props)}>
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            href="#"
            aria-disabled={page <= 1}
            className={page <= 1 ? "pointer-events-none opacity-50" : undefined}
            onClick={(event) => {
              event.preventDefault();
              go(page - 1);
            }}
          />
        </PaginationItem>
        {pageItems(page, total, siblings).map((item, index) =>
          item === "ellipsis" ? (
            <PaginationItem key={`ellipsis-${index}`}>
              <PaginationEllipsis />
            </PaginationItem>
          ) : (
            <PaginationItem key={item}>
              <PaginationLink
                href="#"
                isActive={item === page}
                onClick={(event) => {
                  event.preventDefault();
                  go(item);
                }}
              >
                {item}
              </PaginationLink>
            </PaginationItem>
          ),
        )}
        <PaginationItem>
          <PaginationNext
            href="#"
            aria-disabled={page >= total}
            className={
              page >= total ? "pointer-events-none opacity-50" : undefined
            }
            onClick={(event) => {
              event.preventDefault();
              go(page + 1);
            }}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}

export function SidebarAdapter({
  props,
  children,
  slots,
  navigate,
}: AdapterProps) {
  return (
    <SidebarProvider defaultOpen={props.defaultOpen !== false}>
      <Sidebar
        collapsible={
          (text(props.collapsible) as
            "offcanvas" | "icon" | "none" | undefined) ?? "icon"
        }
        side={(text(props.side) as "left" | "right" | undefined) ?? "left"}
        className={className(props)}
      >
        <SidebarHeader>
          {slots.header}
          <SidebarTrigger />
        </SidebarHeader>
        <SidebarContent>
          {list<Record<string, unknown>>(props.sections).map(
            (section, sectionIndex) => (
              <SidebarGroup key={sectionIndex}>
                {text(section.label) ? (
                  <SidebarGroupLabel>{text(section.label)}</SidebarGroupLabel>
                ) : null}
                <SidebarGroupContent>
                  <SidebarMenu>
                    {list<Record<string, unknown>>(section.items).map(
                      (item, index) => {
                        const href = text(item.href);
                        return (
                          <SidebarMenuItem key={`${text(item.label)}-${index}`}>
                            <SidebarMenuButton
                              isActive={boolean(item.active)}
                              onClick={() => {
                                if (href) navigate(href);
                              }}
                            >
                              {item.icon ? iconFor(item.icon) : null}
                              <span>{text(item.label)}</span>
                            </SidebarMenuButton>
                            {text(item.badge) ? (
                              <SidebarMenuBadge>
                                {text(item.badge)}
                              </SidebarMenuBadge>
                            ) : null}
                          </SidebarMenuItem>
                        );
                      },
                    )}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            ),
          )}
          {children}
        </SidebarContent>
        <SidebarFooter>{slots.footer}</SidebarFooter>
      </Sidebar>
    </SidebarProvider>
  );
}
