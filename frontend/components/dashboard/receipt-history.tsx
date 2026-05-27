"use client"

import { useState, useEffect } from "react"
import {
  Search,
  X,
  LayoutGrid,
  List,
  Eye,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Calendar,
  Receipt,
  Loader2,
  Download,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { apiGetReceipts, apiDeleteReceipt, apiUpdateReceipt, apiExportCSV } from "@/lib/api"

type ViewMode = "table" | "grid"
type StatusFilter = "all" | "Chờ duyệt" | "Đã duyệt" | "Từ chối"

interface ReceiptItem {
  id: number
  receipt_date: string | null
  supplier_name: string | null
  category_name: string | null
  total_amount: number
  status: string
  created_at: string
}

const PAGE_SIZE = 8

const formatVND = (amount: number) => amount.toLocaleString("vi-VN") + " đ"

const statusStyles: Record<string, string> = {
  "Đã duyệt": "bg-emerald-50 text-emerald-700",
  "Chờ duyệt": "bg-amber-50 text-amber-700",
  "Từ chối": "bg-red-50 text-red-600",
}

const statusFilters: { label: string; value: StatusFilter; icon: React.ElementType }[] = [
  { label: "Tất cả", value: "all", icon: Receipt },
  { label: "Chờ duyệt", value: "Chờ duyệt", icon: Clock },
  { label: "Đã duyệt", value: "Đã duyệt", icon: CheckCircle2 },
  { label: "Từ chối", value: "Từ chối", icon: XCircle },
]

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusStyles[status] || "bg-gray-50 text-gray-700")}>
      {status}
    </span>
  )
}

function ReceiptCard({ item, onView, onDelete, onApprove, onReject }: { item: ReceiptItem; onView: (id: number) => void; onDelete: (id: number) => void; onApprove: (id: number) => void; onReject: (id: number) => void }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onView(item.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          onView(item.id)
        }
      }}
      className="group flex cursor-pointer flex-col overflow-hidden rounded-xl border border-border bg-card shadow-sm transition-shadow duration-200 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring"
    >
      <div className="h-32 bg-gradient-to-br from-indigo-50 to-blue-100 flex items-center justify-center relative">
        <Receipt className="h-12 w-12 text-indigo-300" />
        <div className="absolute top-2 right-2"><StatusBadge status={item.status} /></div>
      </div>
      <div className="flex flex-col gap-2 p-4 flex-1">
        <p className="font-semibold text-foreground text-sm leading-snug line-clamp-1">{item.supplier_name || "—"}</p>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Calendar className="h-3.5 w-3.5" />
          {item.receipt_date || new Date(item.created_at).toLocaleDateString("vi-VN")}
        </div>
        {item.category_name && (
          <span className="inline-flex w-fit items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200">
            {item.category_name}
          </span>
        )}
        <p className="mt-auto pt-2 text-base font-bold text-indigo-600">{formatVND(item.total_amount)}</p>
      </div>
      <div className="flex border-t border-border divide-x divide-border">
        <button onClick={(event) => { event.stopPropagation(); onView(item.id) }} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs text-muted-foreground hover:text-indigo-600 hover:bg-indigo-50 transition-colors">
          <Eye className="h-3.5 w-3.5" /> Xem
        </button>
        {item.status === "Chờ duyệt" && (
          <>
            <button onClick={(event) => { event.stopPropagation(); onApprove(item.id) }} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs text-muted-foreground hover:text-emerald-600 hover:bg-emerald-50 transition-colors">
              <CheckCircle2 className="h-3.5 w-3.5" /> Duyệt
            </button>
            <button onClick={(event) => { event.stopPropagation(); onReject(item.id) }} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors">
              <XCircle className="h-3.5 w-3.5" /> Từ chối
            </button>
          </>
        )}
        <button onClick={(event) => { event.stopPropagation(); onDelete(item.id) }} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors">
          <Trash2 className="h-3.5 w-3.5" /> Xóa
        </button>
      </div>
    </div>
  )
}

export function ReceiptHistory({ onViewReceipt }: { onViewReceipt: (id: number) => void }) {
  const [receipts, setReceipts] = useState<ReceiptItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [viewMode, setViewMode] = useState<ViewMode>("table")
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")

  const fetchReceipts = async (searchQuery?: string) => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (searchQuery) params.search = searchQuery
      const data = await apiGetReceipts(Object.keys(params).length > 0 ? params : undefined)
      setReceipts(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReceipts(search || undefined)
  }, [])

  const handleSearch = () => {
    setPage(1)
    fetchReceipts(search || undefined)
  }

  const handleDelete = async (id: number) => {
    try {
      await apiDeleteReceipt(id)
      setReceipts((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  const handleApprove = async (id: number) => {
    try {
      await apiUpdateReceipt(id, { status: "Đã duyệt" })
      setReceipts((prev) => prev.map((r) => r.id === id ? { ...r, status: "Đã duyệt" } : r))
    } catch (err) {
      console.error(err)
    }
  }

  const handleReject = async (id: number) => {
    try {
      await apiUpdateReceipt(id, { status: "Từ chối" })
      setReceipts((prev) => prev.map((r) => r.id === id ? { ...r, status: "Từ chối" } : r))
    } catch (err) {
      console.error(err)
    }
  }

  const filteredReceipts = statusFilter === "all"
    ? receipts
    : receipts.filter((r) => r.status === statusFilter)
  const totalPages = Math.max(1, Math.ceil(filteredReceipts.length / PAGE_SIZE))
  const pagedReceipts = filteredReceipts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status filter tabs */}
      <div className="flex gap-1 rounded-lg border border-border bg-muted/30 p-1">
        {statusFilters.map((filter) => {
          const Icon = filter.icon
          const count = filter.value === "all"
            ? receipts.length
            : receipts.filter((r) => r.status === filter.value).length
          return (
            <button
              key={filter.value}
              onClick={() => { setStatusFilter(filter.value); setPage(1) }}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                statusFilter === filter.value
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {filter.label}
            </button>
          )
        })}
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Tìm theo nhà cung cấp..."
              className="h-9 w-64 rounded-lg border border-input bg-background pl-9 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            {search && (
              <button onClick={() => { setSearch(""); fetchReceipts(undefined) }} className="absolute right-2 top-1/2 -translate-y-1/2">
                <X className="h-4 w-4 text-muted-foreground" />
              </button>
            )}
          </div>
          <button onClick={handleSearch} className="h-9 px-3 rounded-lg bg-primary text-primary-foreground text-sm hover:bg-primary/90">
            Tìm
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={() => apiExportCSV()} className="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-border bg-background text-sm hover:bg-muted">
            <Download className="h-4 w-4" />
            Xuất CSV
          </button>
          <div className="flex rounded-lg border border-border overflow-hidden">
            <button onClick={() => setViewMode("table")} className={cn("p-2", viewMode === "table" ? "bg-primary text-primary-foreground" : "bg-background hover:bg-muted")}>
              <List className="h-4 w-4" />
            </button>
            <button onClick={() => setViewMode("grid")} className={cn("p-2", viewMode === "grid" ? "bg-primary text-primary-foreground" : "bg-background hover:bg-muted")}>
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {filteredReceipts.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <Receipt className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-lg font-medium">{statusFilter === "all" ? "Chưa có hóa đơn nào" : `Không có hóa đơn "${statusFilter}"`}</p>
          <p className="text-sm mt-1">{statusFilter === "all" ? "Hãy tải hóa đơn đầu tiên từ trang Tải hóa đơn" : "Thử chọn bộ lọc khác"}</p>
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {pagedReceipts.map((item) => (
            <ReceiptCard key={item.id} item={item} onView={onViewReceipt} onDelete={handleDelete} onApprove={handleApprove} onReject={handleReject} />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border bg-card">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/30 text-left text-sm text-muted-foreground">
                <th className="px-4 py-3 font-medium">Ngày</th>
                <th className="px-4 py-3 font-medium">Nhà cung cấp</th>
                <th className="px-4 py-3 font-medium">Danh mục</th>
                <th className="px-4 py-3 font-medium text-right">Số tiền</th>
                <th className="px-4 py-3 font-medium">Trạng thái</th>
                <th className="px-4 py-3 font-medium text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {pagedReceipts.map((item) => (
                <tr key={item.id} onClick={() => onViewReceipt(item.id)} className="cursor-pointer border-b last:border-0 hover:bg-muted/20">
                  <td className="px-4 py-3 text-sm">{item.receipt_date || new Date(item.created_at).toLocaleDateString("vi-VN")}</td>
                  <td className="px-4 py-3 text-sm font-medium">{item.supplier_name || "—"}</td>
                  <td className="px-4 py-3 text-sm">{item.category_name || "—"}</td>
                  <td className="px-4 py-3 text-sm text-right font-semibold text-indigo-600">{formatVND(item.total_amount)}</td>
                  <td className="px-4 py-3"><StatusBadge status={item.status} /></td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={(event) => { event.stopPropagation(); onViewReceipt(item.id) }} className="p-1.5 rounded hover:bg-indigo-50 text-muted-foreground hover:text-indigo-600" title="Xem">
                        <Eye className="h-4 w-4" />
                      </button>
                      {item.status === "Chờ duyệt" && (
                        <>
                          <button onClick={(event) => { event.stopPropagation(); handleApprove(item.id) }} className="p-1.5 rounded hover:bg-emerald-50 text-muted-foreground hover:text-emerald-600" title="Duyệt">
                            <CheckCircle2 className="h-4 w-4" />
                          </button>
                          <button onClick={(event) => { event.stopPropagation(); handleReject(item.id) }} className="p-1.5 rounded hover:bg-red-50 text-muted-foreground hover:text-red-600" title="Từ chối">
                            <XCircle className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      <button onClick={(event) => { event.stopPropagation(); handleDelete(item.id) }} className="p-1.5 rounded hover:bg-red-50 text-muted-foreground hover:text-red-600" title="Xóa">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-muted-foreground">
            Hiển thị {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filteredReceipts.length)} / {filteredReceipts.length} hóa đơn
          </p>
          <div className="flex items-center gap-1">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="p-2 rounded-lg border border-border disabled:opacity-30 hover:bg-muted">
              <ChevronLeft className="h-4 w-4" />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button key={p} onClick={() => setPage(p)} className={cn("h-8 w-8 rounded-lg text-sm", p === page ? "bg-primary text-primary-foreground" : "border border-border hover:bg-muted")}>
                {p}
              </button>
            ))}
            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-2 rounded-lg border border-border disabled:opacity-30 hover:bg-muted">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
