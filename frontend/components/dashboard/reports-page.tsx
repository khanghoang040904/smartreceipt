"use client"

import { useEffect, useState } from "react"
import {
  BarChart3,
  Calendar,
  Download,
  FileSpreadsheet,
  Loader2,
  TrendingDown,
  TrendingUp,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
import { apiGetDashboard, apiGetReceipts, apiExportCSV } from "@/lib/api"
import { AnimatedSection } from "@/components/ui/animated-section"

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("vi-VN").format(value) + " đ"

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

interface ReceiptItem {
  id: number
  receipt_date: string | null
  supplier_name: string | null
  category_name: string | null
  total_amount: number
  status: string
  created_at: string
}

export function ReportsPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [receipts, setReceipts] = useState<ReceiptItem[]>([])
  const [loading, setLoading] = useState(true)
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  const fetchData = async () => {
    setLoading(true)
    try {
      const [dashData, receiptData] = await Promise.all([
        apiGetDashboard(),
        apiGetReceipts({ date_from: dateFrom || undefined, date_to: dateTo || undefined }),
      ])
      setDashboard(dashData)
      setReceipts(receiptData)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleFilter = () => fetchData()

  const topSuppliers = receipts.reduce((acc, r) => {
    const name = r.supplier_name || "Không rõ"
    acc[name] = (acc[name] || 0) + r.total_amount
    return acc
  }, {} as Record<string, number>)

  const topSuppliersData = Object.entries(topSuppliers)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, value]) => ({ name, value }))

  const statusCounts = receipts.reduce((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const handleExportCSV = () => apiExportCSV()

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const stats = dashboard?.stats

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Báo cáo & Thống kê</h2>
          <p className="text-sm text-muted-foreground">Phân tích chi tiêu chi tiết và xuất dữ liệu</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExportCSV} className="gap-2">
            <FileSpreadsheet className="h-4 w-4" />
            Xuất CSV
          </Button>
        </div>
      </div>

      {/* Date filter */}
      <Card className="border-border bg-card shadow-sm">
        <CardContent className="flex flex-wrap items-end gap-4 p-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <label className="text-sm font-medium">Từ ngày</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Đến ngày</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <Button onClick={handleFilter} className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Lọc
          </Button>
        </CardContent>
      </Card>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AnimatedSection delay={0}>
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Tổng hóa đơn</p>
            <p className="mt-1 text-2xl font-bold">{stats?.total_receipts?.toLocaleString("vi-VN") ?? "0"}</p>
          </CardContent>
        </Card>
        </AnimatedSection>
        <AnimatedSection delay={100}>
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Tổng chi tiêu</p>
            <p className="mt-1 text-2xl font-bold text-indigo-600">{formatCurrency(stats?.total_spending ?? 0)}</p>
          </CardContent>
        </Card>
        </AnimatedSection>
        <AnimatedSection delay={200}>
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Tháng này</p>
            <p className="mt-1 text-2xl font-bold">{formatCurrency(stats?.this_month_spending ?? 0)}</p>
            {stats?.month_change_percent != null && (
              <div className="mt-1 flex items-center gap-1 text-xs">
                {stats.month_change_percent >= 0 ? (
                  <TrendingUp className="h-3 w-3 text-red-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-emerald-500" />
                )}
                <span className={stats.month_change_percent >= 0 ? "text-red-500" : "text-emerald-500"}>
                  {stats.month_change_percent > 0 ? "+" : ""}{stats.month_change_percent}%
                </span>
              </div>
            )}
          </CardContent>
        </Card>
        </AnimatedSection>
        <AnimatedSection delay={300}>
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Trung bình/hóa đơn</p>
            <p className="mt-1 text-2xl font-bold">{formatCurrency(stats?.avg_per_receipt ?? 0)}</p>
          </CardContent>
        </Card>
        </AnimatedSection>
      </div>

      {/* Status summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Đã duyệt</p>
            <p className="mt-1 text-2xl font-bold text-emerald-600">{statusCounts["Đã duyệt"] || 0}</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Chờ duyệt</p>
            <p className="mt-1 text-2xl font-bold text-amber-600">{statusCounts["Chờ duyệt"] || 0}</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Từ chối</p>
            <p className="mt-1 text-2xl font-bold text-red-600">{statusCounts["Từ chối"] || 0}</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
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

      {/* Top suppliers */}
      {topSuppliersData.length > 0 && (
        <AnimatedSection delay={100}>
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Top nhà cung cấp</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topSuppliersData.map((item, i) => {
                const maxValue = topSuppliersData[0]?.value || 1
                const percent = Math.round((item.value / maxValue) * 100)
                return (
                  <div key={item.name} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{i + 1}. {item.name}</span>
                      <span className="font-semibold text-indigo-600">{formatCurrency(item.value)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div className="h-full rounded-full bg-indigo-500 transition-all" style={{ width: `${percent}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
        </AnimatedSection>
      )}
    </div>
  )
}
