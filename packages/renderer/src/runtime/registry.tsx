import * as React from "react";
import {
  AlertAdapter,
  AspectRatioAdapter,
  AvatarAdapter,
  BadgeAdapter,
  BoxAdapter,
  CodeBlockAdapter,
  ButtonGroupAdapter,
  EmptyAdapter,
  GridAdapter,
  HeadingAdapter,
  IconAdapter,
  InputGroupAdapter,
  ItemAdapter,
  KbdAdapter,
  LinkAdapter,
  MarkerAdapter,
  ProgressAdapter,
  ScrollAreaAdapter,
  SeparatorAdapter,
  SkeletonAdapter,
  SpinnerAdapter,
  TextAdapter,
  ThemeToggleAdapter,
  ToggleAdapter,
  ToggleGroupAdapter,
} from "@/shadlet/adapters/basic";
import {
  AccordionAdapter,
  CardAdapter,
  CollapsibleAdapter,
  DataTableAdapter,
  ResizableAdapter,
  TableAdapter,
} from "@/shadlet/adapters/display";
import {
  ButtonAdapter,
  CheckboxAdapter,
  ComboboxAdapter,
  FieldAdapter,
  FormAdapter,
  InputAdapter,
  InputOTPAdapter,
  LabelAdapter,
  NativeSelectAdapter,
  RadioGroupAdapter,
  SelectAdapter,
  SliderAdapter,
  SwitchAdapter,
  TextareaAdapter,
} from "@/shadlet/adapters/forms";
import {
  BreadcrumbAdapter,
  PaginationAdapter,
  SidebarAdapter,
  TabsAdapter,
} from "@/shadlet/adapters/navigation";
import {
  AlertDialogAdapter,
  CommandAdapter,
  ContextMenuAdapter,
  DialogAdapter,
  DrawerAdapter,
  DropdownMenuAdapter,
  HoverCardAdapter,
  MenubarAdapter,
  NavigationMenuAdapter,
  PopoverAdapter,
  SheetAdapter,
  TooltipAdapter,
} from "@/shadlet/adapters/overlays";
import { DirectionAdapter, ToastAdapter } from "@/shadlet/adapters/feedback";
import type { AdapterProps } from "@/shadlet/types";

const ChartAdapter = React.lazy(() =>
  import("@/shadlet/adapters/chart").then((module) => ({
    default: module.ChartAdapter,
  })),
);

const CarouselAdapter = React.lazy(() =>
  import("@/shadlet/adapters/carousel").then((module) => ({
    default: module.CarouselAdapter,
  })),
);

const CalendarAdapter = React.lazy(() =>
  import("@/shadlet/adapters/calendar").then((module) => ({
    default: module.CalendarAdapter,
  })),
);

const DatePickerAdapter = React.lazy(() =>
  import("@/shadlet/adapters/calendar").then((module) => ({
    default: module.DatePickerAdapter,
  })),
);

export type Adapter = React.ComponentType<AdapterProps>;

const builtinRegistry = new Map<string, Adapter>(
  Object.entries({
    Box: BoxAdapter,
    Row: BoxAdapter,
    Column: BoxAdapter,
    Stack: BoxAdapter,
    Wrap: BoxAdapter,
    Container: BoxAdapter,
    Center: BoxAdapter,
    Spacer: BoxAdapter,
    Positioned: BoxAdapter,
    Expanded: BoxAdapter,
    SizedBox: BoxAdapter,
    Grid: GridAdapter,
    GridItem: BoxAdapter,
    ScrollArea: ScrollAreaAdapter,

    Text: TextAdapter,
    Heading: HeadingAdapter,
    Link: LinkAdapter,
    Icon: IconAdapter,
    Code: TextAdapter,
    CodeBlock: CodeBlockAdapter,
    Kbd: KbdAdapter,
    Marker: MarkerAdapter,
    Separator: SeparatorAdapter,
    Skeleton: SkeletonAdapter,
    Spinner: SpinnerAdapter,
    Badge: BadgeAdapter,
    Avatar: AvatarAdapter,
    AspectRatio: AspectRatioAdapter,
    Alert: AlertAdapter,
    Empty: EmptyAdapter,
    Item: ItemAdapter,
    Progress: ProgressAdapter,
    Toggle: ToggleAdapter,
    ToggleGroup: ToggleGroupAdapter,
    ButtonGroup: ButtonGroupAdapter,
    InputGroup: InputGroupAdapter,
    ThemeToggle: ThemeToggleAdapter,

    Button: ButtonAdapter,
    Input: InputAdapter,
    Textarea: TextareaAdapter,
    Label: LabelAdapter,
    Checkbox: CheckboxAdapter,
    Switch: SwitchAdapter,
    Slider: SliderAdapter,
    Select: SelectAdapter,
    NativeSelect: NativeSelectAdapter,
    RadioGroup: RadioGroupAdapter,
    Combobox: ComboboxAdapter,
    InputOTP: InputOTPAdapter,
    Calendar: CalendarAdapter,
    DatePicker: DatePickerAdapter,
    Form: FormAdapter,
    Field: FieldAdapter,

    Dialog: DialogAdapter,
    AlertDialog: AlertDialogAdapter,
    Sheet: SheetAdapter,
    Drawer: DrawerAdapter,
    Popover: PopoverAdapter,
    Tooltip: TooltipAdapter,
    HoverCard: HoverCardAdapter,
    DropdownMenu: DropdownMenuAdapter,
    ContextMenu: ContextMenuAdapter,
    Menubar: MenubarAdapter,
    NavigationMenu: NavigationMenuAdapter,
    Command: CommandAdapter,

    Card: CardAdapter,
    Table: TableAdapter,
    DataTable: DataTableAdapter,
    Chart: ChartAdapter,
    Carousel: CarouselAdapter,
    Accordion: AccordionAdapter,
    Collapsible: CollapsibleAdapter,
    Resizable: ResizableAdapter,

    Tabs: TabsAdapter,
    Breadcrumb: BreadcrumbAdapter,
    Pagination: PaginationAdapter,
    Sidebar: SidebarAdapter,
    Direction: DirectionAdapter,
    Toast: ToastAdapter,
  }),
);

const extensionRegistry = new Map<string, Adapter>();
const namespacePattern = /^[a-z][a-z0-9_-]{0,62}$/;
const componentPattern = /^[A-Z][A-Za-z0-9]{0,62}$/;

export function getComponentAdapter(name: string): Adapter | undefined {
  return builtinRegistry.get(name) ?? extensionRegistry.get(name);
}

export function getBuiltinComponentNames(): string[] {
  return [...builtinRegistry.keys()];
}

export function registerExtensionComponents(
  namespace: string,
  components: Record<string, Adapter>,
): () => void {
  if (!namespacePattern.test(namespace)) {
    throw new Error(`invalid extension namespace: ${namespace}`);
  }
  const entries = Object.entries(components);
  if (entries.length === 0) {
    throw new Error(
      `extension ${namespace} must register at least one component`,
    );
  }
  const registered: Array<[string, Adapter]> = [];
  for (const [componentName, adapter] of entries) {
    const typeName = `${namespace}:${componentName}`;
    if (!componentPattern.test(componentName)) {
      throw new Error(`invalid extension component name: ${componentName}`);
    }
    if (
      typeof adapter !== "function" &&
      (typeof adapter !== "object" || adapter === null)
    ) {
      throw new Error(
        `extension component ${typeName} must be a React component`,
      );
    }
    if (builtinRegistry.has(typeName) || extensionRegistry.has(typeName)) {
      throw new Error(`component type is already registered: ${typeName}`);
    }
    registered.push([typeName, adapter]);
  }

  for (const [typeName, adapter] of registered) {
    extensionRegistry.set(typeName, adapter);
  }

  return () => {
    for (const [typeName, adapter] of registered) {
      if (extensionRegistry.get(typeName) === adapter) {
        extensionRegistry.delete(typeName);
      }
    }
  };
}
