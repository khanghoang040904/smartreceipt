"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Loader2,
  Pencil,
  Receipt,
  Save,
  Trash2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiDeleteBudget, apiGetBudgets, apiUpsertBudget, BudgetSummary } from "@/lib/api"
import { cn } from "@/lib/utils"

const moneyFormatter = new Intl.NumberFormat("vi-VN")
const formatVND = (value: number) => `${moneyFormatter.format(Math.round(value || 0))} đ`
const formatNumber = (value: number) => moneyFormatter.format(Math.round(value || 0))
const parseMoney = (value: string) => Number(value.replace(/[^\d]/g, "")) || 0

function currentMonth() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
}

function statusLabel(status: string) {
  if (status === "over") return "Vượt ngân sách"
  if (status === "warning") return "Sắp vượt"
  if (status === "ok") return "Trong giới hạn"
  return "Chưa đặt"
}

function statusClass(status: string) {
  if (status === "over") return "bg-red-50 text-red-700"
  if (status === "warning") return "bg-amber-50 text-amber-700"
  if (status === "ok") return "bg-emerald-50 text-emerald-700"
  return "bg-muted text-muted-foreground"
}

export function BudgetPage() {
  const [month, setMonth] = useState(currentMonth())
  const [summary, setSummary] = useState<BudgetSummary | null>(null)
  const [drafts, setDrafts] = useState<Record<number, number>>({})
  const [editing, setEditing] = useState<Record<number, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState<number | null>(null)
  const [error, setError] = useState("")

  const usagePercent = useMemo(() => {
    if (!summary || summary.total_budget <= 0) return 0
    return Math.min(100, Math.round((summary.total_spent / summary.total_budget) * 100))
  }, [summary])

  const fetchBudgets = async (selectedMonth = month) => {
    setLoading(true)
    setError("")
    try {
      const data = await apiGetBudgets(selectedMonth)
      setSummary(data)
      setDrafts(Object.fromEntries(data.categories.map((item) => [item.category_id, item.budget_amount])))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tải được ngân sách")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBudgets(month)
  }, [month])

  const saveBudget = async (categoryId: number) => {
    setSavingId(categoryId)
    setError("")
    try {
      await apiUpsertBudget({
        category_id: categoryId,
        month,
        amount: drafts[categoryId] || 0,
      })
      setEditing((prev) => ({ ...prev, [categoryId]: false }))
      await fetchBudgets(month)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được ngân sách")
    } finally {
      setSavingId(null)
    }
  }

  const removeBudget = async (budgetId: number) => {
    setError("")
    try {
      await apiDeleteBudget(budgetId)
      await fetchBudgets(month)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không xóa được ngân sách")
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Ngân sách</h2>
          <p className="text-sm text-muted-foreground">Theo dõi hạn mức chi tiêu theo từng danh mục</p>
        </div>
        <label className="flex items-center gap-2 text-sm">
          Tháng
          <input
            type="month"
            value={month}
            onChange={(event) => setMonth(event.target.value)}
            className="rounded-lg border border-input bg-background px-3 py-2"
          />
        </label>
      </div>

      {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">Ngân sách tháng</p>
              <p className="mt-1 text-xl font-semibold">{formatVND(summary?.total_budget || 0)}</p>
            </div>
            <DollarSign className="h-8 w-8 text-primary" />
          </CardContent>
        </Card>
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">Đã chi</p>
              <p className="mt-1 text-xl font-semibold">{formatVND(summary?.total_spent || 0)}</p>
            </div>
            <Receipt className="h-8 w-8 text-indigo-600" />
          </CardContent>
        </Card>
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">Tỷ lệ sử dụng</p>
              <p className="text-sm font-medium">{usagePercent}%</p>
            </div>
            <div className="mt-3 h-2 rounded-full bg-muted">
              <div
                className={cn("h-2 rounded-full", usagePercent >= 100 ? "bg-red-500" : usagePercent >= 80 ? "bg-amber-500" : "bg-emerald-500")}
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border bg-card shadow-sm">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Ngân sách theo danh mục</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-3 font-medium">Danh mục</th>
                  <th className="pb-3 font-medium text-right">Ngân sách</th>
                  <th className="pb-3 font-medium text-right">Đã chi</th>
                  <th className="pb-3 font-medium text-right">Còn lại</th>
                  <th className="pb-3 font-medium">Trạng thái</th>
                  <th className="pb-3 font-medium text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {(summary?.categories || []).map((item) => {
                  const isEditing = editing[item.category_id] || item.budget_id == null
                  return (
                    <tr key={item.category_id} className="border-b last:border-0">
                      <td className="py-3 font-medium">{item.category_name}</td>
                      <td className="py-3 text-right">
                        {isEditing ? (
                          <input
                            type="text"
                            inputMode="numeric"
                            value={formatNumber(drafts[item.category_id] || 0)}
                            onChange={(event) => setDrafts((prev) => ({ ...prev, [item.category_id]: parseMoney(event.target.value) }))}
                            className="w-32 rounded border border-input bg-background px-2 py-1 text-right"
                          />
                        ) : (
                          formatVND(item.budget_amount)
                        )}
                      </td>
                      <td className="py-3 text-right">{formatVND(item.spent_amount)}</td>
                      <td className={cn("py-3 text-right font-medium", item.remaining_amount < 0 ? "text-red-600" : "text-foreground")}>
                        {formatVND(item.remaining_amount)}
                      </td>
                      <td className="py-3">
                        <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", statusClass(item.status))}>
                          {item.status === "ok" ? <CheckCircle2 className="h-3.5 w-3.5" /> : item.status !== "unset" ? <AlertTriangle className="h-3.5 w-3.5" /> : null}
                          {statusLabel(item.status)} {item.budget_amount > 0 ? `(${Math.round(item.usage_percent)}%)` : ""}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <div className="flex justify-end gap-1">
                          {isEditing ? (
                            <Button size="sm" onClick={() => saveBudget(item.category_id)} disabled={savingId === item.category_id} className="gap-1">
                              {savingId === item.category_id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                              Lưu
                            </Button>
                          ) : (
                            <Button size="sm" variant="outline" onClick={() => setEditing((prev) => ({ ...prev, [item.category_id]: true }))} className="gap-1">
                              <Pencil className="h-3.5 w-3.5" />
                              Sửa
                            </Button>
                          )}
                          {item.budget_id && (
                            <Button size="sm" variant="outline" onClick={() => removeBudget(item.budget_id!)} className="gap-1 text-red-600 hover:text-red-700">
                              <Trash2 className="h-3.5 w-3.5" />
                              Xóa
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
