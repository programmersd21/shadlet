import * as React from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuGroup,
  ContextMenuItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import {
  Menubar,
  MenubarContent,
  MenubarGroup,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarShortcut,
  MenubarTrigger,
} from "@/components/ui/menubar";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { iconFor } from "@/shadlet/icons";
import {
  boolean,
  className,
  list,
  text,
  type AdapterProps,
} from "@/shadlet/types";

type MenuEntry = Record<string, unknown>;
type SlotNode = React.ReactNode;

function triggerRender(slot: SlotNode): React.ReactElement | undefined {
  return React.isValidElement(slot) ? slot : undefined;
}

function openProps(
  props: Record<string, unknown>,
  events: Record<string, string>,
  dispatch: AdapterProps["dispatch"],
) {
  const value = props.open;
  const controlled = value !== null && value !== undefined;
  return {
    open: controlled ? boolean(value) : undefined,
    onOpenChange: events.open_change
      ? (open: boolean) => dispatch("open_change", { open })
      : undefined,
  };
}

function renderMenuEntries(
  entries: MenuEntry[],
  dispatch: AdapterProps["dispatch"],
  components: {
    Item: typeof DropdownMenuItem;
    Group: typeof DropdownMenuGroup;
    Label: typeof DropdownMenuLabel;
    Separator: typeof DropdownMenuSeparator;
    Shortcut: typeof DropdownMenuShortcut;
  },
) {
  return entries.map((entry, index) => {
    if (entry.kind === "group") {
      return (
        <components.Group key={`group-${index}`}>
          <components.Label>{text(entry.label)}</components.Label>
          {renderMenuEntries(list(entry.items), dispatch, components)}
        </components.Group>
      );
    }
    const value = text(entry.value) ?? "";
    return (
      <React.Fragment key={`${value}-${index}`}>
        {boolean(entry.separatorBefore) ? <components.Separator /> : null}
        <components.Item
          disabled={boolean(entry.disabled)}
          variant={boolean(entry.destructive) ? "destructive" : "default"}
          onSelect={() => dispatch("select", { value })}
        >
          {entry.icon ? iconFor(entry.icon) : null}
          {text(entry.label)}
          {text(entry.shortcut) ? (
            <components.Shortcut>{text(entry.shortcut)}</components.Shortcut>
          ) : null}
        </components.Item>
      </React.Fragment>
    );
  });
}

export function DialogAdapter({
  props,
  children,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  return (
    <Dialog {...openProps(props, events, dispatch)}>
      {trigger ? <DialogTrigger render={trigger} /> : null}
      <DialogContent
        showCloseButton={props.showClose !== false}
        className={className(props)}
      >
        {text(props.title) || text(props.description) ? (
          <DialogHeader>
            {text(props.title) ? (
              <DialogTitle>{text(props.title)}</DialogTitle>
            ) : null}
            {text(props.description) ? (
              <DialogDescription>{text(props.description)}</DialogDescription>
            ) : null}
          </DialogHeader>
        ) : null}
        {children}
        {slots.footer ? <DialogFooter>{slots.footer}</DialogFooter> : null}
      </DialogContent>
    </Dialog>
  );
}

export function AlertDialogAdapter({
  props,
  children,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  const action = triggerRender(slots.action);
  const cancel = triggerRender(slots.cancel);
  return (
    <AlertDialog {...openProps(props, events, dispatch)}>
      {trigger ? <AlertDialogTrigger render={trigger} /> : null}
      <AlertDialogContent className={className(props)}>
        <AlertDialogHeader>
          {text(props.title) ? (
            <AlertDialogTitle>{text(props.title)}</AlertDialogTitle>
          ) : null}
          {text(props.description) ? (
            <AlertDialogDescription>
              {text(props.description)}
            </AlertDialogDescription>
          ) : null}
        </AlertDialogHeader>
        {children}
        {slots.action || slots.cancel ? (
          <AlertDialogFooter>
            {cancel ? <AlertDialogCancel render={cancel} /> : null}
            {action ? <AlertDialogAction render={action} /> : null}
          </AlertDialogFooter>
        ) : null}
      </AlertDialogContent>
    </AlertDialog>
  );
}

export function SheetAdapter({
  props,
  children,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  return (
    <Sheet {...openProps(props, events, dispatch)}>
      {trigger ? <SheetTrigger render={trigger} /> : null}
      <SheetContent
        side={
          (text(props.side) as
            "top" | "right" | "bottom" | "left" | undefined) ?? "right"
        }
        showCloseButton={props.showClose !== false}
        className={className(props)}
      >
        {text(props.title) || text(props.description) ? (
          <SheetHeader>
            {text(props.title) ? (
              <SheetTitle>{text(props.title)}</SheetTitle>
            ) : null}
            {text(props.description) ? (
              <SheetDescription>{text(props.description)}</SheetDescription>
            ) : null}
          </SheetHeader>
        ) : null}
        {children}
        {slots.footer ? <SheetFooter>{slots.footer}</SheetFooter> : null}
      </SheetContent>
    </Sheet>
  );
}

export function DrawerAdapter({
  props,
  children,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  const direction = text(props.direction) ?? "bottom";
  return (
    <Drawer
      swipeDirection={direction as "up" | "down" | "left" | "right"}
      {...openProps(props, events, dispatch)}
    >
      {trigger ? <DrawerTrigger render={trigger} /> : null}
      <DrawerContent className={className(props)}>
        <DrawerHeader>
          {text(props.title) ? (
            <DrawerTitle>{text(props.title)}</DrawerTitle>
          ) : null}
          {text(props.description) ? (
            <DrawerDescription>{text(props.description)}</DrawerDescription>
          ) : null}
        </DrawerHeader>
        {children}
        {slots.footer ? <DrawerFooter>{slots.footer}</DrawerFooter> : null}
      </DrawerContent>
    </Drawer>
  );
}

export function PopoverAdapter({
  props,
  children,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  return (
    <Popover {...openProps(props, events, dispatch)}>
      {trigger ? <PopoverTrigger render={trigger} /> : null}
      <PopoverContent
        align={
          (text(props.align) as "start" | "center" | "end" | undefined) ??
          "center"
        }
        side={
          (text(props.side) as
            "top" | "right" | "bottom" | "left" | undefined) ?? "bottom"
        }
        className={className(props)}
      >
        {children}
      </PopoverContent>
    </Popover>
  );
}

export function TooltipAdapter({ props, children, slots }: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  return (
    <Tooltip>
      {trigger ? <TooltipTrigger render={trigger} /> : null}
      <TooltipContent
        side={
          (text(props.side) as
            "top" | "right" | "bottom" | "left" | undefined) ?? "top"
        }
      >
        {children}
      </TooltipContent>
    </Tooltip>
  );
}

export function HoverCardAdapter({ props, children, slots }: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  return (
    <HoverCard>
      {trigger ? <HoverCardTrigger render={trigger} /> : null}
      <HoverCardContent className={className(props)}>
        {children}
      </HoverCardContent>
    </HoverCard>
  );
}

export function DropdownMenuAdapter({
  props,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const trigger = triggerRender(slots.trigger);
  return (
    <DropdownMenu {...openProps(props, events, dispatch)}>
      {trigger ? <DropdownMenuTrigger render={trigger} /> : null}
      <DropdownMenuContent
        align={
          (text(props.align) as "start" | "center" | "end" | undefined) ??
          "start"
        }
        side={
          (text(props.side) as
            "top" | "right" | "bottom" | "left" | undefined) ?? "bottom"
        }
        className={className(props)}
      >
        {text(props.label) ? (
          <DropdownMenuLabel>{text(props.label)}</DropdownMenuLabel>
        ) : null}
        {renderMenuEntries(list(props.items), dispatch, {
          Item: DropdownMenuItem,
          Group: DropdownMenuGroup,
          Label: DropdownMenuLabel,
          Separator: DropdownMenuSeparator,
          Shortcut: DropdownMenuShortcut,
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ContextMenuAdapter({
  props,
  children,
  dispatch,
}: AdapterProps) {
  return (
    <ContextMenu>
      <ContextMenuTrigger>{children}</ContextMenuTrigger>
      <ContextMenuContent>
        {list(props.items).map((entry, index) =>
          entry.kind === "group" ? (
            <ContextMenuGroup key={`group-${index}`}>
              <ContextMenuLabel>{text(entry.label)}</ContextMenuLabel>
              {list(entry.items).map((item, itemIndex) => {
                const value = text(item.value) ?? "";
                return (
                  <ContextMenuItem
                    key={`${value}-${itemIndex}`}
                    disabled={boolean(item.disabled)}
                    variant={
                      boolean(item.destructive) ? "destructive" : "default"
                    }
                    onSelect={() => dispatch("select", { value })}
                  >
                    {item.icon ? iconFor(item.icon) : null}
                    {text(item.label)}
                    {text(item.shortcut) ? (
                      <ContextMenuShortcut>
                        {text(item.shortcut)}
                      </ContextMenuShortcut>
                    ) : null}
                  </ContextMenuItem>
                );
              })}
            </ContextMenuGroup>
          ) : (
            <React.Fragment key={index}>
              {boolean(entry.separatorBefore) ? <ContextMenuSeparator /> : null}
              <ContextMenuItem
                disabled={boolean(entry.disabled)}
                variant={boolean(entry.destructive) ? "destructive" : "default"}
                onSelect={() =>
                  dispatch("select", { value: text(entry.value) ?? "" })
                }
              >
                {entry.icon ? iconFor(entry.icon) : null}
                {text(entry.label)}
                {text(entry.shortcut) ? (
                  <ContextMenuShortcut>
                    {text(entry.shortcut)}
                  </ContextMenuShortcut>
                ) : null}
              </ContextMenuItem>
            </React.Fragment>
          ),
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
}

export function MenubarAdapter({ props, dispatch }: AdapterProps) {
  return (
    <Menubar className={className(props)}>
      {list(props.menus).map((menu, menuIndex) => (
        <MenubarMenu key={`${text(menu.label)}-${menuIndex}`}>
          <MenubarTrigger>{text(menu.label)}</MenubarTrigger>
          <MenubarContent>
            {list(menu.items).map((entry, index) =>
              entry.kind === "group" ? (
                <MenubarGroup key={`group-${index}`}>
                  {list(entry.items).map((item, itemIndex) => {
                    const value = text(item.value) ?? "";
                    return (
                      <MenubarItem
                        key={`${value}-${itemIndex}`}
                        disabled={boolean(item.disabled)}
                        variant={
                          boolean(item.destructive) ? "destructive" : "default"
                        }
                        onSelect={() => dispatch("select", { value })}
                      >
                        {item.icon ? iconFor(item.icon) : null}
                        {text(item.label)}
                        {text(item.shortcut) ? (
                          <MenubarShortcut>
                            {text(item.shortcut)}
                          </MenubarShortcut>
                        ) : null}
                      </MenubarItem>
                    );
                  })}
                </MenubarGroup>
              ) : (
                <React.Fragment key={index}>
                  {boolean(entry.separatorBefore) ? <MenubarSeparator /> : null}
                  <MenubarItem
                    disabled={boolean(entry.disabled)}
                    variant={
                      boolean(entry.destructive) ? "destructive" : "default"
                    }
                    onSelect={() =>
                      dispatch("select", { value: text(entry.value) ?? "" })
                    }
                  >
                    {entry.icon ? iconFor(entry.icon) : null}
                    {text(entry.label)}
                    {text(entry.shortcut) ? (
                      <MenubarShortcut>{text(entry.shortcut)}</MenubarShortcut>
                    ) : null}
                  </MenubarItem>
                </React.Fragment>
              ),
            )}
          </MenubarContent>
        </MenubarMenu>
      ))}
    </Menubar>
  );
}

function navigationItems(
  items: MenuEntry[],
  navigate: (path: string) => void,
): React.ReactNode {
  return items.map((item, index) => {
    const label = text(item.label) ?? "";
    const href = text(item.href);
    const children = list(item.children);
    if (children.length > 0) {
      return (
        <NavigationMenuItem key={`${label}-${index}`}>
          <NavigationMenuTrigger>{label}</NavigationMenuTrigger>
          <NavigationMenuContent>
            <ul className="grid w-48 gap-1 p-2">
              {children.map((child, childIndex) => {
                const childHref = text(child.href);
                return (
                  <li key={`${text(child.label)}-${childIndex}`}>
                    <NavigationMenuLink
                      href={childHref ?? "#"}
                      onClick={(event) => {
                        if (childHref?.startsWith("/")) {
                          event.preventDefault();
                          navigate(childHref);
                        }
                      }}
                    >
                      {text(child.label)}
                    </NavigationMenuLink>
                  </li>
                );
              })}
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>
      );
    }
    return (
      <NavigationMenuItem key={`${label}-${index}`}>
        <NavigationMenuLink
          href={href ?? "#"}
          onClick={(event) => {
            if (href?.startsWith("/")) {
              event.preventDefault();
              navigate(href);
            }
          }}
        >
          {label}
        </NavigationMenuLink>
      </NavigationMenuItem>
    );
  });
}

export function NavigationMenuAdapter({ props, navigate }: AdapterProps) {
  return (
    <NavigationMenu className={className(props)}>
      <NavigationMenuList>
        {navigationItems(list(props.items), navigate)}
      </NavigationMenuList>
    </NavigationMenu>
  );
}

function commandItems(
  entries: MenuEntry[],
  dispatch: AdapterProps["dispatch"],
): React.ReactNode {
  return entries.map((entry, index) => {
    if (entry.kind === "group") {
      return (
        <CommandGroup key={`group-${index}`} heading={text(entry.label)}>
          {commandItems(list(entry.items), dispatch)}
        </CommandGroup>
      );
    }
    const value = text(entry.value) ?? "";
    return (
      <CommandItem
        key={`${value}-${index}`}
        value={value}
        disabled={boolean(entry.disabled)}
        onSelect={() => dispatch("select", { value })}
      >
        {entry.icon ? iconFor(entry.icon) : null}
        {text(entry.label)}
        {text(entry.shortcut) ? (
          <CommandShortcut>{text(entry.shortcut)}</CommandShortcut>
        ) : null}
      </CommandItem>
    );
  });
}

export function CommandAdapter({
  props,
  slots,
  events,
  dispatch,
}: AdapterProps) {
  const palette = (
    <Command className={className(props)}>
      <CommandInput
        placeholder={text(props.placeholder) ?? "type a command..."}
      />
      <CommandList>
        <CommandEmpty>
          {text(props.emptyText) ?? "no results found"}
        </CommandEmpty>
        {commandItems(list(props.items), dispatch)}
      </CommandList>
    </Command>
  );
  const trigger = triggerRender(slots.trigger);
  if (!trigger) return palette;
  return (
    <Dialog {...openProps(props, events, dispatch)}>
      <DialogTrigger render={trigger} />
      <DialogContent className="p-0" showCloseButton={false}>
        <DialogTitle className="sr-only">
          {text(props.title) ?? "command palette"}
        </DialogTitle>
        {text(props.description) ? (
          <DialogDescription className="sr-only">
            {text(props.description)}
          </DialogDescription>
        ) : null}
        {palette}
      </DialogContent>
    </Dialog>
  );
}
