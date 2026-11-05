import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Bell,
  Calendar,
  ChartColumn,
  ChartLine,
  ChartPie,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  CircleAlert,
  CircleCheck,
  Clock,
  Code,
  Command,
  Copy,
  Database,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  File,
  Filter,
  Folder,
  Github,
  Heart,
  House,
  Image as ImageIcon,
  Info,
  Loader2,
  LoaderCircle,
  Lock,
  LogOut,
  Mail,
  Menu,
  Minus,
  Monitor,
  Moon,
  MoreHorizontal,
  MoreVertical,
  PanelLeft,
  PanelRight,
  Pause,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  Server,
  Settings,
  SlidersHorizontal,
  Sparkles,
  Star,
  Sun,
  Table,
  Terminal,
  Trash2,
  TriangleAlert,
  Upload,
  User,
  Users,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";
import * as React from "react";

const icons: Record<string, LucideIcon> = {
  "arrow-down": ArrowDown,
  "arrow-left": ArrowLeft,
  "arrow-right": ArrowRight,
  "arrow-up": ArrowUp,
  bell: Bell,
  calendar: Calendar,
  "chart-bar": ChartColumn,
  "chart-line": ChartLine,
  "chart-pie": ChartPie,
  check: Check,
  "chevron-down": ChevronDown,
  "chevron-left": ChevronLeft,
  "chevron-right": ChevronRight,
  "chevron-up": ChevronUp,
  "circle-alert": CircleAlert,
  "circle-check": CircleCheck,
  clock: Clock,
  code: Code,
  command: Command,
  copy: Copy,
  database: Database,
  download: Download,
  edit: Pencil,
  "external-link": ExternalLink,
  eye: Eye,
  "eye-off": EyeOff,
  file: File,
  filter: Filter,
  folder: Folder,
  github: Github,
  heart: Heart,
  home: House,
  image: ImageIcon,
  info: Info,
  "loader-2": Loader2,
  "loader-circle": LoaderCircle,
  lock: Lock,
  "log-out": LogOut,
  mail: Mail,
  menu: Menu,
  minus: Minus,
  monitor: Monitor,
  moon: Moon,
  "more-horizontal": MoreHorizontal,
  "more-vertical": MoreVertical,
  "panel-left": PanelLeft,
  "panel-right": PanelRight,
  pause: Pause,
  pencil: Pencil,
  play: Play,
  plus: Plus,
  "refresh-cw": RefreshCw,
  "rotate-ccw": RotateCcw,
  save: Save,
  search: Search,
  server: Server,
  settings: Settings,
  "sliders-horizontal": SlidersHorizontal,
  sparkles: Sparkles,
  star: Star,
  sun: Sun,
  table: Table,
  terminal: Terminal,
  trash: Trash2,
  "triangle-alert": TriangleAlert,
  upload: Upload,
  user: User,
  users: Users,
  x: X,
  zap: Zap,
};

type IconData = {
  lucideVersion: string;
  names: string[];
  data: string[];
  index: Record<string, number>;
};

let iconDataPromise: Promise<IconData> | null = null;
const loadedIconData: { value: IconData | null } = { value: null };

function loadIconData(): Promise<IconData> {
  iconDataPromise ??= import("./icon-data.generated.json").then((module) => {
    loadedIconData.value = module.default as IconData;
    return loadedIconData.value;
  });
  return iconDataPromise;
}

function useLazyIcon(name: string): string | null | undefined {
  const [markup, setMarkup] = React.useState<string | null | undefined>(() => {
    const data = loadedIconData.value;
    if (!data) return undefined;
    const index = data.index[name];
    return index === undefined ? null : data.data[index];
  });

  React.useEffect(() => {
    if (icons[name]) return;
    let active = true;
    void loadIconData()
      .then((data) => {
        if (!active) return;
        const index = data.index[name];
        setMarkup(index === undefined ? null : data.data[index]);
      })
      .catch(() => {
        if (active) setMarkup(null);
      });
    return () => {
      active = false;
    };
  }, [name]);

  return markup;
}

export function ShadletIcon({
  name,
  size = 16,
  strokeWidth = 2,
  color,
  label,
  className,
}: {
  name: string;
  size?: number | string;
  strokeWidth?: number;
  color?: string;
  label?: string;
  className?: string;
}) {
  const Icon = icons[name];
  const markup = useLazyIcon(name);

  if (Icon) {
    return (
      <Icon
        aria-hidden={label ? undefined : true}
        aria-label={label}
        className={className}
        width={size}
        height={size}
        strokeWidth={strokeWidth}
        color={color}
      />
    );
  }

  if (markup === undefined) {
    return (
      <svg
        aria-busy="true"
        aria-hidden={label ? undefined : true}
        aria-label={label}
        className={className}
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
      />
    );
  }

  if (markup === null) {
    throw new Error(`unknown icon: ${name}`);
  }

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden={label ? undefined : true}
      aria-label={label}
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      color={color}
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function iconFor(name: unknown): React.ReactNode {
  if (typeof name !== "string" || !name) return null;
  return <ShadletIcon name={name} />;
}
