declare module "lucide-react" {
  import * as React from "react"

  export interface LucideProps extends React.SVGProps<SVGSVGElement> {
    size?: string | number
    absoluteStrokeWidth?: boolean
  }

  export type LucideIcon = React.ForwardRefExoticComponent<
    Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>
  >

  export const AlertTriangle: LucideIcon
  export const ArrowLeft: LucideIcon
  export const ArrowRight: LucideIcon
  export const BarChart3: LucideIcon
  export const Bell: LucideIcon
  export const Bot: LucideIcon
  export const Building2: LucideIcon
  export const Calculator: LucideIcon
  export const Calendar: LucideIcon
  export const Check: LucideIcon
  export const CheckCircle2: LucideIcon
  export const CheckIcon: LucideIcon
  export const ChevronDown: LucideIcon
  export const ChevronDownIcon: LucideIcon
  export const ChevronLeft: LucideIcon
  export const ChevronLeftIcon: LucideIcon
  export const ChevronRight: LucideIcon
  export const ChevronRightIcon: LucideIcon
  export const ChevronUp: LucideIcon
  export const ChevronUpIcon: LucideIcon
  export const CircleIcon: LucideIcon
  export const CloudUpload: LucideIcon
  export const DollarSign: LucideIcon
  export const Download: LucideIcon
  export const Eye: LucideIcon
  export const EyeOff: LucideIcon
  export const FileImage: LucideIcon
  export const FileSearch: LucideIcon
  export const GripVerticalIcon: LucideIcon
  export const HelpCircle: LucideIcon
  export const LayoutDashboard: LucideIcon
  export const LayoutGrid: LucideIcon
  export const List: LucideIcon
  export const Loader2: LucideIcon
  export const Loader2Icon: LucideIcon
  export const Lock: LucideIcon
  export const LogOut: LucideIcon
  export const Mail: LucideIcon
  export const MessageSquare: LucideIcon
  export const MinusIcon: LucideIcon
  export const MoreHorizontal: LucideIcon
  export const MoreHorizontalIcon: LucideIcon
  export const PanelLeftIcon: LucideIcon
  export const Pencil: LucideIcon
  export const PlusCircle: LucideIcon
  export const Receipt: LucideIcon
  export const RefreshCw: LucideIcon
  export const RotateCcw: LucideIcon
  export const Save: LucideIcon
  export const Search: LucideIcon
  export const SearchIcon: LucideIcon
  export const Send: LucideIcon
  export const Settings: LucideIcon
  export const Tag: LucideIcon
  export const Trash2: LucideIcon
  export const TrendingDown: LucideIcon
  export const TrendingUp: LucideIcon
  export const Upload: LucideIcon
  export const User: LucideIcon
  export const UserRound: LucideIcon
  export const X: LucideIcon
  export const XIcon: LucideIcon
  export const ZoomIn: LucideIcon
  export const ZoomOut: LucideIcon
}
