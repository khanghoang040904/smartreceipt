"use client"

import { useState, useEffect } from "react"
import {
  ArrowLeft,
  Pencil,
  Save,
  Trash2,
  ZoomIn,
  ZoomOut,
  Receipt,
  Calendar,
  Tag,
  Building2,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  PlusCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { apiGetReceipt, apiUpdateReceipt, apiDeleteReceipt, apiGetCategories, getImageUrl } from "@/lib/api"

type Category = string
type Status = "Đã duyệt" | "Chờ duyệt" | "Từ chối"

interface LineItem {
  id: number
  item_name: string
  quantity: number
  unit_price: number
  amount: number
}

interface ReceiptData {
  id: number
  supplier_name: string | null
  receipt_date: string | null
  category_id: number | null
  category_name: string | null
  status: string
  total_amount: number
  created_at: string
  image_path: string
  raw_text: string | null
  items: LineItem[]
}

interface CategoryOption {
  id: number
  name: string
}

const moneyFormatter = new Intl.NumberFormat("vi-VN")
const formatVND = (n: number) => `${moneyFormatter.format(Math.round(n || 0))} đ`
const formatNumber = (n: number) => moneyFormatter.format(Math.round(n || 0))
const parseMoney = (value: string) => Number(value.replace(/[^\d]/g, "")) || 0

const statusStyles: Record<string, string> = {
  "Đã duyệt": "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  "Chờ duyệt": "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  "Từ chối": "bg-red-50 text-red-600 ring-1 ring-red-200",
}

function SectionCard({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-xl border border-border bg-card shadow-sm overflow-hidden", className)}>
      <div className="border-b border-border px-5 py-3.5">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}

function Field({ label, icon: Icon, children }: { label: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </label>
      {children}
    </div>
  )
}

function DeleteModal({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative z-10 w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-xl">
        <div className="flex flex-col items-center text-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-foreground">Xác nhận xóa hóa đơn</h3>
            <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">
              Hành động này không thể hoàn tác. Hóa đơn và toàn bộ dữ liệu liên quan sẽ bị xóa vĩnh viễn.
            </p>
          </div>
          <div className="flex w-full gap-3 pt-1">
            <button onClick={onCancel} className="flex-1 rounded-lg border border-border bg-background py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors">
              Hủy
            </button>
            <button onClick={onConfirm} className="flex-1 rounded-lg bg-red-600 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors">
              Xóa
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function ReceiptDetail({ receiptId, onBack }: { receiptId: number | null; onBack: () => void }) {
  const [receipt, setReceipt] = useState<ReceiptData | null>(null)
  const [categories, setCategories] = useState<CategoryOption[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const [zoom, setZoom] = useState(1)

  const [supplier, setSupplier] = useState("")
  const [date, setDate] = useState("")
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [status, setStatus] = useState<string>("Chờ duyệt")
  const [total, setTotal] = useState(0)
  const [editItems, setEditItems] = useState<LineItem[]>([])

  useEffect(() => {
    if (!receiptId) return
    const id = receiptId
    async function fetchData() {
      setLoading(true)
      try {
        const [receiptData, cats] = await Promise.all([
          apiGetReceipt(id),
          apiGetCategories(),
        ])
        setReceipt(receiptData)
        setCategories(cats)
        setSupplier(receiptData.supplier_name || "")
        setDate(receiptData.receipt_date || "")
        setCategoryId(receiptData.category_id)
        setStatus(receiptData.status)
        setTotal(receiptData.total_amount)
        setEditItems(receiptData.items || [])
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [receiptId])

  const handleSave = async () => {
    if (!receiptId) return
    setSaving(true)
    try {
      const updated = await apiUpdateReceipt(receiptId, {
        supplier_name: supplier,
        receipt_date: date,
        category_id: categoryId,
        status: status,
        total_amount: total,
        items: editItems.map((item) => ({
          item_name: item.item_name,
          quantity: item.quantity,
          unit_price: item.unit_price,
          amount: item.amount,
        })),
      })
      setReceipt(updated)
      setEditItems(updated.items || [])
      setEditing(false)
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    if (receipt) {
      setSupplier(receipt.supplier_name || "")
      setDate(receipt.receipt_date || "")
      setCategoryId(receipt.category_id)
      setStatus(receipt.status)
      setTotal(receipt.total_amount)
      setEditItems(receipt.items || [])
    }
    setEditing(false)
  }

  const updateItem = (id: number, field: keyof LineItem, value: string | number) => {
    setEditItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item
        const updated = { ...item, [field]: value }
        if (field === "quantity" || field === "unit_price") {
          updated.amount = Number(updated.quantity || 0) * Number(updated.unit_price || 0)
        }
        return updated
      })
    )
  }

  const addItem = () => {
    const nextId = editItems.length > 0 ? Math.min(...editItems.map((item) => item.id), 0) - 1 : -1
    setEditItems([
      ...editItems,
      { id: nextId, item_name: "", quantity: 1, unit_price: 0, amount: 0 },
    ])
  }

  const removeItem = (id: number) => {
    setEditItems((prev) => prev.filter((item) => item.id !== id))
  }

  const handleDelete = async () => {
    if (!receiptId) return
    try {
      await apiDeleteReceipt(receiptId)
      onBack()
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!receipt) {
    return (
      <div className="text-center py-24 text-muted-foreground">
        <p>Không tìm thấy hóa đơn</p>
        <button onClick={onBack} className="mt-4 text-primary hover:underline">Quay lại</button>
      </div>
    )
  }

  const displayedItems = editing ? editItems : receipt.items
  const itemsTotal = displayedItems.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  const displayedTotal = editing ? total : receipt.total_amount
  const totalDiff = Math.abs(Number(displayedTotal || 0) - itemsTotal)
  const hasItems = displayedItems.length > 0
  const totalsMatch = hasItems && totalDiff < 1

  return (
    <div className="space-y-6">
      {showDelete && <DeleteModal onConfirm={handleDelete} onCancel={() => setShowDelete(false)} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Quay lại
          </button>
          <h2 className="text-lg font-semibold">Hóa đơn #{receipt.id}</h2>
          <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusStyles[receipt.status] || "bg-gray-50 text-gray-700")}>
            {receipt.status}
          </span>
        </div>
        <div className="flex gap-2">
          {editing ? (
            <>
              <button onClick={handleCancelEdit} className="px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted">Hủy</button>
              <button onClick={handleSave} disabled={saving} className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center gap-1.5">
                {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                Lưu
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)} className="px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted flex items-center gap-1.5">
                <Pencil className="h-3.5 w-3.5" />
                Chỉnh sửa
              </button>
              <button onClick={() => setShowDelete(true)} className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 text-sm hover:bg-red-50 flex items-center gap-1.5">
                <Trash2 className="h-3.5 w-3.5" />
                Xóa
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Image */}
        <SectionCard title="Ảnh hóa đơn">
          <div className="flex justify-end gap-1 mb-2">
            <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))} className="p-1.5 rounded hover:bg-muted"><ZoomOut className="h-4 w-4" /></button>
            <button onClick={() => setZoom((z) => Math.min(3, z + 0.25))} className="p-1.5 rounded hover:bg-muted"><ZoomIn className="h-4 w-4" /></button>
          </div>
          <div className="overflow-auto rounded-lg bg-muted/30 p-4" style={{ maxHeight: 500 }}>
            <img
              src={getImageUrl(receipt.image_path)}
              alt="Ảnh hóa đơn"
              style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}
              className="max-w-full transition-transform"
            />
          </div>
        </SectionCard>

        {/* Info */}
        <div className="space-y-4">
          <SectionCard title="Thông tin hóa đơn">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Nhà cung cấp" icon={Building2}>
                {editing ? (
                  <input type="text" value={supplier} onChange={(e) => setSupplier(e.target.value)} className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm" />
                ) : (
                  <p className="text-sm font-medium">{receipt.supplier_name || "—"}</p>
                )}
              </Field>
              <Field label="Ngày" icon={Calendar}>
                {editing ? (
                  <input type="text" value={date} onChange={(e) => setDate(e.target.value)} className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm" />
                ) : (
                  <p className="text-sm font-medium">{receipt.receipt_date || "—"}</p>
                )}
              </Field>
              <Field label="Danh mục" icon={Tag}>
                {editing ? (
                  <select value={categoryId ?? ""} onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : null)} className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm">
                    <option value="">-- Chọn danh mục --</option>
                    {categories.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
                  </select>
                ) : (
                  <p className="text-sm font-medium">{receipt.category_name || "—"}</p>
                )}
              </Field>
              <Field label="Trạng thái" icon={Receipt}>
                {editing ? (
                  <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm">
                    <option value="Chờ duyệt">Chờ duyệt</option>
                    <option value="Đã duyệt">Đã duyệt</option>
                    <option value="Từ chối">Từ chối</option>
                  </select>
                ) : (
                  <span className={cn("inline-flex w-fit items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusStyles[receipt.status] || "bg-gray-50 text-gray-700")}>
                    {receipt.status}
                  </span>
                )}
              </Field>
            </div>
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Tổng tiền</p>
              {editing ? (
                <div className="relative">
                  <input type="text" inputMode="numeric" value={formatNumber(total)} onChange={(e) => setTotal(parseMoney(e.target.value))} className="w-full rounded-lg border border-input bg-background px-3 py-2 pr-10 text-lg font-bold text-indigo-600" />
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">đ</span>
                </div>
              ) : (
                <p className="text-2xl font-bold text-indigo-600">{formatVND(receipt.total_amount)}</p>
              )}
            </div>
          </SectionCard>

          {/* Items */}
          <SectionCard
            title="Danh sách sản phẩm"
            className={editing ? "lg:col-span-1" : undefined}
          >
            {editing && (
              <div className="mb-3 flex justify-end">
                <button onClick={addItem} className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-muted">
                  <PlusCircle className="h-4 w-4" />
                  Thêm sản phẩm
                </button>
              </div>
            )}
            {hasItems && (
              <div className={cn(
                "mb-3 flex items-start gap-2 rounded-lg px-3 py-2 text-sm",
                totalsMatch ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
              )}>
                {totalsMatch ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />}
                <div>
                  <p className="font-medium">{totalsMatch ? "Tổng sản phẩm khớp với tổng hóa đơn" : "Tổng sản phẩm chưa khớp tổng hóa đơn"}</p>
                  <p className="text-xs">
                    Hóa đơn: {formatVND(displayedTotal)} · Sản phẩm: {formatVND(itemsTotal)}
                    {!totalsMatch ? ` · Lệch: ${formatVND(totalDiff)}` : ""}
                  </p>
                </div>
              </div>
            )}
            {displayedItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">Không có sản phẩm nào</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="pb-2 font-medium">Sản phẩm</th>
                      <th className="pb-2 font-medium text-center">SL</th>
                      <th className="pb-2 font-medium text-right">Đơn giá</th>
                      <th className="pb-2 font-medium text-right">Thành tiền</th>
                      {editing && <th className="pb-2 font-medium text-right">Xóa</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {displayedItems.map((item) => (
                      <tr key={item.id} className="border-b last:border-0">
                        <td className="py-2">
                          {editing ? (
                            <input type="text" value={item.item_name} onChange={(e) => updateItem(item.id, "item_name", e.target.value)} className="w-full min-w-44 rounded border border-input bg-background px-2 py-1" />
                          ) : (
                            item.item_name
                          )}
                        </td>
                        <td className="py-2 text-center">
                          {editing ? (
                            <input type="number" min={1} value={item.quantity} onChange={(e) => updateItem(item.id, "quantity", Number(e.target.value))} className="w-16 rounded border border-input bg-background px-2 py-1 text-center" />
                          ) : (
                            item.quantity
                          )}
                        </td>
                        <td className="py-2 text-right">
                          {editing ? (
                            <input type="text" inputMode="numeric" value={formatNumber(item.unit_price)} onChange={(e) => updateItem(item.id, "unit_price", parseMoney(e.target.value))} className="w-28 rounded border border-input bg-background px-2 py-1 text-right" />
                          ) : (
                            formatVND(item.unit_price)
                          )}
                        </td>
                        <td className="py-2 text-right font-medium">{formatVND(item.amount)}</td>
                        {editing && (
                          <td className="py-2 text-right">
                            <button onClick={() => removeItem(item.id)} className="rounded p-1.5 text-red-500 hover:bg-red-50">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>

          {/* Raw OCR */}
          {receipt.raw_text && (
            <SectionCard title="Văn bản OCR gốc">
              <pre className="whitespace-pre-wrap rounded-lg bg-muted/50 p-4 text-xs font-mono max-h-60 overflow-auto">{receipt.raw_text}</pre>
            </SectionCard>
          )}
        </div>
      </div>
    </div>
  )
}
