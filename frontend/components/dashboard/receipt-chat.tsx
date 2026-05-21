"use client"

import { useEffect, useMemo, useState } from "react"
import {
  Bot,
  FileSearch,
  Loader2,
  Send,
  UserRound,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiChat, ChatSource } from "@/lib/api"
import { cn } from "@/lib/utils"

interface ChatMessage {
  id: number
  role: "user" | "assistant"
  text: string
  route?: string
  confidence?: number
  sources?: ChatSource[]
}

interface ReceiptChatProps {
  onViewReceipt: (id: number) => void
}

const CHAT_HISTORY_LIMIT = 80
const formatVND = (amount: number) => amount.toLocaleString("vi-VN") + " đ"
const defaultMessages: ChatMessage[] = [
  {
    id: 1,
    role: "assistant",
    text: "Bạn có thể hỏi về tổng tiền, nhà cung cấp, phương thức thanh toán hoặc từng sản phẩm trong hóa đơn.",
    sources: [],
    route: "ready",
    confidence: 1,
  },
]

function getChatStorageKey() {
  if (typeof window === "undefined") return "smartreceipt-chat-history"
  try {
    const user = JSON.parse(localStorage.getItem("user") || "{}")
    return `smartreceipt-chat-history:${user.email || "guest"}`
  } catch {
    return "smartreceipt-chat-history:guest"
  }
}

function SourceList({ sources, onViewReceipt }: { sources: ChatSource[]; onViewReceipt: (id: number) => void }) {
  if (sources.length === 0) return null
  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-medium uppercase text-muted-foreground">
        <FileSearch className="h-3.5 w-3.5" />
        Nguồn tham chiếu
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {sources.map((source) => (
          <button
            key={`${source.receipt_id}-${source.score}`}
            onClick={() => onViewReceipt(source.receipt_id)}
            className="rounded-lg border border-border bg-background p-3 text-left transition-colors hover:bg-muted/50"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">
                  {source.supplier_name || `Hóa đơn #${source.receipt_id}`}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {source.receipt_date || "Không rõ ngày"} · {formatVND(source.total_amount)}
                </p>
              </div>
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                {Math.round(source.score * 100)}%
              </span>
            </div>
            <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
              {source.chunk_text}
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}

function MessageBubble({ message, onViewReceipt }: { message: ChatMessage; onViewReceipt: (id: number) => void }) {
  const isUser = message.role === "user"
  return (
    <div className={cn("flex gap-3", isUser && "justify-end")}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div className={cn("max-w-3xl rounded-xl px-4 py-3", isUser ? "bg-primary text-primary-foreground" : "bg-muted")}>
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</p>
        {!isUser && message.route && (
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span className="rounded-full bg-background px-2 py-0.5">luồng: {message.route}</span>
            <span className="rounded-full bg-background px-2 py-0.5">
              độ tin cậy: {Math.round((message.confidence || 0) * 100)}%
            </span>
          </div>
        )}
        {!isUser && message.sources && (
          <SourceList sources={message.sources} onViewReceipt={onViewReceipt} />
        )}
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sidebar text-sidebar-foreground">
          <UserRound className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}

export function ReceiptChat({ onViewReceipt }: ReceiptChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(defaultMessages)
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [historyLoaded, setHistoryLoaded] = useState(false)

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading])

  useEffect(() => {
    const saved = localStorage.getItem(getChatStorageKey())
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as ChatMessage[]
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed)
        }
      } catch {
        setMessages(defaultMessages)
      }
    }
    setHistoryLoaded(true)
  }, [])

  useEffect(() => {
    if (!historyLoaded) return
    const trimmed = messages.slice(-CHAT_HISTORY_LIMIT)
    localStorage.setItem(getChatStorageKey(), JSON.stringify(trimmed))
  }, [messages, historyLoaded])

  const handleSend = async () => {
    const text = input.trim()
    if (!text) return
    const userMessage: ChatMessage = { id: Date.now(), role: "user", text }
    setMessages((prev) => [...prev, userMessage].slice(-CHAT_HISTORY_LIMIT))
    setInput("")
    setLoading(true)
    setError("")
    try {
      const response = await apiChat(text)
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: response.answer,
        route: response.route,
        confidence: response.confidence,
        sources: response.sources,
      }
      setMessages((prev) => [...prev, assistantMessage].slice(-CHAT_HISTORY_LIMIT))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không gửi được câu hỏi")
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      if (canSend) handleSend()
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Trợ lý hóa đơn</h2>
          <p className="text-sm text-muted-foreground">Hỏi nhanh về tổng tiền, sản phẩm và hóa đơn đã lưu</p>
        </div>
      </div>

      <Card className="border-border bg-card shadow-sm">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Cuộc trò chuyện</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex min-h-[420px] flex-col gap-4 rounded-lg border border-border bg-background p-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} onViewReceipt={onViewReceipt} />
            ))}
            {loading && (
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang trả lời...
              </div>
            )}
          </div>

          {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}

          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ví dụ: Hóa đơn nào có rau muống?"
              className="min-h-12 flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <Button onClick={handleSend} disabled={!canSend} className="h-12 gap-2 px-4">
              <Send className="h-4 w-4" />
              Gửi
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
