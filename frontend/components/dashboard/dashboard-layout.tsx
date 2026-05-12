"use client"

import { useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "./sidebar"
import { Navbar } from "./navbar"
import { UploadReceipt } from "./upload-receipt"
import { ReceiptHistory } from "./receipt-history"
import { ReceiptDetail } from "./receipt-detail"
import { cn } from "@/lib/utils"

const pageTitles: Record<string, string> = {
  dashboard: "Dashboard",
  upload: "Upload Receipt",
  history: "Receipt History",
  categories: "Categories",
  detail: "Chi tiết hóa đơn",
}

interface DashboardLayoutProps {
  children: ReactNode
  activeItem?: string
  onNavigate?: (item: string) => void
}

export function DashboardLayout({
  children,
  activeItem = "dashboard",
  onNavigate,
}: DashboardLayoutProps) {
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [currentPage, setCurrentPage] = useState(activeItem)
  const [selectedReceiptId, setSelectedReceiptId] = useState<number | null>(null)
  const [userName, setUserName] = useState("User")
  const [userEmail, setUserEmail] = useState("")

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    const userStr = localStorage.getItem("user")
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        setUserName(user.full_name || "User")
        setUserEmail(user.email || "")
      } catch {}
    }
  }, [router])

  const handleNavigate = (item: string) => {
    setCurrentPage(item)
    onNavigate?.(item)
  }

  const handleViewReceipt = (id: number) => {
    setSelectedReceiptId(id)
    setCurrentPage("detail")
  }

  const handleBackFromDetail = () => {
    setCurrentPage("history")
    setSelectedReceiptId(null)
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    router.push("/login")
  }

  const renderContent = () => {
    if (currentPage === "upload") return <UploadReceipt />
    if (currentPage === "history") return <ReceiptHistory onViewReceipt={handleViewReceipt} />
    if (currentPage === "detail") return <ReceiptDetail receiptId={selectedReceiptId} onBack={handleBackFromDetail} />
    return children
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        activeItem={currentPage === "detail" ? "history" : currentPage}
        onNavigate={handleNavigate}
        isCollapsed={isCollapsed}
        onToggle={() => setIsCollapsed(!isCollapsed)}
        userName={userName}
        userEmail={userEmail}
        onLogout={handleLogout}
      />
      <Navbar
        title={pageTitles[currentPage] || "Dashboard"}
        sidebarCollapsed={isCollapsed}
      />
      <main
        className={cn(
          "min-h-screen pt-16 transition-all duration-300",
          isCollapsed ? "pl-16" : "pl-64"
        )}
      >
        <div className="p-6">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}
