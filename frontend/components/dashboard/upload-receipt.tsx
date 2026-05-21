"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import {
  CloudUpload,
  FileImage,
  X,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Save,
  Upload,
  PlusCircle,
  Trash2,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { apiUploadReceipt, apiUpdateReceipt, apiGetCategories, apiCreateCategory, getImageUrl } from "@/lib/api"

type AppState = "upload" | "processing" | "results"

interface LineItem {
  id: number
  name: string
  qty: number
  unitPrice: number
  amount: number
}

interface CategoryOption {
  id: number
  name: string
}

const moneyFormatter = new Intl.NumberFormat("vi-VN")
const fmt = (n: number) => `${moneyFormatter.format(Math.round(n || 0))} đ`
const formatNumber = (n: number) => moneyFormatter.format(Math.round(n || 0))
const parseMoney = (value: string) => Number(value.replace(/[^\d]/g, "")) || 0
const normalizeText = (value: string) =>
  value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim()

function UploadZone({ onFile }: { onFile: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files?.[0]
      if (file) onFile(file)
    },
    [onFile]
  )

  return (
    <div className="flex flex-col items-center justify-center gap-6 py-8">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative flex w-full max-w-xl cursor-pointer flex-col items-center justify-center gap-5 rounded-2xl border-2 border-dashed px-8 py-16 transition-all duration-200",
          dragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border bg-muted/30 hover:border-primary/60 hover:bg-primary/5"
        )}
      >
        {["top-3 left-3", "top-3 right-3", "bottom-3 left-3", "bottom-3 right-3"].map((pos) => (
          <span key={pos} className={`absolute ${pos} h-1.5 w-1.5 rounded-full bg-primary/30`} />
        ))}
        <div className={cn("flex h-20 w-20 items-center justify-center rounded-2xl transition-colors duration-200", dragging ? "bg-primary/20" : "bg-primary/10")}>
          <CloudUpload className={cn("h-10 w-10 transition-colors duration-200", dragging ? "text-primary" : "text-primary/70")} />
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-foreground">{dragging ? "Thả ảnh vào đây" : "Kéo & thả ảnh hóa đơn vào đây"}</p>
          <p className="mt-1 text-sm text-muted-foreground">hoặc <span className="font-medium text-primary">nhấn để chọn file</span></p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-border bg-background px-4 py-1.5">
          <FileImage className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Hỗ trợ JPG, PNG — tối đa 10MB</span>
        </div>
        <input ref={inputRef} type="file" accept="image/jpeg,image/png" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f) }} />
      </div>
      <Button onClick={() => inputRef.current?.click()} className="gap-2 bg-primary px-8 text-primary-foreground hover:bg-primary/90">
        <Upload className="h-4 w-4" />
        Chọn ảnh hóa đơn
      </Button>
    </div>
  )
}

function ProcessingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-24">
      <div className="relative flex h-24 w-24 items-center justify-center">
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
        <Loader2 className="h-8 w-8 animate-pulse text-primary" />
      </div>
      <div className="text-center">
        <p className="text-lg font-semibold text-foreground">Đang xử lý OCR...</p>
        <p className="mt-1 text-sm text-muted-foreground">Trích xuất thông tin từ ảnh hóa đơn</p>
      </div>
    </div>
  )
}

export function UploadReceipt() {
  const [state, setState] = useState<AppState>("upload")
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [ocrText, setOcrText] = useState("")
  const [showRawText, setShowRawText] = useState(false)
  const [items, setItems] = useState<LineItem[]>([])
  const [supplier, setSupplier] = useState("")
  const [date, setDate] = useState("")
  const [total, setTotal] = useState(0)
  const [receiptId, setReceiptId] = useState<number | null>(null)
  const [imagePath, setImagePath] = useState("")
  const [categories, setCategories] = useState<CategoryOption[]>([])
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState("")

  const itemsTotal = items.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  const totalDiff = Math.abs(Number(total || 0) - itemsTotal)
  const hasItems = items.length > 0
  const totalsMatch = hasItems && totalDiff < 1

  useEffect(() => {
    let active = true
    async function loadCategories() {
      try {
        const current = await apiGetCategories()
        let next = current
        if (!current.some((category: CategoryOption) => normalizeText(category.name) === "khac")) {
          const other = await apiCreateCategory("Khác")
          next = [...current, other]
        }
        if (active) setCategories(next)
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Không tải được danh mục")
      }
    }
    loadCategories()
    return () => {
      active = false
    }
  }, [])

  const handleFile = async (file: File) => {
    setPreviewUrl(URL.createObjectURL(file))
    setState("processing")
    setError("")

    try {
      const result = await apiUploadReceipt(file)
      setOcrText(result.raw_text || "")
      setSupplier(result.supplier_name || "")
      setDate(result.receipt_date || "")
      setTotal(result.total_amount || 0)
      setReceiptId(result.id)
      setImagePath(result.image_path)
      setCategoryId(null)
      setItems(
        (result.items || []).map((item: { item_name: string; quantity: number; unit_price: number; amount: number }, i: number) => ({
          id: i + 1,
          name: item.item_name,
          qty: item.quantity,
          unitPrice: item.unit_price,
          amount: item.amount,
        }))
      )
      setState("results")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Không tải được hóa đơn")
      setState("upload")
    }
  }

  const handleSave = async () => {
    if (!receiptId) return
    if (!categoryId) {
      setError("Vui lòng chọn danh mục trước khi lưu hóa đơn")
      return
    }
    setSaving(true)
    setError("")
    try {
      await apiUpdateReceipt(receiptId, {
        supplier_name: supplier,
        receipt_date: date,
        total_amount: total,
        category_id: categoryId,
        status: "Đã duyệt",
        items: items.map((item) => ({
          item_name: item.name,
          quantity: item.qty,
          unit_price: item.unitPrice,
          amount: item.amount,
        })),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Không lưu được hóa đơn")
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setState("upload")
    setPreviewUrl(null)
    setOcrText("")
    setItems([])
    setSupplier("")
    setDate("")
    setTotal(0)
    setReceiptId(null)
    setImagePath("")
    setCategoryId(null)
    setZoom(1)
    setError("")
    setSaved(false)
  }

  const updateItem = (id: number, field: keyof LineItem, value: string | number) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item
        const updated = { ...item, [field]: value }
        if (field === "qty" || field === "unitPrice") {
          updated.amount = updated.qty * updated.unitPrice
        }
        return updated
      })
    )
  }

  const addItem = () => {
    const newId = items.length > 0 ? Math.max(...items.map((i) => i.id)) + 1 : 1
    setItems([...items, { id: newId, name: "", qty: 1, unitPrice: 0, amount: 0 }])
  }

  const removeItem = (id: number) => {
    setItems(items.filter((i) => i.id !== id))
  }

  if (state === "upload") {
    return (
      <Card className="border-border bg-card shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Tải hóa đơn</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-600 text-sm">{error}</div>}
          <UploadZone onFile={handleFile} />
        </CardContent>
      </Card>
    )
  }

  if (state === "processing") {
    return (
      <Card className="border-border bg-card shadow-sm">
        <CardContent>
          <ProcessingSpinner />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Kết quả OCR</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset} className="gap-2">
            <RotateCcw className="h-4 w-4" />
            Tải ảnh mới
          </Button>
          <Button onClick={handleSave} disabled={saving || saved} className="gap-2">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : saved ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />}
            {saving ? "Đang lưu..." : saved ? "Đã lưu!" : "Lưu hóa đơn"}
          </Button>
        </div>
      </div>
      {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Image preview */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Ảnh hóa đơn</CardTitle>
            <div className="flex gap-1">
              <Button variant="ghost" size="icon" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={() => setZoom((z) => Math.min(3, z + 0.25))}>
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto rounded-lg bg-muted/30 p-4" style={{ maxHeight: 500 }}>
              {previewUrl ? (
                <img src={previewUrl} alt="Ảnh hóa đơn" style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }} className="max-w-full transition-transform" />
              ) : imagePath ? (
                <img src={getImageUrl(imagePath)} alt="Ảnh hóa đơn" style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }} className="max-w-full transition-transform" />
              ) : null}
            </div>
          </CardContent>
        </Card>

        {/* OCR results */}
        <div className="space-y-4">
          <Card className="border-border bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Thông tin trích xuất</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase">Nhà cung cấp</label>
                <input type="text" value={supplier} onChange={(e) => setSupplier(e.target.value)} className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase">Danh mục</label>
                <select value={categoryId ?? ""} onChange={(e) => { setError(""); setCategoryId(e.target.value ? Number(e.target.value) : null) }} className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm">
                  <option value="">-- Chọn danh mục --</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground uppercase">Ngày</label>
                  <input type="text" value={date} onChange={(e) => setDate(e.target.value)} className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground uppercase">Tổng tiền</label>
                  <div className="relative mt-1">
                    <input type="text" inputMode="numeric" value={formatNumber(total)} onChange={(e) => setTotal(parseMoney(e.target.value))} className="w-full rounded-lg border border-input bg-background px-3 py-2 pr-9 text-sm" />
                    <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">đ</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Items table */}
          <Card className="border-border bg-card shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium">Danh sách sản phẩm</CardTitle>
              <Button variant="outline" size="sm" onClick={addItem} className="gap-1">
                <PlusCircle className="h-3.5 w-3.5" />
                Thêm
              </Button>
            </CardHeader>
            <CardContent>
              {hasItems && (
                <div className={cn(
                  "mb-3 flex items-start gap-2 rounded-lg px-3 py-2 text-sm",
                  totalsMatch ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                )}>
                  {totalsMatch ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />}
                  <div>
                    <p className="font-medium">{totalsMatch ? "Tổng sản phẩm khớp với tổng hóa đơn" : "Tổng sản phẩm chưa khớp tổng hóa đơn"}</p>
                    <p className="text-xs">
                      Hóa đơn: {fmt(total)} · Sản phẩm: {fmt(itemsTotal)}
                      {!totalsMatch ? ` · Lệch: ${fmt(totalDiff)}` : ""}
                    </p>
                  </div>
                </div>
              )}
              <div className="space-y-2">
                {items.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-border px-3 py-4 text-center text-sm text-muted-foreground">
                    Chưa trích xuất được sản phẩm. Bạn có thể thêm thủ công.
                  </p>
                ) : (
                  items.map((item) => (
                    <div key={item.id} className="flex items-center gap-2 rounded-lg border border-border bg-muted/20 p-2">
                      <input type="text" value={item.name} onChange={(e) => updateItem(item.id, "name", e.target.value)} placeholder="Tên sản phẩm" className="flex-1 rounded border-0 bg-transparent px-2 py-1 text-sm" />
                      <input type="number" value={item.qty} onChange={(e) => updateItem(item.id, "qty", Number(e.target.value))} className="w-14 rounded border border-input bg-background px-2 py-1 text-center text-sm" />
                      <input type="text" inputMode="numeric" value={formatNumber(item.unitPrice)} onChange={(e) => updateItem(item.id, "unitPrice", parseMoney(e.target.value))} className="w-24 rounded border border-input bg-background px-2 py-1 text-right text-sm" />
                      <span className="w-28 text-right text-sm font-medium">{fmt(item.amount)}</span>
                      <Button variant="ghost" size="icon" onClick={() => removeItem(item.id)} className="h-7 w-7 text-red-400 hover:text-red-600">
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Raw OCR text */}
          <Card className="border-border bg-card shadow-sm">
            <CardHeader>
              <button onClick={() => setShowRawText(!showRawText)} className="flex w-full items-center justify-between text-sm font-medium">
                Văn bản OCR gốc
                {showRawText ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </CardHeader>
            {showRawText && (
              <CardContent>
                <pre className="whitespace-pre-wrap rounded-lg bg-muted/50 p-4 text-xs font-mono">{ocrText}</pre>
              </CardContent>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
