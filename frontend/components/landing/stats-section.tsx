"use client"

import { CheckCircle, Zap, Globe, Gift } from "lucide-react"

const stats = [
  {
    icon: CheckCircle,
    value: "99%",
    label: "chính xác OCR",
  },
  {
    icon: Zap,
    value: "< 5 giây",
    label: "xử lý",
  },
  {
    icon: Globe,
    value: "Tiếng Việt",
    label: "hỗ trợ đầy đủ",
  },
  {
    icon: Gift,
    value: "Miễn phí",
    label: "sử dụng",
  },
]

export function StatsSection() {
  return (
    <section id="stats" className="py-16 bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div
              key={stat.label}
              className="text-center animate-in fade-in slide-in-from-bottom-4 duration-700"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="inline-flex items-center justify-center w-12 h-12 mb-4 bg-primary-foreground/10 rounded-xl">
                <stat.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-primary-foreground">
                {stat.value}
              </p>
              <p className="text-sm text-primary-foreground/80 mt-1">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
