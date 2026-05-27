"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function CTASection() {
  return (
    <section className="py-20 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/5" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground text-balance">
            Sẵn sàng quản lý hóa đơn thông minh?
          </h2>
          <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
            Bắt đầu ngay hôm nay và trải nghiệm sức mạnh của AI trong việc quản lý chi tiêu
          </p>
          <div className="mt-10">
            <Button size="lg" className="text-lg px-10 py-6 gap-2" asChild>
              <Link href="/register">
                Đăng ký ngay
                <ArrowRight className="w-5 h-5" />
              </Link>
            </Button>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Hoàn toàn miễn phí • Không cần thẻ tín dụng
          </p>
        </div>
      </div>
    </section>
  )
}
