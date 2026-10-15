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
  if (!Icon) {
    return (
      <CircleAlert
        aria-label={`unknown icon: ${name}`}
        className={className}
        width={size}
        height={size}
        strokeWidth={strokeWidth}
      />
    );
  }
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

// eslint-disable-next-line react-refresh/only-export-components
export function iconFor(name: unknown): React.ReactNode {
  if (typeof name !== "string" || !name) return null;
  return <ShadletIcon name={name} />;
}
