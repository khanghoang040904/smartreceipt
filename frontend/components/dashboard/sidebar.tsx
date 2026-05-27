"use client"

import {
  LayoutDashboard,
  Upload,
  List,
  BarChart3,
  MessageSquare,
  Receipt,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"

interface SidebarProps {
  activeItem: string
  onNavigate: (item: string) => void
  isCollapsed: boolean
  onToggle: () => void
  userName?: string
  userEmail?: string
  onLogout?: () => void
}

const navItems = [
  { id: "dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { id: "upload", label: "Tải hóa đơn", icon: Upload },
  { id: "history", label: "Lịch sử hóa đơn", icon: List },
  { id: "chat", label: "Trợ lý", icon: MessageSquare },
  { id: "reports", label: "Báo cáo", icon: BarChart3 },
]

export function Sidebar({ activeItem, onNavigate, isCollapsed, onToggle, userName = "Người dùng", userEmail = "", onLogout }: SidebarProps) {
  const initials = userName.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col bg-sidebar text-sidebar-foreground transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-primary">
            <Receipt className="h-4 w-4 text-sidebar-primary-foreground" />
          </div>
          <span className={cn("text-lg font-semibold whitespace-nowrap transition-opacity duration-200", isCollapsed ? "opacity-0" : "opacity-100")}>
            SmartReceipt
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className={cn(
            "h-8 w-8 shrink-0 text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            isCollapsed && "absolute -right-3 top-4 rounded-full bg-sidebar border border-sidebar-border shadow-md"
          )}
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeItem === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-muted hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5 shrink-0", isActive && "text-sidebar-primary")} />
              <span className={cn("whitespace-nowrap transition-opacity duration-200", isCollapsed ? "opacity-0 w-0" : "opacity-100")}>
                {item.label}
              </span>
            </button>
          )
        })}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <div className={cn("flex items-center gap-3 rounded-lg p-2", !isCollapsed && "bg-sidebar-accent/30")}>
          <Avatar className="h-9 w-9 shrink-0">
            <AvatarFallback className="bg-sidebar-primary text-sidebar-primary-foreground text-sm">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className={cn("flex-1 overflow-hidden transition-opacity duration-200", isCollapsed ? "opacity-0 w-0" : "opacity-100")}>
            <p className="truncate text-sm font-medium">{userName}</p>
            <p className="truncate text-xs text-sidebar-muted">{userEmail}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          onClick={onLogout}
          className={cn(
            "mt-2 w-full justify-start gap-3 text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground",
            isCollapsed && "justify-center px-0"
          )}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          <span className={cn("whitespace-nowrap transition-opacity duration-200", isCollapsed ? "opacity-0 w-0 hidden" : "opacity-100")}>
            Đăng xuất
          </span>
        </Button>
      </div>
    </aside>
  )
}
