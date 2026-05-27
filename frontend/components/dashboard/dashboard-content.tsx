"use client"

import { useEffect, useState } from "react"
import {
  Calculator,
  DollarSign,
  Loader2,
  Receipt,
  TrendingDown,
  TrendingUp,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { apiGetDashboard, apiGetReceipts } from "@/lib/api"
import { AnimatedSection } from "@/components/ui/animated-section"

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("vi-VN").format(value) + " đ"
}

interface DashboardData {
  stats: {
    total_receipts: number
    total_spending: number
    this_month_spending: number
    avg_per_receipt: number
    month_change_percent: number | null
  }
  category_spending: { name: string; value: number; color: string }[]
  monthly_spending: { month: string; amount: number }[]
}

interface RecentReceipt {
  id: number
  receipt_date: string | null
  supplier_name: string | null
  category_name: string | null
  total_amount: number
  status: string
  created_at: string
}

const statusStyles: Record<string, string> = {
  "Đã duyệt": "bg-emerald-100 text-emerald-700",
  "Chờ duyệt": "bg-amber-100 text-amber-700",
  "Từ chối": "bg-red-100 text-red-700",
}

export function DashboardContent() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [recentReceipts, setRecentReceipts] = useState<RecentReceipt[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    async function fetchData() {
      try {
        const [dashData, receipts] = await Promise.all([
          apiGetDashboard().catch(() => null),
          apiGetReceipts().catch(() => []),
        ])
        if (!active) return
        if (dashData) setDashboard(dashData)
        setRecentReceipts(Array.isArray(receipts) ? receipts.slice(0, 5) : [])
      } catch (err) {
        console.error("Không tải được dữ liệu tổng quan:", err)
      } finally {
        if (active) setLoading(false)
      }
    }
    fetchData()
    return () => { active = false }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const stats = dashboard?.stats
  const statCards = [
    {
      title: "Tổng hóa đơn",
      value: stats?.total_receipts?.toLocaleString("vi-VN") ?? "0",
      icon: Receipt,
      iconBg: "bg-indigo-100",
      iconColor: "text-indigo-600",
    },
    {
      title: "Tổng chi tiêu",
      value: formatCurrency(stats?.total_spending ?? 0),
      icon: DollarSign,
      iconBg: "bg-emerald-100",
      iconColor: "text-emerald-600",
    },
    {
      title: "Tháng này",
      value: formatCurrency(stats?.this_month_spending ?? 0),
      change: stats?.month_change_percent != null ? `${stats.month_change_percent > 0 ? "+" : ""}${stats.month_change_percent}%` : undefined,
      trend: stats?.month_change_percent != null ? (stats.month_change_percent >= 0 ? "up" : "down") : undefined,
      icon: TrendingUp,
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
    },
    {
      title: "Trung bình/hóa đơn",
      value: formatCurrency(stats?.avg_per_receipt ?? 0),
      icon: Calculator,
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
    },
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon
          return (
            <AnimatedSection key={stat.title} delay={index * 100}>
            <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                    <p className="mt-2 text-2xl font-bold text-card-foreground">{stat.value}</p>
                    {stat.change && (
                      <div className="mt-1 flex items-center gap-1 text-xs">
                        {stat.trend === "up" ? (
                          <TrendingUp className="h-3 w-3 text-emerald-500" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-red-500" />
                        )}
                        <span className={stat.trend === "up" ? "text-emerald-500" : "text-red-500"}>
                          {stat.change}
                        </span>
                        <span className="text-muted-foreground">so với tháng trước</span>
                      </div>
                    )}
                  </div>
                  <div className={`rounded-xl p-3 ${stat.iconBg}`}>
                    <Icon className={`h-6 w-6 ${stat.iconColor}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
            </AnimatedSection>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <AnimatedSection delay={100} direction="left">
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Chi tiêu theo danh mục</CardTitle>
          </CardHeader>
          <CardContent>
            {(dashboard?.category_spending?.length ?? 0) > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={dashboard!.category_spending} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {dashboard!.category_spending.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[280px] items-center justify-center text-muted-foreground">Chưa có dữ liệu</div>
            )}
          </CardContent>
        </Card>

        </AnimatedSection>
        <AnimatedSection delay={200} direction="right">
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Chi tiêu theo tháng</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={dashboard?.monthly_spending ?? []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `${(Number(value) / 1000000).toFixed(1)}M`} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        </AnimatedSection>
      </div>

      <AnimatedSection delay={100}>
      <Card className="border-border bg-card shadow-sm">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Hóa đơn gần đây</CardTitle>
        </CardHeader>
        <CardContent>
          {recentReceipts.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">Chưa có hóa đơn nào. Hãy tải hóa đơn đầu tiên!</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-muted-foreground">
                    <th className="pb-3 font-medium">Ngày</th>
                    <th className="pb-3 font-medium">Nhà cung cấp</th>
                    <th className="pb-3 font-medium">Danh mục</th>
                    <th className="pb-3 font-medium text-right">Số tiền</th>
                    <th className="pb-3 font-medium">Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {recentReceipts.map((receipt) => (
                    <tr key={receipt.id} className="border-b last:border-0">
                      <td className="py-3 text-sm">{receipt.receipt_date || new Date(receipt.created_at).toLocaleDateString("vi-VN")}</td>
                      <td className="py-3 text-sm font-medium">{receipt.supplier_name || "—"}</td>
                      <td className="py-3 text-sm">{receipt.category_name || "—"}</td>
                      <td className="py-3 text-right text-sm font-semibold text-indigo-600">{formatCurrency(receipt.total_amount)}</td>
                      <td className="py-3">
                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[receipt.status] || "bg-gray-100 text-gray-700"}`}>
                          {receipt.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
      </AnimatedSection>
    </div>
  )
}
