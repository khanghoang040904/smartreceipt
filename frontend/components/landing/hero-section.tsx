"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Play, TrendingUp, PieChart, BarChart3, DollarSign, ShoppingCart, Utensils, Car } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-1/4 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%236366f1' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left content */}
          <div className="text-center lg:text-left animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight text-balance">
              Quản lý hóa đơn{" "}
              <span className="text-primary">thông minh</span> với AI
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-xl mx-auto lg:mx-0 text-pretty">
              Tải ảnh hóa đơn lên, AI tự động trích xuất thông tin, phân loại và phân tích chi tiêu cho bạn
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Button size="lg" className="text-base px-8" asChild>
                <Link href="/register">Bắt đầu miễn phí</Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base px-8 gap-2">
                <Play className="w-4 h-4" />
                Xem demo
              </Button>
            </div>
          </div>

          {/* Right content - Dashboard mockup */}
          <div className="relative animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
            <div className="bg-card rounded-2xl border border-border shadow-xl p-6 space-y-6">
              {/* Stats cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-secondary/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-primary mb-2">
                    <TrendingUp className="w-4 h-4" />
                    <span className="text-xs font-medium">Tổng chi</span>
                  </div>
                  <p className="text-xl font-bold text-foreground">12.5M</p>
                  <p className="text-xs text-muted-foreground">VNĐ</p>
                </div>
                <div className="bg-secondary/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-primary mb-2">
                    <DollarSign className="w-4 h-4" />
                    <span className="text-xs font-medium">Hóa đơn</span>
                  </div>
                  <p className="text-xl font-bold text-foreground">48</p>
                  <p className="text-xs text-muted-foreground">tháng này</p>
                </div>
                <div className="bg-secondary/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-primary mb-2">
                    <BarChart3 className="w-4 h-4" />
                    <span className="text-xs font-medium">Trung bình</span>
                  </div>
                  <p className="text-xl font-bold text-foreground">260K</p>
                  <p className="text-xs text-muted-foreground">/hóa đơn</p>
                </div>
              </div>

              {/* Charts row */}
              <div className="grid grid-cols-2 gap-4">
                {/* Pie chart mockup */}
                <div className="bg-secondary/50 rounded-xl p-4">
                  <p className="text-sm font-medium text-foreground mb-3">Theo danh mục</p>
                  <div className="flex items-center justify-center">
                    <div className="relative w-24 h-24">
                      <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                        <circle
                          cx="18"
                          cy="18"
                          r="15.915"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          className="text-primary/20"
                        />
                        <circle
                          cx="18"
                          cy="18"
                          r="15.915"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray="40 60"
                          className="text-primary"
                        />
                        <circle
                          cx="18"
                          cy="18"
                          r="15.915"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray="25 75"
                          strokeDashoffset="-40"
                          className="text-chart-2"
                        />
                        <circle
                          cx="18"
                          cy="18"
                          r="15.915"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray="20 80"
                          strokeDashoffset="-65"
                          className="text-chart-4"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <PieChart className="w-6 h-6 text-primary" />
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <Utensils className="w-3 h-3 text-primary" />
                      <span className="text-muted-foreground">Ăn uống 40%</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <ShoppingCart className="w-3 h-3 text-chart-2" />
                      <span className="text-muted-foreground">Mua sắm 25%</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Car className="w-3 h-3 text-chart-4" />
                      <span className="text-muted-foreground">Di chuyển 20%</span>
                    </div>
                  </div>
                </div>

                {/* Bar chart mockup */}
                <div className="bg-secondary/50 rounded-xl p-4">
                  <p className="text-sm font-medium text-foreground mb-3">Chi tiêu theo tháng</p>
                  <div className="flex items-end justify-between gap-2 h-24">
                    {[65, 45, 80, 55, 90, 70].map((height, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <div
                          className="w-full bg-primary/80 rounded-t transition-all hover:bg-primary"
                          style={{ height: `${height}%` }}
                        />
                        <span className="text-[10px] text-muted-foreground">T{i + 1}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Floating elements */}
            <div className="absolute -top-4 -right-4 bg-card rounded-xl border border-border shadow-lg p-3 animate-in fade-in slide-in-from-right-4 duration-700 delay-500">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Tiết kiệm</p>
                  <p className="text-sm font-bold text-green-600">+15%</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
